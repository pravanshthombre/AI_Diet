"""
Budget-constrained diet optimizer.
Selects the best combination of foods per meal slot to maximize
nutrition coverage while staying within the user's daily budget.
Uses a greedy approach scored by nutrient-per-rupee efficiency.
"""
from sqlalchemy.orm import Session
from .models import Food


def optimize_budget(
    db: Session,
    daily_budget_inr: float,
    diet_type: str,
    region: str,
    calorie_target: float,
) -> dict:
    """
    Return budget-optimized food picks per slot.
    """
    slot_budgets = {
        "breakfast": daily_budget_inr * 0.20,
        "lunch":     daily_budget_inr * 0.35,
        "dinner":    daily_budget_inr * 0.30,
        "snack":     daily_budget_inr * 0.15,
    }
    slot_calories = {
        "breakfast": calorie_target * 0.25,
        "lunch":     calorie_target * 0.35,
        "dinner":    calorie_target * 0.30,
        "snack":     calorie_target * 0.10,
    }

    result = {}
    total_cost = 0
    total_cals = 0

    for slot, budget in slot_budgets.items():
        foods = (
            db.query(Food)
            .filter(Food.meal_slot == slot)
            .filter(Food.price_inr_per_serving <= budget)
            .filter((Food.region == region) | (Food.region == "pan_india"))
            .all()
        )

        # Filter by diet type
        if diet_type == "vegan":
            foods = [f for f in foods if f.diet_type == "vegan"]
        elif diet_type == "vegetarian":
            foods = [f for f in foods if f.diet_type != "non_vegetarian"]
        elif diet_type == "eggetarian":
            foods = [f for f in foods if f.diet_type != "non_vegetarian"]
        elif diet_type == "jain":
            foods = [f for f in foods if f.is_jain_friendly]

        if not foods:
            result[slot] = []
            continue

        target_cals = slot_calories[slot]

        # Score: nutrition efficiency per rupee, penalizing calorie overshoot
        def score(f):
            cal_fit = 1.0 / (1 + abs(f.calories_per_serving - target_cals) / max(target_cals, 1))
            protein_per_rs = f.protein_g / max(f.price_inr_per_serving, 1)
            return cal_fit * 0.6 + protein_per_rs * 0.01 * 0.4

        foods.sort(key=score, reverse=True)
        pick = foods[0]
        result[slot] = {
            "food_id": pick.id,
            "food_name": pick.name,
            "calories": pick.calories_per_serving,
            "protein_g": pick.protein_g,
            "cost_inr": pick.price_inr_per_serving,
        }
        total_cost += pick.price_inr_per_serving
        total_cals += pick.calories_per_serving

    return {
        "plan": result,
        "total_cost_inr": round(total_cost, 1),
        "total_calories": round(total_cals, 1),
        "daily_budget_inr": daily_budget_inr,
        "remaining_budget": round(daily_budget_inr - total_cost, 1),
    }
