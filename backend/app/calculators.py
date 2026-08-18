"""
Rule-based calculators – deterministic, auditable health-math.
These are the source of truth; the ML features always respect the
targets these functions produce.

Implements: BMI, BMR (Mifflin-St Jeor), TDEE, daily calorie target,
macro/micro nutrition targets, water intake, and meal timing.
"""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENT = {
    "lose": -0.20,       # 20 % deficit
    "maintain": 0.0,
    "gain": 0.15,        # 15 % surplus
}

MIN_SAFE_CALORIES = {"male": 1500, "female": 1200}


# ─────────────────────────────────────────────
# BMI
# ─────────────────────────────────────────────
def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    """BMI = weight (kg) / height² (m²).  Uses Asian cutoffs."""
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 23:
        category = "Normal (Asian cutoff)"
    elif bmi < 25:
        category = "Overweight (Asian cutoff)"
    elif bmi < 30:
        category = "Obese Class I"
    else:
        category = "Obese Class II+"

    # Healthy-weight range for this height
    low = round(18.5 * height_m ** 2, 1)
    high = round(23.0 * height_m ** 2, 1)

    return {
        "bmi": bmi,
        "category": category,
        "healthy_weight_range": f"{low}–{high} kg",
    }


# ─────────────────────────────────────────────
# BMR  (Mifflin-St Jeor)
# ─────────────────────────────────────────────
def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    if sex.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 1)


# ─────────────────────────────────────────────
# TDEE
# ─────────────────────────────────────────────
def calculate_tdee(bmr: float, activity_level: str) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier, 1)


# ─────────────────────────────────────────────
# Daily calorie target
# ─────────────────────────────────────────────
def calculate_daily_calorie_target(tdee: float, goal: str, sex: str) -> dict:
    adjustment = GOAL_ADJUSTMENT.get(goal, 0.0)
    target = tdee * (1 + adjustment)

    caution = None
    floor = MIN_SAFE_CALORIES.get(sex.lower(), 1200)
    if target < floor:
        target = floor
        caution = f"Target capped at the safe minimum of {floor} kcal/day for {sex}."

    # Macro split: 30 % protein / 45 % carbs / 25 % fat
    protein_g = round((target * 0.30) / 4, 1)
    carbs_g   = round((target * 0.45) / 4, 1)
    fat_g     = round((target * 0.25) / 9, 1)

    return {
        "daily_calorie_target": round(target, 1),
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "caution": caution,
    }


# ─────────────────────────────────────────────
# Nutrition targets (macros + micros)
# ─────────────────────────────────────────────
def calculate_nutrition_targets(weight_kg: float, sex: str, goal: str, tdee: float) -> dict:
    cal = calculate_daily_calorie_target(tdee, goal, sex)
    calories = cal["daily_calorie_target"]

    return {
        "calories": calories,
        "protein_g": round((calories * 0.30) / 4, 1),
        "carbs_g":   round((calories * 0.45) / 4, 1),
        "fat_g":     round((calories * 0.25) / 9, 1),
        "fiber_g":   38.0 if sex.lower() == "male" else 25.0,
        "iron_mg":   8.0  if sex.lower() == "male" else 18.0,
        "calcium_mg": 1000.0,
    }


# ─────────────────────────────────────────────
# Water intake
# ─────────────────────────────────────────────
def calculate_water_intake(weight_kg: float, activity_level: str, climate: str = "moderate") -> dict:
    base_ml_per_kg = 33
    liters = (weight_kg * base_ml_per_kg) / 1000

    if activity_level in ("active", "very_active"):
        liters += 0.5
    if climate in ("hot_humid", "hot"):
        liters += 0.5

    liters = round(liters, 2)
    glasses = round(liters / 0.25)   # ~250 ml per glass

    return {"liters_per_day": liters, "glasses_per_day": glasses}


# ─────────────────────────────────────────────
# Meal timing
# ─────────────────────────────────────────────
def _parse_time(t: str) -> int:
    """Parse 'HH:MM' to minutes from midnight."""
    parts = t.strip().split(":")
    return int(parts[0]) * 60 + (int(parts[1]) if len(parts) > 1 else 0)


def _fmt(minutes: int) -> str:
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def calculate_meal_timing(
    wake_time: str = "07:00",
    sleep_time: str = "23:00",
    exercise_time: str = "",
    meals_per_day: int = 4,
) -> dict:
    wake = _parse_time(wake_time)
    sleep = _parse_time(sleep_time)
    if sleep <= wake:
        sleep += 24 * 60

    awake = sleep - wake
    gap = awake // (meals_per_day + 1)

    result = {
        "breakfast": _fmt(wake + gap),
        "lunch":     _fmt(wake + gap * 2),
        "snack":     _fmt(wake + gap * 3),
        "dinner":    _fmt(sleep - gap),
    }

    if exercise_time:
        ex = _parse_time(exercise_time)
        result["pre_workout"]  = _fmt(ex - 60)
        result["post_workout"] = _fmt(ex + 30)
    else:
        result["pre_workout"] = None
        result["post_workout"] = None

    return result
