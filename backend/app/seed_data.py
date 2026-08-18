"""
Seed the food database from foods.json.
Nutrition data based on IFCT approximations and generated regional variations.

Run:  python -m app.seed_data
"""
import json
import os
from .database import engine, SessionLocal, Base
from .models import Food

def seed():
    """Create tables and populate the food database."""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'foods.json')
    
    if not os.path.exists(json_path):
        print(f"[SEED ERROR] Could not find {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        foods_data = json.load(f)

    try:
        # Attempt to add the column if it doesn't exist (SQLite / Postgres safe)
        with engine.begin() as conn:
            from sqlalchemy import text
            try:
                conn.execute(text("ALTER TABLE foods ADD COLUMN ingredients TEXT DEFAULT ''"))
            except Exception:
                pass # Column likely already exists
        
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            db.query(Food).delete()
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
            print(f"[OK] Seeded {len(foods_data)} regional Indian foods into the database.")
        finally:
            db.close()
    except Exception as e:
        print(f"[SEED WARNING] Could not seed database: {e}")

if __name__ == "__main__":
    seed()
