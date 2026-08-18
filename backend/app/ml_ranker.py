"""
Feature-based meal ranker with optional LightGBM/XGBoost training hook.

Blends explicit feedback, calorie fit, regional preference, and budget fit.
Falls back to rules when no trained booster is loaded.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# In a real scenario: import lightgbm as lgb

NUTRIENT_FIELDS = [
    "calories_per_serving",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
]


class MLRanker:
    def __init__(self, model_path: str = None):
        self.model = None
        self.is_trained = False
        if model_path:
            self.load_model(model_path)

    def load_model(self, path: str):
        """Load a pre-trained LightGBM/XGBoost model."""
        # self.model = lgb.Booster(model_file=path)
        self.is_trained = True

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
        region_match = 1.0 if user.region == candidate_food.region else 0.0
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
                score = float(self.model.predict([features])[0])
                reason = "ML model ranking"
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
        """
        from .models import Feedback, MealLog, User, Food

        rows_x = []
        rows_y = []

        feedback_rows = db.query(Feedback).all()
        for fb in feedback_rows:
            user = db.query(User).filter(User.id == fb.user_id).first()
            food = db.query(Food).filter(Food.id == fb.food_id).first()
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

        logged = db.query(MealLog).all()
        for log in logged:
            user = db.query(User).filter(User.id == log.user_id).first()
            food = db.query(Food).filter(Food.id == log.food_id).first()
            if not user or not food:
                continue
            rows_x.append(
                self.extract_features(user, food, target_calories=500.0)
            )
            rows_y.append(0.75)

        return rows_x, rows_y

    def train_model(self, db: Session, save_path: str):
        """Train ranker when enough labeled data exists."""
        X, y = self.collect_training_data(db)
        if len(X) < 10:
            self.is_trained = False
            return False

        # train_data = lgb.Dataset(X, label=y)
        # self.model = lgb.train(params, train_data, 100)
        # self.model.save_model(save_path)
        self.is_trained = True
        return True


ranker = MLRanker()
