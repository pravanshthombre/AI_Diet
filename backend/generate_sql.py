from app.seed_data import FOODS

sql_lines = []
sql_lines.append("-- NutriCalc Supabase Schema & Initial Data\n")

sql_lines.append("""
-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    age INTEGER NOT NULL,
    sex VARCHAR NOT NULL,
    height_cm FLOAT NOT NULL,
    weight_kg FLOAT NOT NULL,
    activity_level VARCHAR NOT NULL,
    goal VARCHAR DEFAULT 'maintain',
    region VARCHAR DEFAULT 'pan_india',
    state VARCHAR DEFAULT '',
    diet_type VARCHAR DEFAULT 'vegetarian',
    weekly_budget_inr FLOAT,
    allergies VARCHAR DEFAULT '',
    food_dislikes VARCHAR DEFAULT '',
    wake_time VARCHAR DEFAULT '07:00',
    sleep_time VARCHAR DEFAULT '23:00',
    exercise_time VARCHAR DEFAULT '',
    meals_per_day INTEGER DEFAULT 4,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Foods Table
CREATE TABLE IF NOT EXISTS foods (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    region VARCHAR NOT NULL,
    state VARCHAR DEFAULT '',
    diet_type VARCHAR NOT NULL,
    is_jain_friendly BOOLEAN DEFAULT FALSE,
    meal_slot VARCHAR NOT NULL,
    calories_per_serving FLOAT NOT NULL,
    protein_g FLOAT NOT NULL,
    carbs_g FLOAT NOT NULL,
    fat_g FLOAT NOT NULL,
    fiber_g FLOAT NOT NULL,
    iron_mg FLOAT NOT NULL,
    calcium_mg FLOAT DEFAULT 0,
    price_inr_per_serving FLOAT NOT NULL,
    allergens VARCHAR DEFAULT '',
    prep_method VARCHAR DEFAULT '',
    seasonality VARCHAR DEFAULT 'all_year'
);

-- 3. Meal Logs
CREATE TABLE IF NOT EXISTS meal_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_id INTEGER NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
    meal_slot VARCHAR DEFAULT 'lunch',
    servings FLOAT DEFAULT 1.0,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Water Logs
CREATE TABLE IF NOT EXISTS water_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_ml FLOAT NOT NULL,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Weight Logs
CREATE TABLE IF NOT EXISTS weight_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    weight_kg FLOAT NOT NULL,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_id INTEGER NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
    liked BOOLEAN NOT NULL,
    rating INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS ix_foods_name ON foods(name);
CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);
""")

sql_lines.append("\n-- Seed 114 Indian Regional Foods\n")
for f in FOODS:
    name, region, diet_type, jain, slot, cal, protein, carbs, fat, fiber, iron, calcium, price, allergens, prep, season = f
    safe_name = name.replace("'", "''")
    safe_allergens = allergens.replace("'", "''")
    safe_prep = prep.replace("'", "''")
    safe_season = season.replace("'", "''")
    jain_val = "TRUE" if jain else "FALSE"
    sql_lines.append(
        f"INSERT INTO foods (name, region, state, diet_type, is_jain_friendly, meal_slot, calories_per_serving, protein_g, carbs_g, fat_g, fiber_g, iron_mg, calcium_mg, price_inr_per_serving, allergens, prep_method, seasonality) "
        f"VALUES ('{safe_name}', '{region}', '', '{diet_type}', {jain_val}, '{slot}', {cal}, {protein}, {carbs}, {fat}, {fiber}, {iron}, {calcium}, {price}, '{safe_allergens}', '{safe_prep}', '{safe_season}');"
    )

with open("supabase_schema_and_data.sql", "w", encoding="utf-8") as file:
    file.write("\n".join(sql_lines))

print("Generated supabase_schema_and_data.sql successfully!")
