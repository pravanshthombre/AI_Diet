"""
Personalized meal recommendation engine.

Cold start (no history)  → rule-based ranking by calorie fit + feature ranker.
Warm state (has history) → content-based filtering via cosine similarity
                           on normalized nutrient vectors, blended with feature ranker.
Hard constraints (diet type, allergies, dislikes, Jain, budget) are always enforced
BEFORE any ML ranking.
"""
import numpy as np
from sqlalchemy.orm import Session

from .models import Food, MealLog, Feedback, User
from .features import food_vector, cosine_scores
from .ml_ranker import ranker


def _parse_csv_field(value: str | None) -> list[str]:
    return [item.strip().lower() for item in (value or "").split(",") if item.strip()]


def _food_matches_dislike(food: Food, dislike: str) -> bool:
    """Match dislike tokens against food name (substring, case-insensitive)."""
    name = food.name.lower()
    return dislike in name or name in dislike


def _apply_hard_constraints(
    foods: list[Food],
    diet_type: str,
    allergies: list[str] | None = None,
    food_dislikes: list[str] | None = None,
) -> list[Food]:
    """Constraints that must NEVER be violated."""
    filtered = []
    for f in foods:
        if diet_type == "jain" and not f.is_jain_friendly:
            continue
        if diet_type == "vegan" and f.diet_type not in ("vegan",):
            continue
        if diet_type == "vegetarian" and f.diet_type == "non_vegetarian":
            continue
        if diet_type == "eggetarian" and f.diet_type == "non_vegetarian":
            continue

        if allergies:
            food_allergens = set(
                a.strip().lower() for a in (f.allergens or "").split(",") if a.strip()
            )
            if any(a.lower() in food_allergens for a in allergies):
                continue

        if food_dislikes and any(_food_matches_dislike(f, d) for d in food_dislikes):
            continue

        filtered.append(f)
    return filtered


def _build_weighted_user_vector(
    db: Session,
    user_id: int,
    positive_ids: set[int],
) -> np.ndarray | None:
    """Build preference vector weighted by feedback ratings and meal logs."""
    if not positive_ids:
        return None

    foods = db.query(Food).filter(Food.id.in_(positive_ids)).all()
    if not foods:
        return None

    feedback = {
        fb.food_id: fb
        for fb in db.query(Feedback).filter(Feedback.user_id == user_id).all()
    }
    logged_ids = {
        ml.food_id
        for ml in db.query(MealLog).filter(MealLog.user_id == user_id).all()
    }

    vectors = []
    weights = []
    for food in foods:
        vec = food_vector(food)
        fb = feedback.get(food.id)
        if fb and fb.rating is not None:
            weight = fb.rating / 5.0
        elif fb and fb.liked is True:
            weight = 1.0
        elif food.id in logged_ids:
            weight = 0.75
        else:
            weight = 0.5
        vectors.append(vec)
        weights.append(weight)

    weights_arr = np.array(weights, dtype=float)
    if weights_arr.sum() <= 0:
        return np.mean(vectors, axis=0)

    return np.average(vectors, axis=0, weights=weights_arr)


def recommend_meals(
    db: Session,
    user_id: int,
    region: str,
    diet_type: str,
    meal_slot: str,
    target_calories_for_slot: float,
    weekly_budget_inr: float | None = None,
    allergies: list[str] | None = None,
    food_dislikes: list[str] | None = None,
    top_n: int = 5,
) -> list[dict]:
    """Return top-N food recommendations for a meal slot."""

    candidates = (
        db.query(Food)
        .filter(Food.meal_slot == meal_slot)
        .filter((Food.region == region) | (Food.region == "pan_india"))
        .all()
    )
    candidates = _apply_hard_constraints(
        candidates, diet_type, allergies, food_dislikes
    )

    per_meal_budget = None
    if weekly_budget_inr:
        per_meal_budget = (weekly_budget_inr / 21) * 1.5
        candidates = [
            f for f in candidates if f.price_inr_per_serving <= per_meal_budget
        ]

    if not candidates:
        return []

    liked_ids = {
        fb.food_id
        for fb in db.query(Feedback).filter(
            Feedback.user_id == user_id, Feedback.liked == True
        )
    }
    logged_ids = {
        ml.food_id for ml in db.query(MealLog).filter(MealLog.user_id == user_id)
    }
    disliked_ids = {
        fb.food_id
        for fb in db.query(Feedback).filter(
            Feedback.user_id == user_id, Feedback.liked == False
        )
    }

    positive_ids = liked_ids | logged_ids
    candidates = [f for f in candidates if f.id not in disliked_ids]

    if not candidates:
        return []

    user = db.query(User).filter(User.id == user_id).first()

    content_scored: dict[int, tuple[float, str]] = {}
    if positive_ids:
        user_vector = _build_weighted_user_vector(db, user_id, positive_ids)
        if user_vector is not None:
            cand_vectors = np.array([food_vector(f) for f in candidates])
            sims = cosine_scores(user_vector, cand_vectors)
            for food, sim in zip(candidates, sims):
                calorie_penalty = abs(
                    food.calories_per_serving - target_calories_for_slot
                ) / max(target_calories_for_slot, 1)
                score = float(sim) - 0.3 * calorie_penalty
                content_scored[food.id] = (score, "Similar to foods you've enjoyed")
        else:
            for food, score in _cold_start_score(candidates, target_calories_for_slot):
                content_scored[food.id] = (score, "Matches your calorie target")
    else:
        for food, score in _cold_start_score(candidates, target_calories_for_slot):
            content_scored[food.id] = (score, "Matches your calorie target")

    ml_ranked = ranker.predict_score(
        user=user,
        candidates=candidates,
        db=db,
        target_calories=target_calories_for_slot,
        user_id=user_id,
        per_meal_budget=per_meal_budget,
    )

    ml_scores = {item["food"].id: item["ml_score"] for item in ml_ranked}
    ml_max = max(ml_scores.values()) if ml_scores else 1.0
    content_max = max(s[0] for s in content_scored.values()) if content_scored else 1.0

    blended = []
    for food in candidates:
        content_score, reason = content_scored.get(
            food.id, (0.0, "Personalized match")
        )
        norm_content = content_score / content_max if content_max > 0 else 0.0
        norm_ml = ml_scores.get(food.id, 0.0) / ml_max if ml_max > 0 else 0.0
        final_score = 0.6 * norm_content + 0.4 * norm_ml
        blended.append((food, final_score, reason))

    blended.sort(key=lambda x: x[1], reverse=True)
    top = blended[:top_n]

    return [
        {"food": food, "score": round(float(score), 3), "reason": reason}
        for food, score, reason in top
    ]


def _cold_start_score(candidates, target_calories):
    scored = []
    for food in candidates:
        calorie_diff = abs(food.calories_per_serving - target_calories)
        score = 1 / (1 + calorie_diff / max(target_calories, 1))
        scored.append((food, score))
    return scored
