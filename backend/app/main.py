"""
NutriCalc API — AI/ML Diet & Calorie Calculator.

Full FastAPI backend with:
  - User CRUD
  - Health calculators (BMI, BMR, TDEE, calories, nutrition targets, water, meal timing)
  - ML-based food recommendations
  - Daily diet plan generator
  - Food substitution
  - Meal/water/weight logging
  - Nutrition gap detection
  - Daily tracking summary
  - AI chat assistant
  - Food database browser

Run:
    pip install -r requirements.txt
    python -m app.seed_data
    uvicorn app.main:app --reload
"""
import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from .database import Base, engine, get_db
from . import models, schemas, calculators
from .recommender import recommend_meals, _parse_csv_field
from .meal_planner import generate_daily_plan
from .substitution import find_substitutes
from .nutrition_gap import calculate_nutrition_gaps
from .chat import process_chat

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NutriCalc API",
    description="AI/ML-powered Diet & Calorie Calculator for Indian regional nutrition",
    version="2.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def api_health():
    return {"status": "ok", "message": "NutriCalc API is running. Visit /docs for interactive API."}


# ═══════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════

@app.post("/users", response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = models.User(**user_in.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, updates: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


# ═══════════════════════════════════════════════════════════════════
# CALCULATORS
# ═══════════════════════════════════════════════════════════════════

@app.get("/calculators/bmi")
def calc_bmi(weight_kg: float, height_cm: float):
    return calculators.calculate_bmi(weight_kg, height_cm)


@app.get("/calculators/bmr-tdee")
def calc_bmr_tdee(weight_kg: float, height_cm: float, age: int, sex: str, activity_level: str):
    bmr = calculators.calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculators.calculate_tdee(bmr, activity_level)
    return {"bmr": round(bmr, 1), "tdee": round(tdee, 1)}


@app.get("/calculators/calorie-target")
def calc_calorie_target(tdee: float, goal: str, sex: str):
    return calculators.calculate_daily_calorie_target(tdee, goal, sex)


@app.get("/calculators/nutrition-targets")
def calc_nutrition_targets(weight_kg: float, sex: str, goal: str = "maintain"):
    bmr = calculators.calculate_bmr(weight_kg, 170, 30, sex)  # defaults for standalone use
    tdee = calculators.calculate_tdee(bmr, "moderate")
    return calculators.calculate_nutrition_targets(weight_kg, sex, goal, tdee)


@app.get("/calculators/water-intake")
def calc_water_intake(weight_kg: float, activity_level: str, climate: str = "moderate"):
    return calculators.calculate_water_intake(weight_kg, activity_level, climate)


@app.get("/calculators/meal-timing")
def calc_meal_timing(
    wake_time: str = "07:00",
    sleep_time: str = "23:00",
    exercise_time: str = "",
    meals_per_day: int = 4,
):
    return calculators.calculate_meal_timing(wake_time, sleep_time, exercise_time, meals_per_day)


# ═══════════════════════════════════════════════════════════════════
# FOOD DATABASE
# ═══════════════════════════════════════════════════════════════════

@app.get("/foods", response_model=List[schemas.FoodOut])
def list_foods(
    region: Optional[str] = None,
    state: Optional[str] = None,
    diet_type: Optional[str] = None,
    meal_slot: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Food)
    if region:
        q = q.filter((models.Food.region == region) | (models.Food.region == "pan_india"))
    if state:
        q = q.filter((models.Food.state == state) | (models.Food.state == ""))
    if diet_type:
        if diet_type == "vegetarian":
            q = q.filter(models.Food.diet_type != "non_vegetarian")
        elif diet_type == "vegan":
            q = q.filter(models.Food.diet_type == "vegan")
        else:
            q = q.filter(models.Food.diet_type == diet_type)
    if meal_slot:
        q = q.filter(models.Food.meal_slot == meal_slot)
    if search:
        q = q.filter(models.Food.name.ilike(f"%{search}%"))
    return q.all()


# ═══════════════════════════════════════════════════════════════════
# ML RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════

@app.get("/recommend/{user_id}")
def get_recommendations(
    user_id: int,
    meal_slot: str = Query("lunch", description="breakfast/lunch/dinner/snack"),
    top_n: int = 5,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bmr = calculators.calculate_bmr(user.weight_kg, user.height_cm, user.age, user.sex)
    tdee = calculators.calculate_tdee(bmr, user.activity_level)
    cal = calculators.calculate_daily_calorie_target(tdee, user.goal, user.sex)

    slot_weights = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}
    slot_target = cal["daily_calorie_target"] * slot_weights.get(meal_slot, 0.25)

    allergies = _parse_csv_field(user.allergies)
    food_dislikes = _parse_csv_field(user.food_dislikes)

    results = recommend_meals(
        db=db, user_id=user_id, region=user.region,
        diet_type=user.diet_type, meal_slot=meal_slot,
        target_calories_for_slot=slot_target,
        weekly_budget_inr=user.weekly_budget_inr,
        allergies=allergies,
        food_dislikes=food_dislikes,
        top_n=top_n,
    )

    return [
        {
            "food": schemas.FoodOut.model_validate(r["food"]),
            "score": r["score"],
            "reason": r["reason"],
        }
        for r in results
    ]


# ═══════════════════════════════════════════════════════════════════
# DAILY DIET PLAN
# ═══════════════════════════════════════════════════════════════════

@app.get("/diet-plan/{user_id}")
def get_diet_plan(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = generate_daily_plan(db, user)

    # Serialize food objects
    for slot in ["breakfast", "lunch", "dinner", "snack"]:
        for item in plan[slot]:
            item["food"] = schemas.FoodOut.model_validate(item["food"])

    return plan


@app.post("/diet-plan/{user_id}/substitute")
def substitute_food(
    user_id: int,
    req: schemas.SubstituteRequest,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    budget_ceiling = None
    if user.weekly_budget_inr:
        budget_ceiling = (user.weekly_budget_inr / 21) * 1.5

    subs = find_substitutes(
        db=db, food_id=req.food_id, meal_slot=req.meal_slot,
        diet_type=user.diet_type, region=user.region,
        budget_ceiling=budget_ceiling, top_n=5,
    )

    return [
        {
            "food": schemas.FoodOut.model_validate(s["food"]),
            "similarity": s["similarity"],
            "calorie_diff": s["calorie_diff"],
            "cost_diff": s["cost_diff"],
        }
        for s in subs
    ]


# ═══════════════════════════════════════════════════════════════════
# LOGGING (meals, water, weight)
# ═══════════════════════════════════════════════════════════════════

@app.post("/log-meal")
def log_meal(entry: schemas.MealLogCreate, db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == entry.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    if not db.query(models.Food).filter(models.Food.id == entry.food_id).first():
        raise HTTPException(status_code=404, detail="Food not found")

    log = models.MealLog(
        user_id=entry.user_id,
        food_id=entry.food_id,
        meal_slot=entry.meal_slot,
        servings=entry.servings or 1.0,
    )
    db.add(log)
    db.commit()
    return {"status": "logged", "id": log.id}


@app.post("/log-water")
def log_water(entry: schemas.WaterLogCreate, db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == entry.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

    log = models.WaterLog(user_id=entry.user_id, amount_ml=entry.amount_ml)
    db.add(log)
    db.commit()
    return {"status": "logged", "total_today_ml": _today_water(db, entry.user_id)}


@app.post("/log-weight")
def log_weight(entry: schemas.WeightLogCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log = models.WeightLog(user_id=entry.user_id, weight_kg=entry.weight_kg)
    db.add(log)
    # Also update user's current weight
    user.weight_kg = entry.weight_kg
    db.commit()
    return {"status": "logged", "weight_kg": entry.weight_kg}


# ═══════════════════════════════════════════════════════════════════
# FEEDBACK
# ═══════════════════════════════════════════════════════════════════

@app.post("/feedback")
def submit_feedback(entry: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == entry.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    if not db.query(models.Food).filter(models.Food.id == entry.food_id).first():
        raise HTTPException(status_code=404, detail="Food not found")

    fb = models.Feedback(
        user_id=entry.user_id,
        food_id=entry.food_id,
        liked=entry.liked,
        rating=entry.rating,
    )
    db.add(fb)
    db.commit()
    return {"status": "feedback recorded"}


# ═══════════════════════════════════════════════════════════════════
# NUTRITION GAPS
# ═══════════════════════════════════════════════════════════════════

@app.get("/nutrition-gaps/{user_id}")
def get_nutrition_gaps(
    user_id: int,
    days: int = 1,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bmr = calculators.calculate_bmr(user.weight_kg, user.height_cm, user.age, user.sex)
    tdee = calculators.calculate_tdee(bmr, user.activity_level)

    return calculate_nutrition_gaps(db, user_id, user.sex, user.weight_kg, user.goal, tdee, days)


# ═══════════════════════════════════════════════════════════════════
# DAILY TRACKING SUMMARY
# ═══════════════════════════════════════════════════════════════════

@app.get("/tracking/{user_id}")
def get_tracking(
    user_id: int,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Parse date or use today
    if date:
        try:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            day = datetime.now(timezone.utc).date()
    else:
        day = datetime.now(timezone.utc).date()

    day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    # Calculate targets
    bmr = calculators.calculate_bmr(user.weight_kg, user.height_cm, user.age, user.sex)
    tdee = calculators.calculate_tdee(bmr, user.activity_level)
    cal = calculators.calculate_daily_calorie_target(tdee, user.goal, user.sex)
    targets = calculators.calculate_nutrition_targets(user.weight_kg, user.sex, user.goal, tdee)
    water_target = calculators.calculate_water_intake(user.weight_kg, user.activity_level)

    # Get today's meal logs
    logs = (
        db.query(models.MealLog)
        .filter(models.MealLog.user_id == user_id)
        .filter(models.MealLog.logged_at >= day_start)
        .filter(models.MealLog.logged_at < day_end)
        .all()
    )

    meals = []
    total_cal = 0
    total_protein = 0
    total_fiber = 0
    total_cost = 0

    for log in logs:
        food = db.query(models.Food).filter(models.Food.id == log.food_id).first()
        if food:
            s = log.servings or 1.0
            total_cal += food.calories_per_serving * s
            total_protein += food.protein_g * s
            total_fiber += food.fiber_g * s
            total_cost += food.price_inr_per_serving * s
            meals.append({
                "food_name": food.name,
                "meal_slot": log.meal_slot,
                "calories": round(food.calories_per_serving * s, 1),
                "protein": round(food.protein_g * s, 1),
                "servings": s,
                "logged_at": log.logged_at.isoformat() if log.logged_at else "",
            })

    # Today's water
    water_ml = _today_water(db, user_id, day_start, day_end)

    return {
        "date": day.isoformat(),
        "target_calories": cal["daily_calorie_target"],
        "actual_calories": round(total_cal, 1),
        "target_protein": targets["protein_g"],
        "actual_protein": round(total_protein, 1),
        "target_fiber": targets["fiber_g"],
        "actual_fiber": round(total_fiber, 1),
        "target_water_ml": water_target["liters_per_day"] * 1000,
        "actual_water_ml": water_ml,
        "meals": meals,
        "total_cost": round(total_cost, 1),
    }


def _today_water(db, user_id, start=None, end=None):
    if not start:
        today = datetime.now(timezone.utc).date()
        start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)

    logs = (
        db.query(models.WaterLog)
        .filter(models.WaterLog.user_id == user_id)
        .filter(models.WaterLog.logged_at >= start)
        .filter(models.WaterLog.logged_at < end)
        .all()
    )
    return sum(l.amount_ml for l in logs)


# ═══════════════════════════════════════════════════════════════════
# WEIGHT HISTORY
# ═══════════════════════════════════════════════════════════════════

@app.get("/weight-history/{user_id}")
def get_weight_history(user_id: int, limit: int = 30, db: Session = Depends(get_db)):
    logs = (
        db.query(models.WeightLog)
        .filter(models.WeightLog.user_id == user_id)
        .order_by(models.WeightLog.logged_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"weight_kg": l.weight_kg, "date": l.logged_at.isoformat() if l.logged_at else ""}
        for l in reversed(logs)
    ]


# ═══════════════════════════════════════════════════════════════════
# AI CHAT
# ═══════════════════════════════════════════════════════════════════

@app.post("/chat")
def chat(req: schemas.ChatRequest, db: Session = Depends(get_db)):
    return process_chat(db, req.user_id, req.message)


# ═══════════════════════════════════════════════════════════════════
# SERVE FRONTEND STATIC FILES
# ═══════════════════════════════════════════════════════════════════

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

