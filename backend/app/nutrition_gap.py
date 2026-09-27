"""
Nutrition deficiency warning system.

Monitors potential dietary gaps for protein, iron, fiber (and future
micronutrients). Three warning levels per the PRD:
  - good: intake is >= 80% of target
  - low: potentially below target (60-80%)
  - moderate_concern: repeatedly low over multiple days (40-60%)
  - high_concern: persistent significant gap (<40%)

IMPORTANT: This system detects potential *dietary* gaps, NOT medical
deficiencies. Food logs alone cannot diagnose deficiency.
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from .models import MealLog, Food
from . import calculators

logger = logging.getLogger("nutricalc.nutrition_gap")

DISCLAIMER = (
    "These are potential dietary gap estimates based on your food logs, "
    "not medical diagnoses. Actual nutrient absorption varies. "
    "Please consult a healthcare professional for medical nutrition advice."
)


def calculate_nutrition_gaps(
    db: Session,
    user_id: int,
    sex: str,
    weight_kg: float,
    goal: str,
    tdee: float,
    days: int = 1,
) -> dict:
    """
    Compare logged nutrient intake vs targets over last N days.
    """
    targets = calculators.calculate_nutrition_targets(weight_kg, sex, goal, tdee)

    # Get meals logged in the time window
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # FIXED: Batch load foods via JOIN instead of N+1 individual queries
    logs_with_food = (
        db.query(MealLog, Food)
        .join(Food, MealLog.food_id == Food.id)
        .filter(MealLog.user_id == user_id)
        .filter(MealLog.logged_at >= cutoff)
        .all()
    )

    if not logs_with_food:
        logger.info("No meals logged for user %d in last %d day(s)", user_id, days)
        return {
            "gaps": [],
            "disclaimer": DISCLAIMER,
            "message": "No meals logged yet. Start logging to see nutrition analysis.",
        }

    logger.info(
        "Analyzing %d meal logs for user %d over %d day(s)",
        len(logs_with_food), user_id, days,
    )

    # Sum up nutrients from logged foods
    totals = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0, "iron_mg": 0}

    for log, food in logs_with_food:
        s = log.servings or 1.0
        totals["calories"]  += food.calories_per_serving * s
        totals["protein_g"] += food.protein_g * s
        totals["carbs_g"]   += food.carbs_g * s
        totals["fat_g"]     += food.fat_g * s
        totals["fiber_g"]   += food.fiber_g * s
        totals["iron_mg"]   += food.iron_mg * s

    # Daily average
    daily_avg = {k: v / max(days, 1) for k, v in totals.items()}

    # Compare against targets
    nutrients_to_check = [
        ("Protein",  "protein_g",  targets["protein_g"],  "g"),
        ("Iron",     "iron_mg",    targets["iron_mg"],     "mg"),
        ("Fiber",    "fiber_g",    targets["fiber_g"],     "g"),
        ("Calories", "calories",   targets["calories"],    "kcal"),
    ]

    gaps = []
    for name, key, target, unit in nutrients_to_check:
        actual = daily_avg.get(key, 0)
        pct = (actual / target * 100) if target > 0 else 100

        if pct >= 80:
            level = "good"
            msg = f"{name} intake looks adequate ({actual:.1f}{unit} / {target:.0f}{unit} target)."
        elif pct >= 60:
            level = "low"
            msg = f"{name} intake may be below your daily target. Consider adding {name.lower()}-rich foods."
        elif pct >= 40:
            level = "moderate_concern"
            msg = f"{name} intake is notably below target. Persistent low {name.lower()} may affect health."
        else:
            level = "high_concern"
            msg = f"{name} intake is significantly below target. Please review your diet and consider consulting a professional."

        gaps.append({
            "nutrient": name,
            "target": round(target, 1),
            "actual": round(actual, 1),
            "percentage": round(pct, 1),
            "level": level,
            "message": msg,
        })

    logger.info("Nutrition gap analysis complete for user %d: %s",
                user_id, {g["nutrient"]: g["level"] for g in gaps})
    return {"gaps": gaps, "disclaimer": DISCLAIMER}
