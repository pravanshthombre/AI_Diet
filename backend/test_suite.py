"""
Comprehensive test suite for NutriCalc AI Diet & Calorie Calculator.
Tests calculators, ML recommender, optimizer, nutrition gaps, substitutions, and chat.

Run as a script:
    python test_suite.py

Or with pytest:
    pytest test_suite.py -v
"""
import numpy as np

try:
    import pytest
except ImportError:  # pytest is optional — only needed when running `pytest test_suite.py`
    pytest = None

from app.database import SessionLocal
from app import (
    models,
    calculators,
    recommender,
    optimizer,
    nutrition_gap,
    substitution,
    chat,
    meal_planner,
    features,
)
from app.seed_data import seed


# ---------------------------------------------------------------------------
# Fixtures (used when run via pytest)
# ---------------------------------------------------------------------------

if pytest is not None:
    @pytest.fixture(scope="session", autouse=True)
    def _seed_database():
        """Seed the food database once per pytest session."""
        seed()
        yield

    @pytest.fixture
    def db():
        """Yield a database session and ensure it is closed after the test."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.fixture
    def user(db):
        """Return user_id=1, creating a default profile if it doesn't exist."""
        u = db.query(models.User).filter(models.User.id == 1).first()
        if u is None:
            u = models.User(
                id=1,
                name="Test User",
                age=28,
                sex="female",
                height_cm=160,
                weight_kg=65,
                activity_level="moderate",
                goal="maintain",
                region="south",
                diet_type="vegetarian",
                meals_per_day=4,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
        return u


# ---------------------------------------------------------------------------
# Calculators (pure functions, no DB needed)
# ---------------------------------------------------------------------------

def test_calculators():
    print("Testing Calculators...")
    # BMI test
    bmi = calculators.calculate_bmi(65, 160)
    assert bmi["bmi"] == 25.4
    assert bmi["category"] == "Obese Class I"  # Asian cutoff

    # BMR & TDEE
    bmr = calculators.calculate_bmr(65, 160, 28, "female")
    assert 1300 <= bmr <= 1450
    tdee = calculators.calculate_tdee(bmr, "moderate")
    assert tdee > bmr

    # Calorie target with Indian clinical guidelines
    plan = calculators.calculate_daily_calorie_target(tdee, "lose", "female")
    assert plan["daily_calorie_target"] >= 1200  # Floor respected
    assert "protein_g" in plan and "carbs_g" in plan and "fat_g" in plan

    # Water intake
    water = calculators.calculate_water_intake(65, "moderate")
    assert water["liters_per_day"] > 1.5
    assert water["glasses_per_day"] >= 8

    # Meal timing
    timing = calculators.calculate_meal_timing("07:00", "23:00", "08:00", 4)
    assert "breakfast" in timing
    assert "pre_workout" in timing
    print("[PASS] All Calculators OK")


# ---------------------------------------------------------------------------
# ML recommender + database-backed tests
# ---------------------------------------------------------------------------

def test_food_catalog_populated(db):
    """At least 100 foods should be present after seeding."""
    count = db.query(models.Food).count()
    assert count >= 100, f"Expected 100+ foods, found {count}"


def test_ml_recommender(db, user):
    """The recommender should return scored meals."""
    recs = recommender.recommend_meals(
        db=db,
        user_id=user.id,
        region="south",
        diet_type="vegetarian",
        meal_slot="breakfast",
        target_calories_for_slot=400,
        top_n=3,
    )
    assert len(recs) > 0
    assert all("food" in r and "score" in r for r in recs)
    print(f"[PASS] ML Recommender returned {len(recs)} meals")


def test_substitution_engine(db, user):
    """The substitution engine should return alternatives."""
    food = db.query(models.Food).first()
    assert food is not None
    subs = substitution.find_substitutes(
        db=db,
        user_id=user.id,
        food_id=food.id,
        meal_slot=food.meal_slot,
        diet_type=food.diet_type,
        region=food.region,
        top_n=3,
    )
    assert len(subs) > 0
    print(f"[PASS] Substitution Engine returned {len(subs)} substitutes for {food.name}")


def test_ai_chat(db, user):
    """Chat should return a substantive reply."""
    chat_res = chat.process_chat(db, user.id, "Suggest a high protein breakfast")
    assert "reply" in chat_res
    assert len(chat_res["reply"]) > 10
    print("[PASS] AI Chat returned valid response")


def test_food_dislikes_filter(db, user):
    """Disliked foods must be filtered from recommendations."""
    original_dislikes = user.food_dislikes or ""
    try:
        user.food_dislikes = "idli"
        db.commit()

        filtered = recommender.recommend_meals(
            db=db,
            user_id=user.id,
            region="south",
            diet_type="vegetarian",
            meal_slot="breakfast",
            target_calories_for_slot=400,
            food_dislikes=["idli"],
            top_n=5,
        )
        assert all("idli" not in r["food"].name.lower() for r in filtered)
        print("[PASS] Food dislikes filter OK")
    finally:
        # Always restore, even if assertions above fail.
        user.food_dislikes = original_dislikes
        db.commit()


def test_meal_plan_totals_use_primary_pick(db, user):
    """Daily plan totals should sum only the primary pick from each slot."""
    plan = meal_planner.generate_daily_plan(db, user)
    primary_cals = 0.0
    for slot in ["breakfast", "lunch", "dinner", "snack"]:
        items = plan.get(slot, [])
        if items:
            primary_cals += items[0]["food"].calories_per_serving
    assert abs(plan["total_calories"] - primary_cals) < 0.1
    print("[PASS] Meal plan totals use primary pick only")


def test_feature_normalization(db):
    """Normalized food vectors should have the expected shape."""
    foods = db.query(models.Food).limit(3).all()
    assert len(foods) == 3
    vecs = [features.food_vector(f) for f in foods]
    normed = features.normalize_vectors(np.array(vecs))
    assert normed.shape == (3, len(features.NUTRIENT_FIELDS))
    print("[PASS] Feature normalization OK")


# ---------------------------------------------------------------------------
# Script entrypoint (preserves `python test_suite.py`)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    seed()
    test_calculators()

    db = SessionLocal()
    try:
        # Ensure user_id=1 exists for the script-mode run.
        u = db.query(models.User).filter(models.User.id == 1).first()
        if u is None:
            u = models.User(
                id=1,
                name="Test User",
                age=28,
                sex="female",
                height_cm=160,
                weight_kg=65,
                activity_level="moderate",
                goal="maintain",
                region="south",
                diet_type="vegetarian",
                meals_per_day=4,
            )
            db.add(u)
            db.commit()

        test_food_catalog_populated(db)
        test_ml_recommender(db, u)
        test_substitution_engine(db, u)
        test_ai_chat(db, u)
        test_food_dislikes_filter(db, u)
        test_meal_plan_totals_use_primary_pick(db, u)
        test_feature_normalization(db)
    finally:
        db.close()

    print("\nALL SYSTEM TESTS PASSED SUCCESSFULLY!")
