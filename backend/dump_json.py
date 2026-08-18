import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app.seed_data import FOODS
except ImportError:
    print("Could not import FOODS from app.seed_data")
    sys.exit(1)

keys = [
    "name", "region", "diet_type", "jain", "slot", "cal", "protein", "carbs", "fat",
    "fiber", "iron", "calcium", "price", "allergens", "prep", "season", "ingredients"
]

food_dicts = []
for row in FOODS:
    food_dict = dict(zip(keys, row))
    food_dicts.append(food_dict)

with open('foods.json', 'w', encoding='utf-8') as f:
    json.dump(food_dicts, f, indent=4)

print(f"Dumped {len(food_dicts)} foods to foods.json")
