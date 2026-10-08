"""
Seed the food database from foods.json.
Nutrition data based on IFCT approximations and generated regional variations.

Production-safe: Only seeds when the table is completely empty.
Never deletes existing data (safe for Supabase persistent databases).

Run:  python -m app.seed_data
"""
import json
import os
import logging
from .database import engine, SessionLocal, Base
from .models import Food

logger = logging.getLogger("nutricalc.seed")

def seed():
    """Create tables and populate the food database (idempotent — skips if data exists)."""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'foods.json')
    
    if not os.path.exists(json_path):
        logger.error("Could not find %s", json_path)
        return

    try:
        # Attempt to add the column if it doesn't exist (SQLite / Postgres safe)
        with engine.begin() as conn:
            from sqlalchemy import text
            try:
                conn.execute(text("ALTER TABLE foods ADD COLUMN ingredients TEXT DEFAULT ''"))
            except Exception:
                pass  # Column likely already exists
        
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            existing_count = db.query(Food).count()
            if existing_count > 0:
                logger.info("Database already has %d foods — skipping seed (idempotent).", existing_count)
                return

            # Only seed into an empty table
            with open(json_path, 'r', encoding='utf-8') as f:
                foods_data = json.load(f)

            for row in foods_data:
                db.add(Food(
                    name=row.get('name'),
                    region=row.get('region'),
                    diet_type=row.get('diet_type'),
                    is_jain_friendly=row.get('jain', False),
                    meal_slot=row.get('slot'),
                    calories_per_serving=row.get('cal', 0),
                    protein_g=row.get('protein', 0),
                    carbs_g=row.get('carbs', 0),
                    fat_g=row.get('fat', 0),
                    fiber_g=row.get('fiber', 0),
                    iron_mg=row.get('iron', 0),
                    calcium_mg=row.get('calcium', 0),
                    price_inr_per_serving=row.get('price', 0),
                    allergens=row.get('allergens', ''),
                    prep_method=row.get('prep', ''),
                    seasonality=row.get('season', 'all_year'),
                    ingredients=row.get('ingredients', ''),
                ))
            db.commit()
            logger.info("Seeded %d regional Indian foods into the database.", len(foods_data))
        finally:
            db.close()
    except Exception as e:
        logger.warning("Could not seed database: %s", e)

if __name__ == "__main__":
    seed()

