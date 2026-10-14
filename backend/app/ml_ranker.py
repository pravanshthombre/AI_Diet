"""
Feature-based meal ranker with scikit-learn GradientBoosting training.

Blends explicit feedback, calorie fit, regional preference, and budget fit.
Falls back to weighted rules when no trained model is loaded.

Production: Implements actual model training via GradientBoostingRegressor
instead of stubbed LightGBM imports.
"""
import logging
import os
import pickle
from typing import List, Dict, Any, Optional

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sqlalchemy.orm import Session

logger = logging.getLogger("nutricalc.ml_ranker")

NUTRIENT_FIELDS = [
    "calories_per_serving",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml_model.pkl")


class MLRanker:
    def __init__(self, model_path: str = None):
        self.model: Optional[GradientBoostingRegressor] = None
        self.is_trained = False
        path = model_path or MODEL_PATH
        if os.path.exists(path):
            self.load_model(path)

    def load_model(self, path: str):
        """Load a pre-trained scikit-learn model from disk."""
        try:
            with open(path, "rb") as f:
                self.model = pickle.load(f)
            self.is_trained = True
            logger.info("Loaded ML ranker model from %s", path)
        except Exception as e:
            logger.warning("Failed to load ML model from %s: %s", path, e)
            self.model = None
            self.is_trained = False

    def save_model(self, path: str = None):
        """Save the trained model to disk. Gracefully handles read-only/ephemeral filesystems."""
        path = path or MODEL_PATH
        if self.model is not None:
            try:
                with open(path, "wb") as f:
                    pickle.dump(self.model, f)
                logger.info("Saved ML ranker model to %s", path)
            except OSError as e:
                logger.warning(
                    "Could not persist ML model to %s (ephemeral filesystem?): %s. "
                    "Model is active in-memory and will retrain on next cold start.",
                    path, e,
                )

    def extract_features(
        self,
        user: Any,
        candidate_food: Any,
        target_calories: float,
        feedback_rating: Optional[float] = None,
        per_meal_budget: Optional[float] = None,
    ) -> List[float]:
        calorie_fit = 1.0 / (
            1.0 + abs(candidate_food.calories_per_serving - target_calories)
            / max(target_calories, 1)
        )
        region_match = 1.0 if getattr(user, "region", None) == getattr(candidate_food, "region", None) else 0.0
        state_match = (
            1.0
            if getattr(user, "state", None)
            and getattr(user, "state", None) == getattr(candidate_food, "state", None)
            else 0.0
        )
        budget_fit = 1.0
        if per_meal_budget and per_meal_budget > 0:
            budget_fit = min(1.0, per_meal_budget / max(candidate_food.price_inr_per_serving, 1))
            if candidate_food.price_inr_per_serving > per_meal_budget:
                budget_fit = max(0.0, 1.0 - (candidate_food.price_inr_per_serving - per_meal_budget) / per_meal_budget)

        protein_norm = min(candidate_food.protein_g / 30.0, 1.0)
        rating_norm = (feedback_rating / 5.0) if feedback_rating else 0.0

        return [
            calorie_fit,
            region_match,
            state_match,
            budget_fit,
            protein_norm,
            rating_norm,
        ]

    def rule_score(
        self,
        user: Any,
        food: Any,
        target_calories: float,
        feedback_rating: Optional[float] = None,
        per_meal_budget: Optional[float] = None,
    ) -> float:
        features = self.extract_features(
            user, food, target_calories, feedback_rating, per_meal_budget
        )
        weights = [0.35, 0.15, 0.10, 0.15, 0.10, 0.15]
        return sum(f * w for f, w in zip(features, weights))

    def predict_score(
        self,
        user: Any,
        candidates: List[Any],
        db: Session,
        target_calories: float,
        user_id: int,
        per_meal_budget: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        from .models import Feedback

        # Batch-load all feedback ratings for this user (avoids N+1)
        ratings = {
            fb.food_id: fb.rating
            for fb in db.query(Feedback)
            .filter(Feedback.user_id == user_id, Feedback.rating.isnot(None))
            .all()
        }

        results = []
        for food in candidates:
            rating = ratings.get(food.id)
            if self.is_trained and self.model is not None:
                features = self.extract_features(
                    user, food, target_calories, rating, per_meal_budget
                )
                try:
                    score = float(self.model.predict([features])[0])
                    reason = "ML model ranking"
                except Exception:
                    score = self.rule_score(
                        user, food, target_calories, rating, per_meal_budget
                    )
                    reason = "Feature-based ranking (ML fallback)"
            else:
                score = self.rule_score(
                    user, food, target_calories, rating, per_meal_budget
                )
                reason = "Feature-based ranking"

            results.append({"food": food, "ml_score": score, "reason": reason})

        results.sort(key=lambda x: x["ml_score"], reverse=True)
        return results

    def collect_training_data(self, db: Session):
        """
        Build (X, y) from feedback ratings and implicit meal-log adherence.

        FIXED: Uses batch queries instead of N+1 individual lookups.
        """
        from .models import Feedback, MealLog, User, Food

        rows_x = []
        rows_y = []

        # Batch-load all data upfront
        feedback_rows = db.query(Feedback).all()
        all_user_ids = {fb.user_id for fb in feedback_rows}
        all_food_ids = {fb.food_id for fb in feedback_rows}

        logged = db.query(MealLog).all()
        all_user_ids.update(ml.user_id for ml in logged)
        all_food_ids.update(ml.food_id for ml in logged)

        # Batch load users and foods
        users_map = {u.id: u for u in db.query(User).filter(User.id.in_(all_user_ids)).all()} if all_user_ids else {}
        foods_map = {f.id: f for f in db.query(Food).filter(Food.id.in_(all_food_ids)).all()} if all_food_ids else {}

        for fb in feedback_rows:
            user = users_map.get(fb.user_id)
            food = foods_map.get(fb.food_id)
            if not user or not food:
                continue

            if fb.rating is not None:
                label = fb.rating / 5.0
            elif fb.liked is True:
                label = 1.0
            elif fb.liked is False:
                label = 0.0
            else:
                continue

            rows_x.append(
                self.extract_features(user, food, target_calories=500.0)
            )
            rows_y.append(label)

        for log in logged:
            user = users_map.get(log.user_id)
            food = foods_map.get(log.food_id)
            if not user or not food:
                continue
            rows_x.append(
                self.extract_features(user, food, target_calories=500.0)
            )
            rows_y.append(0.75)

        logger.info("Collected %d training samples (%d from feedback, %d from logs)",
                     len(rows_x), len(feedback_rows), len(logged))

        # If not enough real user interactions, enrich with baseline persona data
        if len(rows_x) < 10:
            logger.info("Real user interactions (%d) < 10. Generating baseline persona training data...", len(rows_x))
            base_x, base_y = self.generate_baseline_training_data(db)
            rows_x.extend(base_x)
            rows_y.extend(base_y)

        return rows_x, rows_y

    def generate_baseline_training_data(self, db: Session):
        """
        Generate synthetic baseline training data using real foods from the database
        and diverse regional archetypes (per PRD Section 2 & 5.4).
        Ensures the ML model is trained and active immediately on startup.
        """
        from .models import Food
        from types import SimpleNamespace

        foods = db.query(Food).limit(100).all()
        if not foods:
            return [], []

        personas = [
            SimpleNamespace(region="north", state="Punjab", diet_type="vegetarian", weekly_budget_inr=2000),
            SimpleNamespace(region="south", state="Tamil Nadu", diet_type="vegetarian", weekly_budget_inr=1800),
            SimpleNamespace(region="west", state="Maharashtra", diet_type="vegetarian", weekly_budget_inr=1500),
            SimpleNamespace(region="east", state="West Bengal", diet_type="non_vegetarian", weekly_budget_inr=2500),
            SimpleNamespace(region="pan_india", state="", diet_type="vegan", weekly_budget_inr=2200),
        ]

        rows_x = []
        rows_y = []
        weights = [0.35, 0.15, 0.10, 0.15, 0.10, 0.15]

        for persona in personas:
            target_cal = 450.0
            budget_per_meal = (persona.weekly_budget_inr / 21) * 1.5
            for food in foods[:20]:
                features = self.extract_features(
                    user=persona,
                    candidate_food=food,
                    target_calories=target_cal,
                    feedback_rating=4.0 if food.region == persona.region else None,
                    per_meal_budget=budget_per_meal,
                )
                score = sum(f * w for f, w in zip(features, weights))
                score += 0.05 * np.sin(features[0] * np.pi)
                score = float(np.clip(score, 0.05, 1.0))

                rows_x.append(features)
                rows_y.append(score)

        return rows_x, rows_y

    def train_model(self, db: Session, save_path: str = None) -> bool:
        """
        Train the GradientBoosting ranker when enough labeled data exists.

        Returns True if model was trained successfully, False otherwise.
        """
        X, y = self.collect_training_data(db)

        if len(X) < 10:
            logger.info("Not enough training data (%d samples, need ≥10). Skipping training.", len(X))
            self.is_trained = False
            return False

        X_arr = np.array(X)
        y_arr = np.array(y)

        logger.info("Training GradientBoosting ranker on %d samples...", len(X))

        self.model = GradientBoostingRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        )
        self.model.fit(X_arr, y_arr)
        self.is_trained = True

        # Log feature importances
        feature_names = ["calorie_fit", "region_match", "state_match", "budget_fit", "protein_norm", "rating_norm"]
        importances = dict(zip(feature_names, self.model.feature_importances_))
        logger.info("Model trained. Feature importances: %s", importances)

        # Save to disk
        self.save_model(save_path or MODEL_PATH)
        return True


# Module-level singleton
ranker = MLRanker()
