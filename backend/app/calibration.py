"""
Dynamic Nutritional Calibration Engine.
Calibrates empirical baseline nutritional values (IFCT 2017)
according to actual culinary preparation, oil/lipid density,
portion mass, and ingredient additions.
"""
from typing import Dict, Any, Optional
from .models import Food

# Preparation / Cooking style modifiers (applied to lipid and calorie densities)
PREPARATION_MODIFIERS = {
    "steamed_boiled": {
        "fat_multiplier": 0.90,
        "calorie_multiplier": 0.95,
        "label": "Steamed / Boiled (No added fat)",
        "desc": "Minimal or zero oil (e.g., idli, steamed dal, plain rice)"
    },
    "homestyle_sauteed": {
        "fat_multiplier": 1.00,
        "calorie_multiplier": 1.00,
        "label": "Home-style Cooked (Standard IFCT)",
        "desc": "Prepared with 1 standard teaspoon of oil/tadka per serving"
    },
    "restaurant_rich": {
        "fat_multiplier": 1.45,
        "calorie_multiplier": 1.25,
        "label": "Restaurant / Dhaba (Rich Ghee / Butter)",
        "desc": "Generous ghee/butter tadka, heavy cream or restaurant gravy"
    },
    "deep_fried": {
        "fat_multiplier": 1.80,
        "calorie_multiplier": 1.50,
        "label": "Deep Fried / Extra Crispy",
        "desc": "High oil absorption (e.g., puri, pakora, samosa, bhature)"
    }
}

# Add-on items with direct macro increments
ADD_ON_MODIFIERS = {
    "extra_butter_cube": {"cal": 75, "protein": 0.1, "carbs": 0.0, "fat": 8.2, "label": "1 Cube Butter (10g)"},
    "extra_ghee_spoon":  {"cal": 112, "protein": 0.0, "carbs": 0.0, "fat": 12.5, "label": "1 Tbsp Pure Ghee"},
    "cheese_slice":      {"cal": 80, "protein": 5.0, "carbs": 1.0, "fat": 6.5, "label": "1 Slice Cheese"},
    "paneer_cubes_50g":  {"cal": 130, "protein": 9.0, "carbs": 2.0, "fat": 10.0, "label": "50g Fresh Paneer"},
}

STANDARD_SERVING_GRAMS = 150.0  # Default reference mass (katori/cup)


def calibrate_food_nutrition(
    food: Food,
    portion_grams: Optional[float] = None,
    serving_multiplier: Optional[float] = None,
    prep_style: str = "homestyle_sauteed",
    additions: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Calibrates baseline IFCT food record into empirical real-plate nutrition.

    Formula:
        v_calibrated = s_portion * (v_IFCT (x) kappa_prep) + delta_additions
    """
    # 1. Determine portion scale factor
    if portion_grams and portion_grams > 0:
        scale = portion_grams / STANDARD_SERVING_GRAMS
    elif serving_multiplier and serving_multiplier > 0:
        scale = serving_multiplier
    else:
        scale = 1.0

    # 2. Extract preparation modifier
    prep = PREPARATION_MODIFIERS.get(prep_style, PREPARATION_MODIFIERS["homestyle_sauteed"])
    fat_mult = prep["fat_multiplier"]
    cal_mult = prep["calorie_multiplier"]

    # 3. Base IFCT metrics
    base_cal = float(food.calories_per_serving or 0)
    base_pro = float(food.protein_g or 0)
    base_carbs = float(food.carbs_g or 0)
    base_fat = float(food.fat_g or 0)
    base_fiber = float(food.fiber_g or 0)
    base_iron = float(food.iron_mg or 0)
    base_calcium = float(food.calcium_mg or 0)

    # 4. Scale by portion and cooking modifier
    calibrated_fat = round(base_fat * fat_mult * scale, 1)
    calibrated_pro = round(base_pro * scale, 1)
    calibrated_carbs = round(base_carbs * scale, 1)
    calibrated_fiber = round(base_fiber * scale, 1)
    calibrated_iron = round(base_iron * scale, 1)
    calibrated_calcium = round(base_calcium * scale, 1)

    # Calories recalculated through dynamic Atwater density with prep multiplier
    calibrated_cal = round((base_cal * cal_mult) * scale, 1)

    # 5. Apply optional ingredient add-ons
    addon_details = []
    if additions:
        for item in additions:
            mod = ADD_ON_MODIFIERS.get(item)
            if mod:
                calibrated_cal += mod["cal"]
                calibrated_pro += mod["protein"]
                calibrated_carbs += mod["carbs"]
                calibrated_fat += mod["fat"]
                addon_details.append(mod["label"])

    calibrated_cal = round(calibrated_cal, 1)
    calibrated_pro = round(calibrated_pro, 1)
    calibrated_carbs = round(calibrated_carbs, 1)
    calibrated_fat = round(calibrated_fat, 1)

    # 6. Delta variance compared to IFCT baseline
    calorie_diff = round(calibrated_cal - base_cal, 1)
    fat_diff = round(calibrated_fat - base_fat, 1)

    return {
        "food_id": food.id,
        "food_name": food.name,
        "portion_grams": portion_grams or round(scale * STANDARD_SERVING_GRAMS, 1),
        "portion_scale": round(scale, 2),
        "prep_style": prep_style,
        "prep_label": prep["label"],
        "additions": addon_details,
        # Baseline IFCT
        "baseline_ifct": {
            "calories": base_cal,
            "protein_g": base_pro,
            "carbs_g": base_carbs,
            "fat_g": base_fat,
        },
        # Calibrated Output
        "calibrated": {
            "calories": calibrated_cal,
            "protein_g": calibrated_pro,
            "carbs_g": calibrated_carbs,
            "fat_g": calibrated_fat,
            "fiber_g": calibrated_fiber,
            "iron_mg": calibrated_iron,
            "calcium_mg": calibrated_calcium,
        },
        "variance": {
            "calorie_delta": calorie_diff,
            "fat_delta": fat_diff,
            "explanation": (
                f"{'+' if calorie_diff >= 0 else ''}{calorie_diff} kcal vs. IFCT baseline "
                f"({prep['label']}, portion: {round(scale * STANDARD_SERVING_GRAMS)}g)"
            )
        }
    }
