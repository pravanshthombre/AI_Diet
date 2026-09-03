"""
Database tables (SQLAlchemy ORM models).

Tables:
  users             – profile, preferences, dietary info, budget
  foods             – Indian regional food database with full nutrition
  meal_logs         – meals a user has logged
  water_logs        – daily water intake
  weight_logs       – weight tracking over time
  feedback          – explicit food ratings/likes/dislikes
  food_preferences  – user's preferred/favorite foods for diet plan prioritization
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)              # "male" | "female"
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_level = Column(String, nullable=False)    # sedentary/light/moderate/active/very_active
    goal = Column(String, default="maintain")          # lose/maintain/gain
    region = Column(String, default="pan_india")       # north/south/east/west/northeast/central
    state = Column(String, default="")                 # e.g., Maharashtra, Gujarat
    diet_type = Column(String, default="vegetarian")   # vegetarian/non_vegetarian/eggetarian/vegan/jain
    weekly_budget_inr = Column(Float, nullable=True)
    allergies = Column(String, default="")             # comma-separated
    food_dislikes = Column(String, default="")         # comma-separated
    wake_time = Column(String, default="07:00")
    sleep_time = Column(String, default="23:00")
    exercise_time = Column(String, default="")
    meals_per_day = Column(Integer, default=4)
    supabase_uid = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    meal_logs = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    water_logs = relationship("WaterLog", back_populates="user", cascade="all, delete-orphan")
    weight_logs = relationship("WeightLog", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    food_preferences = relationship("FoodPreference", back_populates="user", cascade="all, delete-orphan")


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    region = Column(String, nullable=False)              # north/south/east/west/northeast/central/pan_india
    state = Column(String, default="")                   # state-level granularity
    diet_type = Column(String, nullable=False)            # vegetarian/non_vegetarian/eggetarian/vegan
    is_jain_friendly = Column(Boolean, default=False)
    meal_slot = Column(String, nullable=False)            # breakfast/lunch/dinner/snack
    calories_per_serving = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    fiber_g = Column(Float, nullable=False)
    iron_mg = Column(Float, nullable=False)
    calcium_mg = Column(Float, default=0)
    price_inr_per_serving = Column(Float, nullable=False)
    allergens = Column(String, default="")               # comma-separated: gluten, dairy, nuts, soy
    prep_method = Column(String, default="")             # steamed, fried, grilled, raw, boiled
    seasonality = Column(String, default="all_year")     # all_year, summer, winter, monsoon
    ingredients = Column(Text, default="")               # comma-separated ingredients list


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    meal_slot = Column(String, default="lunch")
    servings = Column(Float, default=1.0)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="meal_logs")
    food = relationship("Food")


class WaterLog(Base):
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount_ml = Column(Float, nullable=False)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="water_logs")


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weight_kg = Column(Float, nullable=False)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="weight_logs")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    liked = Column(Boolean, nullable=True)       # True=liked, False=disliked, None=neutral
    rating = Column(Integer, nullable=True)      # 1-5 star rating
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="feedback")
    food = relationship("Food")


class FoodPreference(Base):
    """User's preferred/favorite foods — these get prioritized in diet plan generation."""
    __tablename__ = "food_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    meal_slot = Column(String, default="")          # optional: preferred slot for this food
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="food_preferences")
    food = relationship("Food")
