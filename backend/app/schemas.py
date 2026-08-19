"""
Pydantic request/response schemas for the NutriCalc API.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---- User ----
class UserCreate(BaseModel):
    name: str
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str = "maintain"
    region: str = "pan_india"
    state: str = ""
    diet_type: str = "vegetarian"
    weekly_budget_inr: Optional[float] = None
    allergies: Optional[str] = ""
    food_dislikes: Optional[str] = ""
    wake_time: Optional[str] = "07:00"
    sleep_time: Optional[str] = "23:00"
    exercise_time: Optional[str] = ""
    meals_per_day: Optional[int] = 4


class UserOut(BaseModel):
    id: int
    name: str
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str
    region: str
    state: str
    diet_type: str
    weekly_budget_inr: Optional[float] = None
    allergies: Optional[str] = ""
    food_dislikes: Optional[str] = ""
    wake_time: Optional[str] = "07:00"
    sleep_time: Optional[str] = "23:00"
    exercise_time: Optional[str] = ""
    meals_per_day: Optional[int] = 4

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    region: Optional[str] = None
    state: Optional[str] = None
    diet_type: Optional[str] = None
    weekly_budget_inr: Optional[float] = None
    allergies: Optional[str] = None
    food_dislikes: Optional[str] = None
    wake_time: Optional[str] = None
    sleep_time: Optional[str] = None
    exercise_time: Optional[str] = None
    meals_per_day: Optional[int] = None


# ---- Food ----
class FoodOut(BaseModel):
    id: int
    name: str
    region: str
    state: str
    diet_type: str
    is_jain_friendly: bool
    meal_slot: str
    calories_per_serving: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    iron_mg: float
    calcium_mg: float
    price_inr_per_serving: float
    allergens: str
    prep_method: str
    seasonality: str

    class Config:
        from_attributes = True


# ---- Calculator Results ----
class BMIResult(BaseModel):
    bmi: float
    category: str
    healthy_weight_range: Optional[str] = None


class BMRTDEEResult(BaseModel):
    bmr: float
    tdee: float


class CalorieTargetResult(BaseModel):
    daily_calorie_target: float
    protein_g: float
    carbs_g: float
    fat_g: float
    caution: Optional[str] = None


class NutritionTargetsResult(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    iron_mg: float
    calcium_mg: float


class WaterIntakeResult(BaseModel):
    liters_per_day: float
    glasses_per_day: int


class MealTimingResult(BaseModel):
    breakfast: str
    lunch: str
    snack: str
    dinner: str
    pre_workout: Optional[str] = None
    post_workout: Optional[str] = None


# ---- Recommendation ----
class RecommendationOut(BaseModel):
    food: FoodOut
    score: float
    reason: str


# ---- Meal Plan ----
class MealPlanFood(BaseModel):
    food: FoodOut
    servings: float
    score: float
    reason: str


class DailyPlanOut(BaseModel):
    breakfast: List[MealPlanFood]
    lunch: List[MealPlanFood]
    dinner: List[MealPlanFood]
    snack: List[MealPlanFood]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    total_cost: float
    calorie_target: float
    meal_timing: MealTimingResult
    water: WaterIntakeResult


# ---- Logging ----
class MealLogCreate(BaseModel):
    user_id: int
    food_id: int
    meal_slot: Optional[str] = "lunch"
    servings: Optional[float] = 1.0


class WaterLogCreate(BaseModel):
    user_id: int
    amount_ml: float


class WeightLogCreate(BaseModel):
    user_id: int
    weight_kg: float


# ---- Feedback ----
class FeedbackCreate(BaseModel):
    user_id: int
    food_id: int
    liked: Optional[bool] = None
    rating: Optional[int] = None


# ---- Food Preferences ----
class FoodPreferenceCreate(BaseModel):
    user_id: int
    food_id: int
    meal_slot: Optional[str] = ""


class FoodPreferenceOut(BaseModel):
    id: int
    user_id: int
    food_id: int
    meal_slot: str
    food: FoodOut

    class Config:
        from_attributes = True


# ---- Nutrition Gap ----
class NutritionGapItem(BaseModel):
    nutrient: str
    target: float
    actual: float
    percentage: float
    level: str            # "good" | "low" | "moderate_concern" | "high_concern"
    message: str


class NutritionGapResult(BaseModel):
    gaps: List[NutritionGapItem]
    disclaimer: str


# ---- Tracking ----
class TrackingMealItem(BaseModel):
    food_name: str
    meal_slot: str
    calories: float
    protein: float
    servings: float
    logged_at: str


class TrackingSummary(BaseModel):
    date: str
    target_calories: float
    actual_calories: float
    target_protein: float
    actual_protein: float
    target_fiber: float
    actual_fiber: float
    target_water_ml: float
    actual_water_ml: float
    meals: List[TrackingMealItem]
    total_cost: float


# ---- Substitution ----
class SubstituteRequest(BaseModel):
    meal_slot: str
    food_id: int
    reason: Optional[str] = ""


# ---- Chat ----
class ChatRequest(BaseModel):
    user_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    intent: str
    data: Optional[dict] = None
