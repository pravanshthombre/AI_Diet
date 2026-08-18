"""
Full daily diet plan generator.
Builds a complete day's meals: breakfast, lunch, dinner, snacks,
with water & timing suggestions and nutrition summary.
"""
from sqlalchemy.orm import Session
from . import calculators
from .recommender import recommend_meals, _parse_csv_field
from .models import User


SLOT_WEIGHTS = {
    "breakfast": 0.25,
    "lunch":     0.35,
    "dinner":    0.30,
    "snack":     0.10,
}


def generate_daily_plan(db: Session, user: User) -> dict:
    """
    Generate a complete daily diet plan for a user.
    Returns one primary pick per slot plus alternatives; totals reflect
    the primary pick only so daily calories stay realistic.
    """
    bmr = calculators.calculate_bmr(user.weight_kg, user.height_cm, user.age, user.sex)
    tdee = calculators.calculate_tdee(bmr, user.activity_level)
    cal_plan = calculators.calculate_daily_calorie_target(tdee, user.goal, user.sex)
    daily_cal = cal_plan["daily_calorie_target"]

    water = calculators.calculate_water_intake(user.weight_kg, user.activity_level)
    timing = calculators.calculate_meal_timing(
        wake_time=user.wake_time or "07:00",
        sleep_time=user.sleep_time or "23:00",
        exercise_time=user.exercise_time or "",
        meals_per_day=user.meals_per_day or 4,
    )

    allergies = _parse_csv_field(user.allergies)
    food_dislikes = _parse_csv_field(user.food_dislikes)

    plan = {}
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "cost": 0}

    for slot, weight in SLOT_WEIGHTS.items():
        slot_target = daily_cal * weight
        recs = recommend_meals(
            db=db,
            user_id=user.id,
            region=user.region or "pan_india",
            diet_type=user.diet_type or "vegetarian",
            meal_slot=slot,
            target_calories_for_slot=slot_target,
            weekly_budget_inr=user.weekly_budget_inr,
            allergies=allergies,
            food_dislikes=food_dislikes,
            top_n=3 if slot != "snack" else 2,
        )

        slot_items = []
        for i, rec in enumerate(recs):
            food = rec["food"]
            item = {
                "food": food,
                "servings": 1.0,
                "score": rec["score"],
                "reason": rec["reason"],
                "is_primary": i == 0,
            }
            slot_items.append(item)

            if i == 0:
                totals["calories"] += food.calories_per_serving
                totals["protein"]  += food.protein_g
                totals["carbs"]    += food.carbs_g
                totals["fat"]      += food.fat_g
                totals["fiber"]    += food.fiber_g
                totals["cost"]     += food.price_inr_per_serving

        plan[slot] = slot_items

    return {
        "breakfast": plan.get("breakfast", []),
        "lunch":     plan.get("lunch", []),
        "dinner":    plan.get("dinner", []),
        "snack":     plan.get("snack", []),
        "total_calories": round(totals["calories"], 1),
        "total_protein":  round(totals["protein"], 1),
        "total_carbs":    round(totals["carbs"], 1),
        "total_fat":      round(totals["fat"], 1),
        "total_fiber":    round(totals["fiber"], 1),
        "total_cost":     round(totals["cost"], 1),
        "calorie_target": daily_cal,
        "meal_timing":    timing,
        "water":          water,
    }
