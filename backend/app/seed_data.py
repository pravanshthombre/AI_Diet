"""
Seed the food database with 110+ real Indian foods across 6 regions.
Nutrition data based on IFCT (Indian Food Composition Tables) approximations.

Run:  python -m app.seed_data
"""
from .database import engine, SessionLocal, Base
from .models import Food


# Format: (name, region, diet_type, jain, slot, cal, protein, carbs, fat, fiber, iron, calcium, price, allergens, prep, season)
FOODS = [
    # ═══════════════════════════════════════════════════
    # NORTH INDIAN
    # ═══════════════════════════════════════════════════

    # Breakfast
    ("Aloo Paratha (2 pcs)",       "north", "vegetarian",     False, "breakfast", 380, 10, 52, 14, 4,  2.5, 60,  40, "gluten",         "fried",    "all_year"),
    ("Poha with Peanuts",          "north", "vegan",          True,  "breakfast", 270, 8,  42, 8,  3,  3.2, 30,  25, "",               "sauteed",  "all_year"),
    ("Chole Bhature (1 plate)",    "north", "vegetarian",     False, "breakfast", 520, 14, 60, 24, 6,  3.8, 80,  60, "gluten",         "fried",    "all_year"),
    ("Stuffed Mooli Paratha",      "north", "vegetarian",     False, "breakfast", 340, 8,  48, 12, 5,  2.0, 50,  35, "gluten",         "fried",    "winter"),
    ("Besan Chilla (2 pcs)",       "north", "vegan",          True,  "breakfast", 240, 12, 28, 8,  5,  2.8, 40,  20, "",               "pan_fried","all_year"),

    # Lunch
    ("Rajma Chawal (1 plate)",     "north", "vegan",          False, "lunch",     480, 16, 72, 10, 12, 4.5, 90,  45, "",               "boiled",   "all_year"),
    ("Dal Makhani + 2 Roti",       "north", "vegetarian",     False, "lunch",     520, 18, 62, 20, 8,  4.2, 120, 55, "dairy,gluten",   "slow_cook","all_year"),
    ("Paneer Butter Masala + Rice","north", "vegetarian",     True,  "lunch",     580, 22, 58, 28, 4,  2.5, 240, 70, "dairy",          "sauteed",  "all_year"),
    ("Chicken Curry + 2 Roti",     "north", "non_vegetarian", False, "lunch",     550, 35, 48, 22, 4,  3.0, 40,  80, "gluten",         "sauteed",  "all_year"),
    ("Kadhi Chawal",               "north", "vegetarian",     False, "lunch",     420, 12, 60, 14, 3,  2.0, 140, 35, "dairy",          "boiled",   "all_year"),

    # Dinner
    ("Roti + Aloo Gobi + Dal",     "north", "vegan",          False, "dinner",    440, 14, 62, 12, 8,  3.5, 70,  40, "gluten",         "sauteed",  "all_year"),
    ("Butter Chicken + Naan",      "north", "non_vegetarian", False, "dinner",    620, 32, 50, 30, 3,  2.8, 60,  90, "dairy,gluten",   "grilled",  "all_year"),
    ("Palak Paneer + 2 Roti",      "north", "vegetarian",     True,  "dinner",    460, 20, 44, 22, 6,  5.0, 280, 55, "dairy,gluten",   "sauteed",  "all_year"),
    ("Egg Curry + Rice",           "north", "eggetarian",     False, "dinner",    480, 20, 56, 18, 3,  3.0, 60,  50, "eggs",           "boiled",   "all_year"),

    # Snacks
    ("Roasted Chana (50g)",        "north", "vegan",          True,  "snack",     180, 10, 28, 3,  8,  3.0, 50,  15, "",               "roasted",  "all_year"),
    ("Lassi (Sweet, 300ml)",       "north", "vegetarian",     True,  "snack",     180, 6,  28, 5,  0,  0.2, 200, 20, "dairy",          "blended",  "summer"),
    ("Samosa (2 pcs)",             "north", "vegetarian",     False, "snack",     320, 6,  36, 16, 3,  1.5, 20,  25, "gluten",         "fried",    "all_year"),

    # ═══════════════════════════════════════════════════
    # SOUTH INDIAN
    # ═══════════════════════════════════════════════════

    # Breakfast
    ("Idli (4 pcs) + Sambar",      "south", "vegan",          True,  "breakfast", 280, 10, 48, 4,  4,  2.8, 40,  25, "",               "steamed",  "all_year"),
    ("Masala Dosa + Chutney",      "south", "vegan",          True,  "breakfast", 350, 8,  52, 12, 3,  2.5, 30,  30, "",               "pan_fried","all_year"),
    ("Upma (Rava)",                "south", "vegan",          True,  "breakfast", 260, 7,  40, 8,  3,  1.8, 20,  20, "gluten",         "sauteed",  "all_year"),
    ("Medu Vada (3 pcs) + Sambar", "south", "vegan",          True,  "breakfast", 380, 14, 42, 16, 6,  3.5, 50,  30, "",               "fried",    "all_year"),
    ("Pesarattu (Moong Dosa, 2)",  "south", "vegan",          True,  "breakfast", 280, 14, 36, 6,  6,  3.2, 40,  25, "",               "pan_fried","all_year"),
    ("Pongal (Ven Pongal)",        "south", "vegetarian",     True,  "breakfast", 320, 8,  48, 10, 2,  1.5, 30,  25, "dairy",          "boiled",   "all_year"),

    # Lunch
    ("Sambar Rice + Papad",        "south", "vegan",          True,  "lunch",     420, 12, 68, 8,  8,  3.8, 50,  30, "",               "boiled",   "all_year"),
    ("Curd Rice",                  "south", "vegetarian",     True,  "lunch",     320, 10, 52, 8,  2,  1.0, 180, 25, "dairy",          "raw",      "summer"),
    ("Fish Curry + Rice (Kerala)", "south", "non_vegetarian", False, "lunch",     520, 30, 54, 18, 3,  2.5, 60,  75, "fish",           "sauteed",  "all_year"),
    ("Bisi Bele Bath",             "south", "vegetarian",     True,  "lunch",     450, 14, 64, 12, 8,  3.5, 60,  35, "nuts",           "boiled",   "all_year"),
    ("Rasam Rice + Vegetable",     "south", "vegan",          True,  "lunch",     380, 10, 62, 6,  5,  2.8, 40,  25, "",               "boiled",   "all_year"),

    # Dinner
    ("Appam + Stew (Veg)",         "south", "vegetarian",     True,  "dinner",    380, 8,  52, 14, 4,  1.5, 30,  30, "dairy",          "steamed",  "all_year"),
    ("Meen Pollichathu (Fish)",    "south", "non_vegetarian", False, "dinner",    420, 28, 30, 20, 3,  2.0, 50,  85, "fish",           "baked",    "all_year"),
    ("Lemon Rice + Raita",         "south", "vegetarian",     True,  "dinner",    380, 8,  58, 10, 3,  1.5, 80,  25, "dairy,nuts",     "sauteed",  "all_year"),
    ("Ragi Mudde + Sambar",        "south", "vegan",          True,  "dinner",    360, 10, 60, 4,  8,  4.5, 340, 20, "",               "boiled",   "all_year"),

    # Snacks
    ("Banana Chips (50g)",         "south", "vegan",          True,  "snack",     260, 2,  30, 16, 2,  0.5, 10,  15, "",               "fried",    "all_year"),
    ("Filter Coffee + Biscuit",    "south", "vegetarian",     True,  "snack",     120, 3,  18, 4,  0,  0.3, 80,  15, "dairy,gluten",   "brewed",   "all_year"),
    ("Murukku (50g)",              "south", "vegan",          True,  "snack",     240, 4,  32, 12, 2,  1.0, 15,  10, "",               "fried",    "all_year"),

    # ═══════════════════════════════════════════════════
    # WEST INDIAN (Maharashtra, Gujarat, Rajasthan, Goa)
    # ═══════════════════════════════════════════════════

    # Breakfast
    ("Misal Pav",                  "west",  "vegan",          False, "breakfast", 400, 14, 52, 14, 8,  4.0, 60,  35, "gluten",         "sauteed",  "all_year"),
    ("Thepla (3 pcs) + Curd",     "west",  "vegetarian",     True,  "breakfast", 340, 10, 44, 14, 4,  2.5, 80,  25, "dairy,gluten",   "pan_fried","all_year"),
    ("Sabudana Khichdi",           "west",  "vegetarian",     True,  "breakfast", 320, 6,  52, 10, 2,  1.0, 30,  30, "nuts",           "sauteed",  "all_year"),
    ("Dhokla (4 pcs)",             "west",  "vegan",          True,  "breakfast", 220, 8,  36, 4,  3,  2.0, 20,  15, "",               "steamed",  "all_year"),
    ("Khandvi (6 pcs)",            "west",  "vegetarian",     True,  "breakfast", 200, 8,  28, 6,  2,  1.5, 30,  20, "",               "steamed",  "all_year"),

    # Lunch
    ("Pav Bhaji (1 plate)",        "west",  "vegetarian",     False, "lunch",     520, 12, 60, 24, 6,  3.0, 60,  45, "dairy,gluten",   "sauteed",  "all_year"),
    ("Undhiyu + Rotla",            "west",  "vegetarian",     True,  "lunch",     480, 14, 56, 20, 10, 4.5, 80,  40, "gluten",         "slow_cook","winter"),
    ("Puran Poli + Amti",          "west",  "vegetarian",     True,  "lunch",     440, 10, 68, 12, 6,  3.0, 50,  30, "gluten",         "pan_fried","all_year"),
    ("Fish Thali (Goan)",          "west",  "non_vegetarian", False, "lunch",     580, 32, 54, 22, 5,  3.5, 80,  90, "fish",           "sauteed",  "all_year"),
    ("Gujarati Dal + Rice + Roti", "west",  "vegetarian",     True,  "lunch",     460, 14, 66, 12, 6,  3.2, 60,  35, "dairy,gluten",   "boiled",   "all_year"),

    # Dinner
    ("Bhakri + Zunka",             "west",  "vegan",          True,  "dinner",    380, 12, 54, 10, 8,  3.5, 40,  20, "",               "roasted",  "all_year"),
    ("Varan Bhaat + Toop",         "west",  "vegetarian",     True,  "dinner",    420, 12, 60, 14, 5,  2.5, 40,  30, "dairy",          "boiled",   "all_year"),
    ("Chicken Xacuti (Goan)",      "west",  "non_vegetarian", False, "dinner",    480, 28, 32, 26, 4,  3.0, 50,  85, "nuts",           "sauteed",  "all_year"),

    # Snacks
    ("Fafda + Jalebi",             "west",  "vegetarian",     True,  "snack",     380, 6,  52, 16, 2,  1.0, 20,  30, "gluten,dairy",   "fried",    "all_year"),
    ("Dabeli",                     "west",  "vegan",          False, "snack",     280, 6,  40, 10, 3,  2.0, 30,  25, "gluten,nuts",    "grilled",  "all_year"),
    ("Makhana Roasted (50g)",      "west",  "vegan",          True,  "snack",     180, 5,  28, 4,  3,  1.8, 40,  15, "",               "roasted",  "all_year"),

    # ═══════════════════════════════════════════════════
    # EAST INDIAN (Bengal, Odisha, Bihar, Jharkhand)
    # ═══════════════════════════════════════════════════

    # Breakfast
    ("Luchi + Aloor Dom",          "east",  "vegetarian",     False, "breakfast", 420, 8,  52, 20, 3,  2.0, 30,  35, "gluten",         "fried",    "all_year"),
    ("Chirer Polao (Flattened Rice)","east","vegetarian",     True,  "breakfast", 300, 6,  48, 8,  3,  2.5, 30,  20, "nuts",           "sauteed",  "all_year"),
    ("Sattu Paratha (2 pcs)",      "east",  "vegan",          True,  "breakfast", 360, 14, 48, 10, 6,  3.8, 50,  25, "gluten",         "pan_fried","all_year"),

    # Lunch
    ("Maachher Jhol + Rice",       "east",  "non_vegetarian", False, "lunch",     480, 26, 58, 14, 3,  2.5, 60,  60, "fish",           "sauteed",  "all_year"),
    ("Dalma + Rice (Odia)",        "east",  "vegan",          True,  "lunch",     420, 14, 64, 8,  10, 4.0, 60,  30, "",               "boiled",   "all_year"),
    ("Shukto + Rice + Dal",        "east",  "vegetarian",     True,  "lunch",     440, 12, 62, 12, 8,  3.5, 80,  35, "dairy",          "sauteed",  "all_year"),
    ("Litti Chokha (3 pcs)",       "east",  "vegan",          True,  "lunch",     480, 16, 60, 16, 8,  4.2, 50,  30, "gluten",         "baked",    "all_year"),

    # Dinner
    ("Mishti Doi + Light Rice",    "east",  "vegetarian",     True,  "dinner",    380, 8,  58, 10, 2,  1.0, 150, 30, "dairy",          "raw",      "all_year"),
    ("Egg Bhurji + 2 Paratha",     "east",  "eggetarian",     False, "dinner",    480, 20, 44, 24, 3,  3.0, 60,  45, "eggs,gluten",    "sauteed",  "all_year"),
    ("Begun Bhaja + Dal + Rice",   "east",  "vegan",          True,  "dinner",    440, 12, 62, 14, 6,  3.0, 40,  30, "",               "fried",    "all_year"),

    # Snacks
    ("Jhalmuri",                   "east",  "vegan",          True,  "snack",     200, 5,  32, 6,  3,  2.0, 20,  15, "",               "raw",      "all_year"),
    ("Singara (Samosa, 2 pcs)",    "east",  "vegetarian",     False, "snack",     300, 6,  34, 14, 3,  1.5, 20,  20, "gluten",         "fried",    "all_year"),

    # ═══════════════════════════════════════════════════
    # NORTHEAST INDIAN
    # ═══════════════════════════════════════════════════

    # Breakfast
    ("Pitha (Rice Cake, 3 pcs)",   "northeast", "vegan",      True,  "breakfast", 300, 6,  52, 6,  3,  1.5, 20,  20, "",               "steamed",  "all_year"),
    ("Jolpan (Assamese Flattened Rice)","northeast","vegan",   True,  "breakfast", 280, 6,  46, 8,  3,  2.0, 30,  15, "",               "raw",      "all_year"),

    # Lunch
    ("Bamboo Shoot Curry + Rice",  "northeast", "vegan",      True,  "lunch",     380, 10, 56, 10, 6,  2.5, 30,  30, "",               "boiled",   "all_year"),
    ("Smoked Pork + Rice (Naga)",  "northeast", "non_vegetarian",False,"lunch",    520, 30, 50, 22, 3,  3.0, 20,  70, "",               "smoked",   "all_year"),
    ("Dal + Rice + Ou Tenga",      "northeast", "vegan",      True,  "lunch",     400, 14, 60, 8,  6,  3.5, 40,  25, "",               "boiled",   "all_year"),

    # Dinner
    ("Khaar + Rice (Assamese)",    "northeast", "vegetarian",  True,  "dinner",    360, 8,  56, 8,  4,  2.0, 30,  20, "",               "boiled",   "all_year"),
    ("Jadoh (Meghalaya Rice)",     "northeast", "non_vegetarian",False,"dinner",   480, 22, 52, 16, 3,  2.5, 30,  50, "",               "boiled",   "all_year"),

    # Snacks
    ("Vegetable Momos (8 pcs)",    "northeast", "vegetarian",  True,  "snack",     320, 10, 50, 8,  4,  1.6, 30,  50, "gluten",         "steamed",  "all_year"),
    ("Chicken Momos (8 pcs)",      "northeast", "non_vegetarian",False,"snack",    380, 18, 46, 12, 3,  2.0, 30,  60, "gluten",         "steamed",  "all_year"),

    # ═══════════════════════════════════════════════════
    # CENTRAL INDIAN (MP, Chhattisgarh)
    # ═══════════════════════════════════════════════════

    # Breakfast
    ("Poha Jalebi",                "central", "vegetarian",   True,  "breakfast", 380, 8,  56, 14, 3,  2.0, 30,  30, "gluten",         "fried",    "all_year"),
    ("Bafla (Baked Wheat Balls)",  "central", "vegetarian",   True,  "breakfast", 400, 10, 58, 14, 4,  2.5, 40,  25, "gluten,dairy",   "baked",    "all_year"),

    # Lunch
    ("Dal Bafla + Churma",         "central", "vegetarian",   True,  "lunch",     540, 16, 72, 18, 6,  3.5, 50,  40, "gluten,dairy",   "baked",    "all_year"),
    ("Chhattisgarhi Chila + Chutney","central","vegan",       True,  "lunch",     320, 10, 42, 10, 5,  3.0, 40,  20, "",               "pan_fried","all_year"),
    ("Bhutte ka Kees + Roti",      "central", "vegetarian",   True,  "lunch",     380, 10, 52, 14, 5,  2.5, 40,  30, "dairy,gluten",   "sauteed",  "monsoon"),

    # Dinner
    ("Roti + Sev Tamatar + Dal",   "central", "vegan",        True,  "dinner",    420, 14, 58, 12, 6,  3.5, 40,  30, "gluten",         "sauteed",  "all_year"),
    ("Malpua + Light Dal Rice",    "central", "vegetarian",   True,  "dinner",    460, 10, 66, 16, 4,  2.0, 50,  35, "dairy,gluten",   "fried",    "all_year"),

    # Snacks
    ("Bhutte ka Kees (snack)",     "central", "vegetarian",   True,  "snack",     200, 5,  28, 8,  3,  1.5, 20,  15, "dairy",          "sauteed",  "monsoon"),
    ("Chana Jor Garam",            "central", "vegan",        True,  "snack",     180, 8,  24, 5,  5,  2.5, 30,  10, "",               "roasted",  "all_year"),

    # ═══════════════════════════════════════════════════
    # PAN-INDIA (common staples)
    # ═══════════════════════════════════════════════════

    # Breakfast
    ("Vegetable Oats Porridge",    "pan_india", "vegan",      True,  "breakfast", 220, 8,  36, 6,  5,  2.5, 30,  15, "gluten",         "boiled",   "all_year"),
    ("Moong Dal Chilla (2 pcs)",   "pan_india", "vegan",      True,  "breakfast", 260, 14, 32, 6,  6,  2.8, 30,  25, "",               "pan_fried","all_year"),
    ("Boiled Eggs (2) + Toast",    "pan_india", "eggetarian",  False, "breakfast", 280, 16, 24, 12, 2,  2.0, 50,  30, "eggs,gluten",    "boiled",   "all_year"),
    ("Sprouts Salad",              "pan_india", "vegan",      True,  "breakfast", 180, 12, 24, 3,  8,  3.5, 40,  10, "",               "raw",      "all_year"),
    ("Paneer Paratha (2)",         "pan_india", "vegetarian",  True,  "breakfast", 420, 16, 44, 20, 3,  2.0, 200, 45, "dairy,gluten",   "pan_fried","all_year"),
    ("Banana Smoothie (300ml)",    "pan_india", "vegetarian",  True,  "breakfast", 240, 8,  40, 6,  3,  0.5, 160, 20, "dairy",          "blended",  "all_year"),

    # Lunch
    ("Grilled Paneer Salad",       "pan_india", "vegetarian",  True,  "lunch",     360, 24, 20, 20, 6,  2.5, 280, 70, "dairy",          "grilled",  "all_year"),
    ("Sprout & Vegetable Salad",   "pan_india", "vegan",       True,  "lunch",     240, 12, 32, 5,  9,  3.2, 40,  30, "",               "raw",      "all_year"),
    ("Mixed Vegetable Pulao",      "pan_india", "vegetarian",  True,  "lunch",     380, 8,  58, 10, 4,  2.0, 30,  30, "",               "boiled",   "all_year"),
    ("Tofu Stir Fry + Rice",       "pan_india", "vegan",       True,  "lunch",     400, 20, 48, 14, 5,  3.5, 200, 40, "soy",            "sauteed",  "all_year"),
    ("Chicken Biryani (1 plate)",  "pan_india", "non_vegetarian",False,"lunch",    550, 28, 60, 20, 3,  2.5, 40,  80, "",               "sauteed",  "all_year"),
    ("Veg Biryani (1 plate)",      "pan_india", "vegetarian",  True,  "lunch",     440, 10, 64, 14, 5,  2.5, 40,  45, "",               "sauteed",  "all_year"),
    ("Khichdi + Kadhi",            "pan_india", "vegetarian",  True,  "lunch",     400, 14, 56, 10, 6,  3.0, 120, 30, "dairy",          "boiled",   "all_year"),
    ("Chapati + Mixed Veg + Dal",  "pan_india", "vegan",       True,  "lunch",     420, 14, 58, 10, 8,  3.5, 60,  35, "gluten",         "sauteed",  "all_year"),

    # Dinner
    ("Mixed Millet Khichdi",       "pan_india", "vegan",       True,  "dinner",    380, 12, 65, 8,  9,  3.4, 50,  30, "",               "boiled",   "all_year"),
    ("Grilled Chicken Breast + Salad","pan_india","non_vegetarian",False,"dinner", 400, 40, 12, 16, 5,  1.8, 30, 110, "",               "grilled",  "all_year"),
    ("Mushroom + Capsicum + Roti", "pan_india", "vegan",       True,  "dinner",    340, 10, 46, 10, 6,  3.0, 20,  30, "gluten",         "sauteed",  "all_year"),
    ("Paneer Tikka (8 pcs)",       "pan_india", "vegetarian",  True,  "dinner",    380, 22, 16, 24, 3,  2.0, 300, 60, "dairy",          "grilled",  "all_year"),
    ("Egg Bhurji + 2 Chapati",     "pan_india", "eggetarian",  False, "dinner",    440, 20, 38, 22, 3,  3.0, 60,  40, "eggs,gluten",    "sauteed",  "all_year"),
    ("Dal Tadka + Rice",           "pan_india", "vegan",       True,  "dinner",    420, 14, 60, 10, 6,  3.5, 40,  30, "",               "boiled",   "all_year"),
    ("Curd Rice (Light)",          "pan_india", "vegetarian",  True,  "dinner",    280, 8,  42, 6,  1,  0.8, 160, 20, "dairy",          "raw",      "summer"),
    ("Vegetable Soup + Bread",     "pan_india", "vegan",       True,  "dinner",    200, 6,  30, 4,  5,  1.5, 30,  15, "gluten",         "boiled",   "all_year"),

    # Snacks
    ("Buttermilk (Chaas, 300ml)",  "pan_india", "vegetarian",  True,  "snack",     80,  3,  6,  4,  0,  0.2, 120, 10, "dairy",          "blended",  "summer"),
    ("Fruit Bowl (Mixed, 200g)",   "pan_india", "vegan",       True,  "snack",     120, 2,  28, 1,  4,  0.5, 30,  10, "",               "raw",      "all_year"),
    ("Peanut Chikki (50g)",        "pan_india", "vegan",       True,  "snack",     210, 7,  22, 11, 3,  1.5, 20,  20, "nuts",           "raw",      "winter"),
    ("Boiled Egg (2) + Fruit",     "pan_india", "eggetarian",  False, "snack",     220, 14, 20, 10, 3,  1.8, 50,  30, "eggs",           "boiled",   "all_year"),
    ("Dry Fruits Mix (30g)",       "pan_india", "vegan",       True,  "snack",     180, 5,  14, 12, 2,  1.2, 40,  25, "nuts",           "raw",      "all_year"),
    ("Masala Chana (100g)",        "pan_india", "vegan",       True,  "snack",     160, 8,  24, 3,  6,  2.8, 50,  10, "",               "boiled",   "all_year"),
    ("Yogurt Parfait",             "pan_india", "vegetarian",  True,  "snack",     200, 8,  28, 6,  2,  0.5, 150, 25, "dairy,nuts",     "raw",      "all_year"),
    ("Protein Shake (Whey+Banana)","pan_india", "vegetarian",  True,  "snack",     250, 25, 28, 4,  2,  1.0, 200, 30, "dairy",          "blended",  "all_year"),
    ("Green Tea + Almonds (10)",   "pan_india", "vegan",       True,  "snack",     100, 4,  6,  7,  2,  0.8, 50,  5,  "nuts",           "brewed",   "all_year"),
    ("Makhana Roasted (50g)",      "pan_india", "vegan",       True,  "snack",     180, 5,  28, 4,  3,  1.8, 40,  12, "",               "roasted",  "all_year"),
    ("Ragi Ladoo (2 pcs)",         "pan_india", "vegetarian",  True,  "snack",     200, 4,  30, 8,  3,  2.0, 80,  15, "dairy",          "raw",      "all_year"),
]


def seed():
    """Create tables and populate the food database."""
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            db.query(Food).delete()
            for row in FOODS:
                (name, region, diet_type, jain, slot, cal, protein, carbs, fat,
                 fiber, iron, calcium, price, allergens, prep, season) = row
                db.add(Food(
                    name=name,
                    region=region,
                    diet_type=diet_type,
                    is_jain_friendly=jain,
                    meal_slot=slot,
                    calories_per_serving=cal,
                    protein_g=protein,
                    carbs_g=carbs,
                    fat_g=fat,
                    fiber_g=fiber,
                    iron_mg=iron,
                    calcium_mg=calcium,
                    price_inr_per_serving=price,
                    allergens=allergens,
                    prep_method=prep,
                    seasonality=season,
                ))
            db.commit()
            print(f"[OK] Seeded {len(FOODS)} Indian foods into the database.")
        finally:
            db.close()
    except Exception as e:
        print(f"[SEED WARNING] Could not seed database: {e}")



if __name__ == "__main__":
    seed()
