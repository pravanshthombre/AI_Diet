import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.app.database import engine
from backend.app.models import (
    Base, User, Food, Allergen,
    user_allergens, food_allergens, user_dislikes,
    UserSex, ActivityLevel, UserGoal, DietType, FoodRegion, MealSlot
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def migrate():
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Ensure new tables exist
        logger.info("Creating new tables...")
        Base.metadata.create_all(bind=engine)

        # 2. Migrate Allergens
        logger.info("Migrating Allergens...")
        # Foods
        foods = session.query(Food).all()
        for food in foods:
            if food.allergens:
                for alg_name in [a.strip().lower() for a in food.allergens.split(",") if a.strip()]:
                    allergen = session.query(Allergen).filter_by(name=alg_name).first()
                    if not allergen:
                        allergen = Allergen(name=alg_name)
                        session.add(allergen)
                        session.flush()

                    if not allergen in food.allergens_rel:
                        food.allergens_rel.append(allergen)

        # Users
        users = session.query(User).all()
        for user in users:
            if user.allergies:
                for alg_name in [a.strip().lower() for a in user.allergies.split(",") if a.strip()]:
                    allergen = session.query(Allergen).filter_by(name=alg_name).first()
                    if not allergen:
                        allergen = Allergen(name=alg_name)
                        session.add(allergen)
                        session.flush()

                    if not allergen in user.allergens:
                        user.allergens.append(allergen)

            # Dislikes
            if user.food_dislikes:
                for food_name in [f.strip().lower() for f in user.food_dislikes.split(",") if f.strip()]:
                    food = session.query(Food).filter(Food.name.ilike(f"%{food_name}%")).first()
                    if food:
                        if not food in user.disliked_foods:
                            user.disliked_foods.append(food)

        # 3. Migrate Enums
        logger.info("Migrating Enums...")
        for user in users:
            # Sex
            if user.sex:
                try:
                    user.sex_enum = UserSex(user.sex.lower())
                except ValueError:
                    pass

            # Activity Level
            if user.activity_level:
                try:
                    user.activity_level_enum = ActivityLevel(user.activity_level.lower())
                except ValueError:
                    pass

            # Goal
            if user.goal:
                try:
                    user.goal_enum = UserGoal(user.goal.lower())
                except ValueError:
                    pass

            # Diet Type
            if user.diet_type:
                try:
                    user.diet_type_enum = DietType(user.diet_type.lower())
                except ValueError:
                    pass

        # Food Enums
        foods = session.query(Food).all()
        for food in foods:
            # Region
            if food.region:
                try:
                    food.region_enum = FoodRegion(food.region.lower())
                except ValueError:
                    pass

            # Diet Type
            if food.diet_type:
                try:
                    food.diet_type_enum = DietType(food.diet_type.lower())
                except ValueError:
                    pass

            # Meal Slot
            if food.meal_slot:
                try:
                    food.meal_slot_enum = MealSlot(food.meal_slot.lower())
                except ValueError:
                    pass

        # 4. Migrate Times
        logger.info("Migrating Times...")
        for user in users:
            for col, new_col in [("wake_time", "wake_time_new"), ("sleep_time", "sleep_time_new"), ("exercise_time", "exercise_time_new")]:
                val = getattr(user, col)
                if val and val != "":
                    try:
                        # Simple HH:MM parser
                        h, m = map(int, val.split(":"))
                        setattr(user, new_col, datetime.strptime(f"{h}:{m}", "%H:%M").time())
                    except Exception as e:
                        logger.warning(f"Could not parse time {val} for user {user.id}: {e}")

        session.commit()
        logger.info("Migration completed successfully!")

    except Exception as e:
        session.rollback()
        logger.error(f"Migration failed: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
