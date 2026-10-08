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
  - Food vision analysis & IFCT calibration
  - ML model training endpoint

Production features:
  - Structured logging with request IDs
  - Rate limiting via SlowAPI
  - Tightened CORS (configurable origins)
  - Lifespan startup/shutdown events

Run:
    pip install -r requirements.txt
    python -m app.seed_data
    uvicorn app.main:app --reload
"""
import os
import uuid
import base64
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from .database import Base, engine, get_db, SessionLocal
from . import models, schemas, calculators
from .auth import get_current_user, get_supabase_uid
from .recommender import recommend_meals, _parse_csv_field
from .meal_planner import generate_daily_plan
from .substitution import find_substitutes
from .nutrition_gap import calculate_nutrition_gaps
from .chat import process_chat
from .vision import analyze_food_image
from .calibration import calibrate_food_nutrition, PREPARATION_MODIFIERS, ADD_ON_MODIFIERS

# ─────────────────────────────────────────────
# Structured Logging Setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nutricalc.api")

# ─────────────────────────────────────────────
# Rate Limiting Setup
# ─────────────────────────────────────────────
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
    _rate_limiting_available = True
    logger.info("Rate limiting enabled (slowapi)")
except ImportError:
    limiter = None
    _rate_limiting_available = False
    logger.warning("slowapi not installed — rate limiting disabled. Install with: pip install slowapi")


# ─────────────────────────────────────────────
# Application Lifespan
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    try:
        # ── Environment diagnostics (helps debug Render deploys) ──
        db_url = os.getenv("DATABASE_URL", "")
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        if db_url:
            # Mask password in log output
            masked = db_url.split("@")[-1] if "@" in db_url else "(configured)"
            logger.info("DATABASE_URL: connected to %s", masked)
        else:
            logger.warning("DATABASE_URL not set — falling back to SQLite (data will NOT persist on Render!)")

        if jwt_secret:
            logger.info("SUPABASE_JWT_SECRET: configured (%d chars)", len(jwt_secret))
        else:
            logger.warning("SUPABASE_JWT_SECRET not set — running in DEVELOPMENT auth mode (no JWT verification)")

        logger.info("Connecting to database and creating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")

        # Auto-seed foods if table is empty
        db = SessionLocal()
        try:
            food_count = db.query(models.Food).count()
            if food_count == 0:
                logger.info("Database is empty. Seeding Indian regional foods...")
                from .seed_data import seed
                seed()
                logger.info("Database seeded successfully.")
            else:
                logger.info("Database connected. Found %d existing food records.", food_count)

            # Auto-train ML model if data exists and model not trained
            from .ml_ranker import ranker
            if not ranker.is_trained:
                trained = ranker.train_model(db)
                if trained:
                    logger.info("ML ranker model auto-trained on startup.")
                else:
                    logger.info("ML ranker using rule-based scoring (not enough training data yet).")
        except Exception as e:
            logger.warning("Startup data check: %s", e)
        finally:
            db.close()
    except Exception as e:
        logger.error("Could not connect to database on startup: %s", e)
        logger.warning("Running in resilient mode. Ensure DATABASE_URL is valid.")

    yield

    # Shutdown
    logger.info("NutriCalc API shutting down.")


app = FastAPI(
    title="NutriCalc API",
    description="AI/ML-powered Diet & Calorie Calculator for Indian regional nutrition",
    version="2.0.0",
    lifespan=lifespan,
)

# Register rate limiter
if _rate_limiting_available:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────

# CORS — configurable origins for production
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True if ALLOWED_ORIGINS != ["*"] else False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Add request ID, log requests, and measure response time."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    start_time = time.time()
    logger.info("[%s] %s %s", request_id, request.method, request.url.path)

    try:
        response = await call_next(request)
    except Exception as e:
        duration = time.time() - start_time
        logger.error("[%s] %s %s → 500 (%.2fs) %s",
                     request_id, request.method, request.url.path, duration, str(e))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    duration = time.time() - start_time
    logger.info("[%s] %s %s → %d (%.2fs)",
                request_id, request.method, request.url.path, response.status_code, duration)
    response.headers["X-Request-ID"] = request_id
    return response


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/api/health")
def api_health():
    from .ml_ranker import ranker
    return {
        "status": "ok",
        "message": "NutriCalc API is running. Visit /docs for interactive API.",
        "ml_model_trained": ranker.is_trained,
    }


# ═══════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════

@app.post("/users", response_model=schemas.UserOut)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db), supabase_uid: str = Depends(get_supabase_uid)):
    try:
        data = user_in.model_dump()
        target_uid = data.pop("supabase_uid", None) or supabase_uid

        existing = db.query(models.User).filter(models.User.supabase_uid == target_uid).first()
        if existing:
            for field, value in data.items():
                if value is not None:
                    setattr(existing, field, value)
            db.commit()
            db.refresh(existing)
            logger.info("Updated existing user: id=%d, uid=%s", existing.id, target_uid)
            return existing

        user = models.User(**data, supabase_uid=target_uid)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created new user: id=%d, uid=%s", user.id, target_uid)
        return user
    except Exception as e:
        logger.error("User creation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/me", response_model=schemas.UserOut)
def get_user_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/users/by-supabase/{supabase_uid}", response_model=schemas.UserOut)
def get_user_by_supabase(supabase_uid: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.supabase_uid == supabase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found for this Supabase account")
    return user


@app.get("/users/by-email/{email}", response_model=schemas.UserOut)
def get_user_by_email(email: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found for this email")
    return user


@app.put("/users/me", response_model=schemas.UserOut)
def update_user_me(updates: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    for field, value in updates.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    logger.info("User %d profile updated", current_user.id)
    return current_user


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

@app.get("/recommend", response_model=List[dict])
def get_recommendations(
    meal_slot: str = Query("lunch", description="breakfast/lunch/dinner/snack"),
    top_n: int = 5,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    bmr = calculators.calculate_bmr(current_user.weight_kg, current_user.height_cm, current_user.age, current_user.sex)
    tdee = calculators.calculate_tdee(bmr, current_user.activity_level)
    cal = calculators.calculate_daily_calorie_target(tdee, current_user.goal, current_user.sex)

    slot_weights = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}
    slot_target = cal["daily_calorie_target"] * slot_weights.get(meal_slot, 0.25)

    allergies = _parse_csv_field(current_user.allergies)
    food_dislikes = _parse_csv_field(current_user.food_dislikes)

    results = recommend_meals(
        db=db, user_id=current_user.id, region=current_user.region,
        diet_type=current_user.diet_type, meal_slot=meal_slot,
        target_calories_for_slot=slot_target,
        weekly_budget_inr=current_user.weekly_budget_inr,
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

@app.get("/diet-plan")
def get_diet_plan(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    plan = generate_daily_plan(db, current_user)

    # Serialize food objects
    for slot in ["breakfast", "lunch", "dinner", "snack"]:
        for item in plan[slot]:
            item["food"] = schemas.FoodOut.model_validate(item["food"])

    return plan


@app.post("/diet-plan/substitute")
def substitute_food(
    req: schemas.SubstituteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    budget_ceiling = None
    if current_user.weekly_budget_inr:
        budget_ceiling = (current_user.weekly_budget_inr / 21) * 1.5

    subs = find_substitutes(
        db=db, user_id=current_user.id, food_id=req.food_id, meal_slot=req.meal_slot,
        diet_type=current_user.diet_type, region=current_user.region,
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
def log_meal(entry: schemas.MealLogCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not db.query(models.Food).filter(models.Food.id == entry.food_id).first():
        raise HTTPException(status_code=404, detail="Food not found")

    log = models.MealLog(
        user_id=current_user.id,
        food_id=entry.food_id,
        meal_slot=entry.meal_slot,
        servings=entry.servings or 1.0,
    )
    db.add(log)
    db.commit()
    logger.info("User %d logged meal: food_id=%d, slot=%s", current_user.id, entry.food_id, entry.meal_slot)
    return {"status": "logged", "id": log.id}


@app.post("/log-water")
def log_water(entry: schemas.WaterLogCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    log = models.WaterLog(user_id=current_user.id, amount_ml=entry.amount_ml)
    db.add(log)
    db.commit()
    return {"status": "logged", "total_today_ml": _today_water(db, current_user.id)}


@app.post("/log-weight")
def log_weight(entry: schemas.WeightLogCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    log = models.WeightLog(user_id=current_user.id, weight_kg=entry.weight_kg)
    db.add(log)
    # Also update user's current weight
    current_user.weight_kg = entry.weight_kg
    db.commit()
    logger.info("User %d logged weight: %.1f kg", current_user.id, entry.weight_kg)
    return {"status": "logged", "weight_kg": entry.weight_kg}


# ═══════════════════════════════════════════════════════════════════
# FEEDBACK
# ═══════════════════════════════════════════════════════════════════

@app.post("/feedback")
def submit_feedback(entry: schemas.FeedbackCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not db.query(models.Food).filter(models.Food.id == entry.food_id).first():
        raise HTTPException(status_code=404, detail="Food not found")

    fb = models.Feedback(
        user_id=current_user.id,
        food_id=entry.food_id,
        liked=entry.liked,
        rating=entry.rating,
    )
    db.add(fb)
    db.commit()
    logger.info("User %d submitted feedback: food_id=%d, liked=%s, rating=%s",
                current_user.id, entry.food_id, entry.liked, entry.rating)
    return {"status": "feedback recorded"}


# ═══════════════════════════════════════════════════════════════════
# FOOD PREFERENCES (Favorite Foods for Diet Plan Prioritization)
# ═══════════════════════════════════════════════════════════════════

@app.get("/food-preferences")
def get_food_preferences(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """List all preferred/favorite foods for the authenticated user."""
    prefs = (
        db.query(models.FoodPreference)
        .filter(models.FoodPreference.user_id == current_user.id)
        .all()
    )
    return [
        {
            "id": p.id,
            "user_id": p.user_id,
            "food_id": p.food_id,
            "meal_slot": p.meal_slot or "",
            "food": schemas.FoodOut.model_validate(p.food),
        }
        for p in prefs
    ]


@app.post("/food-preferences")
def add_food_preference(entry: schemas.FoodPreferenceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Add a food to the authenticated user's preferred/favorite foods list."""
    if not db.query(models.Food).filter(models.Food.id == entry.food_id).first():
        raise HTTPException(status_code=404, detail="Food not found")

    # Check for duplicate
    existing = (
        db.query(models.FoodPreference)
        .filter(
            models.FoodPreference.user_id == current_user.id,
            models.FoodPreference.food_id == entry.food_id,
        )
        .first()
    )
    if existing:
        return {"status": "already_preferred", "id": existing.id}

    pref = models.FoodPreference(
        user_id=current_user.id,
        food_id=entry.food_id,
        meal_slot=entry.meal_slot or "",
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return {"status": "preference_added", "id": pref.id}


@app.delete("/food-preferences/{food_id}")
def remove_food_preference(food_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Remove a food from the authenticated user's preferred/favorite foods list."""
    pref = (
        db.query(models.FoodPreference)
        .filter(
            models.FoodPreference.user_id == current_user.id,
            models.FoodPreference.food_id == food_id,
        )
        .first()
    )
    if not pref:
        raise HTTPException(status_code=404, detail="Food preference not found")

    db.delete(pref)
    db.commit()
    return {"status": "preference_removed"}


# ═══════════════════════════════════════════════════════════════════
# NUTRITION GAPS
# ═══════════════════════════════════════════════════════════════════

@app.get("/nutrition-gaps")
def get_nutrition_gaps(
    days: int = 1,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    bmr = calculators.calculate_bmr(current_user.weight_kg, current_user.height_cm, current_user.age, current_user.sex)
    tdee = calculators.calculate_tdee(bmr, current_user.activity_level)

    return calculate_nutrition_gaps(db, current_user.id, current_user.sex, current_user.weight_kg, current_user.goal, tdee, days)


# ═══════════════════════════════════════════════════════════════════
# DAILY TRACKING SUMMARY
# ═══════════════════════════════════════════════════════════════════

@app.get("/tracking")
def get_tracking(
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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
    bmr = calculators.calculate_bmr(current_user.weight_kg, current_user.height_cm, current_user.age, current_user.sex)
    tdee = calculators.calculate_tdee(bmr, current_user.activity_level)
    cal = calculators.calculate_daily_calorie_target(tdee, current_user.goal, current_user.sex)
    targets = calculators.calculate_nutrition_targets(current_user.weight_kg, current_user.sex, current_user.goal, tdee)
    water_target = calculators.calculate_water_intake(current_user.weight_kg, current_user.activity_level)

    # Get today's meal logs with joined food data to avoid N+1 queries
    logs = (
        db.query(models.MealLog, models.Food)
        .join(models.Food, models.MealLog.food_id == models.Food.id)
        .filter(models.MealLog.user_id == current_user.id)
        .filter(models.MealLog.logged_at >= day_start)
        .filter(models.MealLog.logged_at < day_end)
        .all()
    )

    meals = []
    total_cal = 0
    total_protein = 0
    total_fiber = 0
    total_cost = 0

    for log, food in logs:
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
    water_ml = _today_water(db, current_user.id, day_start, day_end)

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

@app.get("/weight-history")
def get_weight_history(limit: int = 30, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    logs = (
        db.query(models.WeightLog)
        .filter(models.WeightLog.user_id == current_user.id)
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
def chat(req: schemas.ChatRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return process_chat(db, current_user.id, req.message)


# ═══════════════════════════════════════════════════════════════════
# ML MODEL TRAINING
# ═══════════════════════════════════════════════════════════════════

@app.post("/admin/train-model")
def train_ml_model(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Manually trigger ML model retraining with current feedback + meal log data."""
    from .ml_ranker import ranker
    success = ranker.train_model(db)
    if success:
        logger.info("ML model retrained successfully by user %d", current_user.id)
        return {"status": "trained", "message": "ML model trained successfully with current data."}
    return {"status": "skipped", "message": "Not enough training data yet (need ≥10 feedback/log entries)."}


# ═══════════════════════════════════════════════════════════════════
# VISION: FOOD IMAGE ANALYSIS & DYNAMIC IFCT CALIBRATION
# ═══════════════════════════════════════════════════════════════════

@app.post("/vision/analyze-plate")
async def vision_analyze_plate(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Analyze an uploaded food photo and identify Indian dishes with IFCT baselines."""
    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    result = await analyze_food_image(
        db=db,
        image_bytes=image_bytes,
        image_base64=image_b64,
        filename=image.filename,
    )
    return result


@app.post("/vision/calibrate")
def vision_calibrate(
    req: schemas.CalibrateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Calibrate IFCT baseline nutrition for real-world portion and preparation style."""
    food = db.query(models.Food).filter(models.Food.id == req.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found in database")
    return calibrate_food_nutrition(
        food=food,
        portion_grams=req.portion_grams,
        serving_multiplier=req.serving_multiplier,
        prep_style=req.prep_style,
        additions=req.additions or [],
    )


@app.get("/vision/prep-styles")
def vision_prep_styles():
    """Returns all available preparation style modifiers and add-on options."""
    return {
        "prep_styles": {
            k: {"label": v["label"], "desc": v["desc"],
                "fat_multiplier": v["fat_multiplier"],
                "calorie_multiplier": v["calorie_multiplier"]}
            for k, v in PREPARATION_MODIFIERS.items()
        },
        "add_ons": {
            k: {"label": v["label"], "cal": v["cal"], "fat": v["fat"]}
            for k, v in ADD_ON_MODIFIERS.items()
        }
    }


# ═══════════════════════════════════════════════════════════════════
# SERVE FRONTEND STATIC FILES
# ═══════════════════════════════════════════════════════════════════

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
