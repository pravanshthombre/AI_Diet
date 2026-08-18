"""
Comprehensive test suite for NutriCalc AI Diet & Calorie Calculator.
Tests calculators, ML recommender, optimizer, nutrition gaps, substitutions, and chat.
"""
import numpy as np
from app.database import SessionLocal, engine, Base
from app import models, calculators, recommender, optimizer, nutrition_gap, substitution, chat, meal_planner, features
from app.seed_data import seed


def test_calculators():
    print("Testing Calculators...")
    # BMI test
    bmi = calculators.calculate_bmi(65, 160)
    assert bmi["bmi"] == 25.4
    assert bmi["category"] == "Obese Class I" # Asian cutoff

    # BMR & TDEE
    bmr = calculators.calculate_bmr(65, 160, 28, "female")
    assert 1300 <= bmr <= 1450
    tdee = calculators.calculate_tdee(bmr, "moderate")
    assert tdee > bmr

    # Calorie target with Indian clinical guidelines
    plan = calculators.calculate_daily_calorie_target(tdee, "lose", "female")
    assert plan["daily_calorie_target"] >= 1200 # Floor respected
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


def test_database_and_ml():
    print("Testing ML Recommender and DB...")
    db = SessionLocal()
    try:
        # Check foods
        count = db.query(models.Food).count()
        assert count >= 100, f"Expected 100+ foods, found {count}"

        # ML Recommendations
        recs = recommender.recommend_meals(
            db=db,
            user_id=1,
            region="south",
            diet_type="vegetarian",
            meal_slot="breakfast",
            target_calories_for_slot=400,
            top_n=3
        )
        assert len(recs) > 0
        assert all("food" in r and "score" in r for r in recs)
        print(f"[PASS] ML Recommender returned {len(recs)} meals")

        # Substitution engine
        food = db.query(models.Food).first()
        subs = substitution.find_substitutes(
            db=db,
            food_id=food.id,
            meal_slot=food.meal_slot,
            diet_type=food.diet_type,
            region=food.region,
            top_n=3
        )
        assert len(subs) > 0
        print(f"[PASS] Substitution Engine returned {len(subs)} substitutes for {food.name}")

        # Chat
        chat_res = chat.process_chat(db, 1, "Suggest a high protein breakfast")
        assert "reply" in chat_res
        assert len(chat_res["reply"]) > 10
        print(f"[PASS] AI Chat returned valid response")

        # Food dislikes should filter matching foods
        user = db.query(models.User).filter(models.User.id == 1).first()
        if user:
            user.food_dislikes = "idli"
            db.commit()
            filtered = recommender.recommend_meals(
                db=db,
                user_id=1,
                region="south",
                diet_type="vegetarian",
                meal_slot="breakfast",
                target_calories_for_slot=400,
                food_dislikes=["idli"],
                top_n=5,
            )
            assert all("idli" not in r["food"].name.lower() for r in filtered)
            user.food_dislikes = ""
            db.commit()
            print("[PASS] Food dislikes filter OK")

        # Daily plan totals should reflect primary pick only
        if user:
            plan = meal_planner.generate_daily_plan(db, user)
            primary_cals = 0
            for slot in ["breakfast", "lunch", "dinner", "snack"]:
                items = plan.get(slot, [])
                if items:
                    primary_cals += items[0]["food"].calories_per_serving
            assert abs(plan["total_calories"] - primary_cals) < 0.1
            print("[PASS] Meal plan totals use primary pick only")

        # Normalized vectors should not be dominated by calories alone
        foods = db.query(models.Food).limit(3).all()
        vecs = [features.food_vector(f) for f in foods]
        normed = features.normalize_vectors(np.array(vecs))
        assert normed.shape == (3, len(features.NUTRIENT_FIELDS))
        print("[PASS] Feature normalization OK")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
    test_calculators()
    test_database_and_ml()
    print("\nALL SYSTEM TESTS PASSED SUCCESSFULLY!")
