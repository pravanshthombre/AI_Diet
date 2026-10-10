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
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Enum, Time, Table, event, text
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .database import Base


class UserSex(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class ActivityLevel(enum.Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"

class UserGoal(enum.Enum):
    LOSE = "lose"
    MAINTAIN = "maintain"
    GAIN = "gain"

class DietType(enum.Enum):
    VEGETARIAN = "vegetarian"
    NON_VEGETARIAN = "non_vegetarian"
    EGGETARIAN = "eggetarian"
    VEGAN = "vegan"
    JAIN = "jain"

class FoodRegion(enum.Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTHEAST = "northeast"
    CENTRAL = "central"
    PAN_INDIA = "pan_india"

class MealSlot(enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


# Association tables for normalization
user_allergens = Table(
    "user_allergens",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id"), primary_key=True),
)

food_allergens = Table(
    "food_allergens",
    Base.metadata,
    Column("food_id", ForeignKey("foods.id"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id"), primary_key=True),
)

user_dislikes = Table(
    "user_dislikes",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("food_id", ForeignKey("foods.id"), primary_key=True),
)

class Allergen(Base):
    __tablename__ = "allergens"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(Enum(UserSex, native_enum=False), nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_level = Column(Enum(ActivityLevel, native_enum=False), nullable=False)
    goal = Column(Enum(UserGoal, native_enum=False), default=UserGoal.MAINTAIN)
    region = Column(String, default="pan_india")
    state = Column(String, default="")                 # e.g., Maharashtra, Gujarat
    diet_type = Column(Enum(DietType, native_enum=False), default=DietType.VEGETARIAN)
    weekly_budget_inr = Column(Float, nullable=True)
    wake_time = Column(Time, default=datetime.strptime("07:00", "%H:%M").time())
    sleep_time = Column(Time, default=datetime.strptime("23:00", "%H:%M").time())
    exercise_time = Column(Time, nullable=True)
    meals_per_day = Column(Integer, default=4)
    supabase_uid = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    meal_logs = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    water_logs = relationship("WaterLog", back_populates="user", cascade="all, delete-orphan")
    weight_logs = relationship("WeightLog", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    food_preferences = relationship("FoodPreference", back_populates="user", cascade="all, delete-orphan")
    allergens = relationship("Allergen", secondary=user_allergens, backref="users")
    disliked_foods = relationship("Food", secondary=user_dislikes, backref="disliked_by")


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    region = Column(Enum(FoodRegion, native_enum=False), nullable=False, index=True)
    state = Column(String, default="")                   # state-level granularity
    diet_type = Column(Enum(DietType, native_enum=False), nullable=False, index=True)
    is_jain_friendly = Column(Boolean, default=False)
    meal_slot = Column(Enum(MealSlot, native_enum=False), nullable=False)
    calories_per_serving = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    fiber_g = Column(Float, nullable=False)
    iron_mg = Column(Float, nullable=False)
    calcium_mg = Column(Float, default=0)
    price_inr_per_serving = Column(Float, nullable=False)
    prep_method = Column(String, default="")             # steamed, fried, grilled, raw, boiled
    seasonality = Column(String, default="all_year")     # all_year, summer, winter, monsoon
    ingredients = Column(Text, default="")               # comma-separated ingredients list

    allergens_rel = relationship("Allergen", secondary=food_allergens, backref="foods")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=False)
    meal_slot = Column(String, default="lunch")
    servings = Column(Float, default=1.0)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="meal_logs")
    food = relationship("Food")


class WaterLog(Base):
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount_ml = Column(Float, nullable=False)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="water_logs")


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weight_kg = Column(Float, nullable=False)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="weight_logs")

@event.listens_for(WeightLog, "after_insert")
def update_user_weight(mapper, connection, target):
    """Sync User.weight_kg with the latest WeightLog entry."""
    connection.execute(
        text("UPDATE users SET weight_kg = :weight WHERE id = :user_id"),
        {"weight": target.weight_kg, "user_id": target.user_id}
    )


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
