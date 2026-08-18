import os

base_dir = r"c:\AI_diet\backend"
os.makedirs(base_dir, exist_ok=True)
app_dir = os.path.join(base_dir, "app")
os.makedirs(app_dir, exist_ok=True)

files = {}

files["requirements.txt"] = """fastapi
uvicorn
sqlalchemy
pydantic
scikit-learn
pandas
numpy
python-multipart
"""

files["app/__init__.py"] = ""

files["app/database.py"] = """from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

files["app/models.py"] = """from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_level = Column(String, nullable=False)
    diet_type = Column(String, nullable=False)
    is_jain_friendly = Column(Boolean, default=False)
    budget_per_meal_inr = Column(Float, nullable=True)
    allergies = Column(String, default="")
    goal = Column(String, nullable=False)

class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    region = Column(String, nullable=False)
    diet_type = Column(String, nullable=False)
    is_jain_friendly = Column(Boolean, default=False)
    meal_slot = Column(String, nullable=False)
    calories_per_serving = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    fiber_g = Column(Float, nullable=False)
    iron_mg = Column(Float, nullable=False)
    calcium_mg = Column(Float, default=0)
    price_inr_per_serving = Column(Float, nullable=False)
    allergens = Column(String, default="")
    prep_method = Column(String, default="")
    seasonality = Column(String, default="all_year")

