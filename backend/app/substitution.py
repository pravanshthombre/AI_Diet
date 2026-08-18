"""
Food substitution engine.
Finds the best replacement for a food, preserving calories, protein,
dietary preference, budget, and cuisine compatibility.
Uses cosine similarity on normalized nutrient vectors.
"""
import numpy as np
from sqlalchemy.orm import Session
from .models import Food
from .features import food_vector, cosine_scores


def find_substitutes(
    db: Session,
    food_id: int,
    meal_slot: str,
    diet_type: str,
    region: str = "",
    budget_ceiling: float | None = None,
    top_n: int = 5,
) -> list[dict]:
    """
    Find foods most similar to the given food in nutrient profile,
    respecting diet-type and optional budget constraints.
    """
    original = db.query(Food).filter(Food.id == food_id).first()
    if not original:
        return []

    candidates = (
        db.query(Food)
        .filter(Food.meal_slot == meal_slot)
        .filter(Food.id != food_id)
        .all()
    )

    filtered = []
    for f in candidates:
        if diet_type == "vegan" and f.diet_type != "vegan":
            continue
        if diet_type == "vegetarian" and f.diet_type == "non_vegetarian":
            continue
        if diet_type == "eggetarian" and f.diet_type == "non_vegetarian":
            continue
        if diet_type == "jain" and not f.is_jain_friendly:
            continue
        if budget_ceiling and f.price_inr_per_serving > budget_ceiling:
            continue
        if region and region not in ("", "pan_india"):
            if f.region not in (region, "pan_india"):
                continue
        filtered.append(f)

    if not filtered:
        return []

    orig_vec = food_vector(original)
    cand_vecs = [food_vector(f) for f in filtered]
    sims = cosine_scores(orig_vec, np.array(cand_vecs))

    results = sorted(zip(filtered, sims), key=lambda x: x[1], reverse=True)[:top_n]

    return [
        {
            "food": sub,
            "similarity": round(float(sim), 3),
            "calorie_diff": round(sub.calories_per_serving - original.calories_per_serving, 1),
            "cost_diff": round(sub.price_inr_per_serving - original.price_inr_per_serving, 1),
        }
        for sub, sim in results
    ]