class MealLog(Base):
    __tablename__ = "meal_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_id = Column(Integer, ForeignKey("foods.id"))
    quantity = Column(Float, default=1.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class WaterLog(Base):
    __tablename__ = "water_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount_ml = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class WeightLog(Base):
    __tablename__ = "weight_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    weight_kg = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_id = Column(Integer, ForeignKey("foods.id"))
    rating = Column(Integer, nullable=False)
"""

files["app/schemas.py"] = """from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    diet_type: str
    is_jain_friendly: bool = False
    budget_per_meal_inr: Optional[float] = None
    allergies: Optional[str] = ""
    goal: str

class UserResponse(UserCreate):
    id: int
    class Config:
        from_attributes = True

class FoodBase(BaseModel):
    name: str
    region: str
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

class FoodResponse(FoodBase):
    id: int
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    user_id: int
    message: str

class MealLogCreate(BaseModel):
    food_id: int
    quantity: float

class SubstituteRequest(BaseModel):
    food_id_to_replace: int
    meal_slot: str
"""

files["app/calculators.py"] = """def calculate_bmi(weight_kg: float, height_m: float) -> tuple[float, str]:
    if height_m <= 0: return 0, "Invalid"
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5: return bmi, "Underweight"
    elif 18.5 <= bmi < 23: return bmi, "Normal (Asian)"
    elif 23 <= bmi < 25: return bmi, "Overweight (Asian)"
    else: return bmi, "Obese"

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    return base + 5 if gender.upper() == 'M' else base - 161

def calculate_tdee(bmr: float, activity_level: str) -> float:
    m = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
    return bmr * m.get(activity_level.lower(), 1.2)

def calculate_daily_calories(tdee: float, goal: str, gender: str) -> float:
    adj = {"lose": -0.20, "gain": 0.15}.get(goal.lower(), 0.0)
    cals = tdee * (1 + adj)
    return max(cals, 1500 if gender.upper() == 'M' else 1200)

def calculate_nutrition_targets(calories: float, gender: str) -> dict:
    return {
        "calories": calories,
        "protein_g": (calories * 0.30) / 4,
        "carbs_g": (calories * 0.45) / 4,
        "fat_g": (calories * 0.25) / 9,
        "fiber_g": 30,
        "iron_mg": 18 if gender.upper() == 'F' else 8
    }

def calculate_water_intake(weight_kg: float, is_active: bool, is_hot: bool) -> float:
    ml = 33 * weight_kg + (500 if is_active else 0) + (500 if is_hot else 0)
    return ml / 1000

def calculate_meal_timing(wake_time: int) -> dict:
    return {
        "breakfast": f"{(wake_time + 1) % 24}:00",
        "lunch": f"{(wake_time + 5) % 24}:00",
        "snack": f"{(wake_time + 9) % 24}:00",
        "dinner": f"{(wake_time + 13) % 24}:00"
    }
"""

files["app/recommender.py"] = """import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class DietRecommender:
    def __init__(self, foods_df):
        self.foods_df = foods_df

    def cold_start_recommend(self, target_cals, meal_slot, top_k=5):
        df = self.foods_df[self.foods_df['meal_slot'] == meal_slot].copy()
        df['cal_diff'] = abs(df['calories_per_serving'] - target_cals)
        return df.sort_values('cal_diff').head(top_k)
        
    def warm_recommend(self, user_history_vector, meal_slot, top_k=5):
        df = self.foods_df[self.foods_df['meal_slot'] == meal_slot].copy()
        if len(df) == 0: return []
        features = df[['calories_per_serving', 'protein_g', 'carbs_g', 'fat_g']]
        sims = cosine_similarity([user_history_vector], features)[0]
        df['sim'] = sims
        return df.sort_values('sim', ascending=False).head(top_k)
"""

files["app/optimizer.py"] = """def optimize_budget(foods_list, budget):
    affordable = [f for f in foods_list if f.price_inr_per_serving <= budget]
    affordable.sort(key=lambda x: x.protein_g / max(x.price_inr_per_serving, 1), reverse=True)
    return affordable[:5]
"""

files["app/nutrition_gap.py"] = """def calculate_nutrition_gaps(logs, targets):
    gaps = {}
    for key in targets:
        intake = sum(l.get(key, 0) for l in logs)
        if intake < targets[key] * 0.5: gaps[key] = "High concern"
        elif intake < targets[key] * 0.8: gaps[key] = "Moderate concern"
        else: gaps[key] = "Low concern / Good"
    return gaps
"""

files["app/substitution.py"] = """import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def find_substitute(food_id, all_foods, budget_limit=None):
    df = pd.DataFrame([vars(f) for f in all_foods])
    target = df[df['id'] == food_id]
    if len(target) == 0: return None
    target_vec = target[['protein_g', 'carbs_g', 'fat_g']].values
    
    candidates = df[(df['id'] != food_id) & (df['meal_slot'] == target['meal_slot'].values[0])]
    if budget_limit:
        candidates = candidates[candidates['price_inr_per_serving'] <= budget_limit]
        
    if len(candidates) == 0: return None
    
    cand_vecs = candidates[['protein_g', 'carbs_g', 'fat_g']].values
    sims = cosine_similarity(target_vec, cand_vecs)[0]
    candidates['sim'] = sims
    best_match = candidates.sort_values('sim', ascending=False).iloc[0]
    return best_match.to_dict()
"""

files["app/meal_planner.py"] = """def generate_daily_plan(daily_cals, foods, user_prefs):
    dist = {"breakfast": 0.25, "lunch": 0.35, "snack": 0.10, "dinner": 0.30}
    plan = {}
    for slot, frac in dist.items():
        slot_cals = daily_cals * frac
        slot_foods = [f for f in foods if f.meal_slot == slot and f.diet_type == user_prefs['diet_type']]
        if slot_foods:
            best = min(slot_foods, key=lambda x: abs(x.calories_per_serving - slot_cals))
            plan[slot] = best
    return plan
"""

files["app/chat.py"] = """def process_chat_intent(message, user_context):
    msg = message.lower()
    if "change my lunch" in msg:
        return {"intent": "substitute", "slot": "lunch", "reply": "I'll find a lunch substitute for you."}
    elif "high protein" in msg:
        return {"intent": "recommend", "focus": "protein", "reply": "Here are some high protein options."}
    elif "warning" in msg:
        return {"intent": "explain_gap", "reply": "Let me explain your nutrition gaps."}
    return {"intent": "general", "reply": "I can help you plan your meals, find substitutes, or analyze your nutrition."}
"""

files["app/seed_data.py"] = """import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, SessionLocal
from app.models import Food
import pandas as pd
import numpy as np

def generate_mock_foods(n=120):
    regions = ["north", "south", "east", "west", "northeast", "central", "pan_india"]
    diets = ["vegetarian", "non_vegetarian", "eggetarian", "vegan"]
    slots = ["breakfast", "lunch", "dinner", "snack"]
    
    foods = []
    for i in range(n):
        f = Food(
            name=f"Mock Indian Food {i}",
            region=np.random.choice(regions),
            diet_type=np.random.choice(diets),
            is_jain_friendly=bool(np.random.choice([True, False])),
            meal_slot=np.random.choice(slots),
            calories_per_serving=float(np.random.randint(100, 600)),
            protein_g=float(np.random.randint(2, 30)),
            carbs_g=float(np.random.randint(10, 80)),
            fat_g=float(np.random.randint(1, 25)),
            fiber_g=float(np.random.randint(1, 15)),
            iron_mg=float(np.random.randint(1, 10)),
            calcium_mg=float(np.random.randint(10, 300)),
            price_inr_per_serving=float(np.random.randint(20, 300))
        )
        foods.append(f)
    return foods

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Food).count() == 0:
        foods = generate_mock_foods()
        db.add_all(foods)
        db.commit()
        print("Inserted 120 Indian foods mock data.")
    else:
        print("Foods already seeded.")
    db.close()

if __name__ == "__main__":
    seed()
"""

files["app/main.py"] = """from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, calculators, database
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Diet & Calorie Calculator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:3000", "http://127.0.0.1:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Diet Backend"}

@app.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u: raise HTTPException(status_code=404)
    return u

@app.get("/calculators/bmi")
def calc_bmi(weight_kg: float, height_cm: float):
    bmi, cat = calculators.calculate_bmi(weight_kg, height_cm / 100)
    return {"bmi": bmi, "category": cat}

@app.get("/calculators/bmr-tdee")
def calc_bmr_tdee(weight_kg: float, height_cm: float, age: int, gender: str, activity: str):
    bmr = calculators.calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculators.calculate_tdee(bmr, activity)
    return {"bmr": bmr, "tdee": tdee}

@app.get("/foods", response_model=List[schemas.FoodResponse])
def get_foods(db: Session = Depends(get_db)):
    return db.query(models.Food).all()
"""

for path, content in files.items():
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Backend files bootstrap completed successfully.")
