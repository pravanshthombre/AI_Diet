import json
import random
import os

# Base Maharashtrian dishes
# format: (name_base, diet_type, cal_base, protein_base, carbs_base, fat_base, fiber_base, iron_base, calcium_base, price_base, allergens_base, prep_base)
BASE_DISHES = [
    # Breakfast
    ("Kanda Poha", "vegan", 280, 6, 45, 8, 4, 3.5, 20, 30, "peanuts", "sauteed"),
    ("Batata Poha", "vegan", 310, 5, 52, 9, 4, 3.0, 20, 35, "peanuts", "sauteed"),
    ("Tarri Poha", "vegan", 350, 10, 55, 12, 6, 4.5, 30, 45, "peanuts", "slow_cook"),
    ("Misal Pav", "vegan", 450, 16, 60, 18, 10, 5.0, 40, 60, "gluten,soy", "slow_cook"),
    ("Usal Pav", "vegan", 400, 14, 55, 15, 9, 4.5, 35, 50, "gluten", "boiled"),
    ("Sabudana Khichdi", "vegetarian", 380, 4, 65, 12, 2, 1.5, 10, 40, "peanuts", "sauteed"),
    ("Thalipeeth", "vegetarian", 300, 8, 45, 10, 6, 3.5, 45, 45, "gluten", "pan_fried"),
    ("Upma", "vegetarian", 250, 5, 40, 8, 3, 2.0, 15, 30, "gluten,dairy", "boiled"),
    ("Sanja", "vegetarian", 260, 5, 42, 9, 3, 2.2, 18, 35, "gluten,dairy", "sauteed"),
    
    # Veg Mains
    ("Pithla Bhakri", "vegan", 350, 14, 50, 10, 8, 4.0, 50, 50, "gluten", "boiled"),
    ("Zunka Bhakri", "vegan", 380, 15, 48, 14, 8, 4.2, 55, 55, "gluten", "sauteed"),
    ("Bharli Vangi", "vegan", 250, 6, 20, 18, 6, 3.0, 40, 60, "peanuts", "slow_cook"),
    ("Varan Bhaat", "vegetarian", 320, 10, 55, 8, 5, 3.5, 30, 40, "dairy", "boiled"),
    ("Masale Bhaat", "vegan", 340, 6, 58, 10, 4, 2.8, 25, 45, "nuts", "slow_cook"),
    ("Vangi Bhaat", "vegan", 350, 6, 60, 11, 5, 3.0, 30, 50, "nuts", "slow_cook"),
    ("Matki Chi Usal", "vegan", 220, 14, 30, 6, 8, 5.5, 40, 40, "", "boiled"),
    ("Veg Kolhapuri", "vegetarian", 380, 10, 35, 24, 6, 4.0, 60, 80, "dairy,nuts", "slow_cook"),
    ("Batata Chi Bhaji", "vegan", 200, 4, 30, 8, 3, 1.5, 15, 30, "", "sauteed"),
    ("Katachi Amti", "vegan", 150, 6, 20, 5, 3, 2.0, 20, 30, "", "boiled"),
    
    # Non-Veg Mains
    ("Tambada Rassa", "non_vegetarian", 420, 28, 15, 28, 2, 4.5, 40, 120, "", "slow_cook"),
    ("Pandhra Rassa", "non_vegetarian", 450, 26, 12, 32, 1, 3.0, 50, 130, "dairy,nuts", "slow_cook"),
    ("Malvani Chicken Sukka", "non_vegetarian", 380, 32, 10, 22, 3, 4.0, 30, 110, "nuts", "sauteed"),
    ("Malvani Fish Curry", "non_vegetarian", 320, 24, 12, 20, 2, 2.5, 40, 150, "fish,coconut", "slow_cook"),
    ("Mutton Kheema Pav", "non_vegetarian", 550, 35, 40, 28, 4, 6.0, 50, 160, "gluten", "sauteed"),
    ("Bombil Fry", "non_vegetarian", 300, 20, 15, 18, 1, 2.0, 80, 120, "fish,gluten", "fried"),
    ("Saoji Chicken", "non_vegetarian", 480, 30, 15, 34, 4, 5.0, 40, 140, "nuts", "slow_cook"),
    ("Kolhapuri Mutton Sukka", "non_vegetarian", 450, 36, 8, 30, 2, 6.5, 45, 180, "", "sauteed"),
    
    # Snacks & Sweets
    ("Vada Pav", "vegan", 300, 5, 40, 14, 3, 2.0, 20, 20, "gluten", "fried"),
    ("Kothimbir Vadi", "vegan", 220, 8, 25, 10, 4, 3.5, 40, 35, "gluten", "fried"),
    ("Alu Vadi", "vegan", 240, 6, 30, 12, 5, 4.0, 50, 40, "gluten", "steamed"),
    ("Modak (Ukadiche)", "vegetarian", 180, 3, 30, 6, 2, 1.0, 15, 40, "dairy", "steamed"),
    ("Puran Poli", "vegetarian", 280, 6, 45, 8, 4, 2.5, 20, 30, "gluten,dairy", "pan_fried"),
    ("Shrikhand", "vegetarian", 320, 8, 40, 14, 0, 0.5, 150, 60, "dairy", "raw"),
    ("Bhakarwadi", "vegetarian", 250, 5, 28, 14, 2, 2.0, 20, 40, "gluten", "fried"),
    ("Kanda Bhaji", "vegan", 280, 6, 35, 14, 3, 2.5, 30, 30, "gluten", "fried")
]

STYLES = [
    ("Classic", 1.0, 1.0, 1.0, 1.0, "Authentic traditional preparation"),
    ("Kolhapuri", 1.1, 1.0, 1.2, 1.0, "Spicy Kolhapuri style with red chili and garlic"),
    ("Puneri", 0.9, 0.9, 0.9, 1.0, "Mild Puneri style with a hint of sweetness"),
    ("Malvani", 1.05, 1.0, 1.15, 1.1, "Malvani style rich in coconut and kokum"),
    ("Saoji", 1.2, 1.1, 1.3, 1.2, "Extremely spicy Vidarbha Saoji preparation"),
    ("Satvik (No Onion/Garlic)", 0.9, 0.9, 0.9, 1.0, "Jain/Satvik preparation without onion or garlic"),
]

SIZES = [
    ("Mini Portion", 0.6, 0.6),
    ("Regular Portion", 1.0, 1.0),
    ("Large Thali Portion", 1.5, 1.4),
    ("Jumbo Family Pack", 2.5, 2.0)
]

SLOTS = {
    "breakfast": ["Kanda Poha", "Batata Poha", "Tarri Poha", "Misal Pav", "Usal Pav", "Sabudana Khichdi", "Thalipeeth", "Upma", "Sanja"],
    "lunch": ["Pithla Bhakri", "Zunka Bhakri", "Bharli Vangi", "Varan Bhaat", "Masale Bhaat", "Vangi Bhaat", "Matki Chi Usal", "Veg Kolhapuri", "Tambada Rassa", "Pandhra Rassa", "Malvani Chicken Sukka", "Malvani Fish Curry", "Saoji Chicken", "Kolhapuri Mutton Sukka"],
    "dinner": ["Pithla Bhakri", "Zunka Bhakri", "Bharli Vangi", "Varan Bhaat", "Masale Bhaat", "Matki Chi Usal", "Batata Chi Bhaji", "Katachi Amti", "Tambada Rassa", "Pandhra Rassa", "Malvani Chicken Sukka", "Malvani Fish Curry", "Mutton Kheema Pav", "Bombil Fry", "Saoji Chicken"],
    "snack": ["Vada Pav", "Kothimbir Vadi", "Alu Vadi", "Modak (Ukadiche)", "Puran Poli", "Shrikhand", "Bhakarwadi", "Kanda Bhaji"]
}

def get_slot(name):
    for slot, items in SLOTS.items():
        if name in items:
            return slot
    return "lunch" # fallback

generated_foods = []

for base in BASE_DISHES:
    name_base, diet_type, cal_base, pro_base, carb_base, fat_base, fib_base, iron_base, calc_base, price_base, allergens_base, prep_base = base
    
    slot = get_slot(name_base)
    
    for style in STYLES:
        style_name, cal_mult, pro_mult, fat_mult, price_mult, ing_desc = style
        
        # Skip Satvik for non-veg
        if "Satvik" in style_name and diet_type == "non_vegetarian":
            continue
            
        jain = True if "Satvik" in style_name else False
        
        for size in SIZES:
            size_name, qty_mult, size_price_mult = size
            
            full_name = f"{name_base} ({style_name}, {size_name})"
            
            cal = round(cal_base * cal_mult * qty_mult, 1)
            pro = round(pro_base * pro_mult * qty_mult, 1)
            carb = round(carb_base * qty_mult, 1)
            fat = round(fat_base * fat_mult * qty_mult, 1)
            fib = round(fib_base * qty_mult, 1)
            iron = round(iron_base * qty_mult, 1)
            calc = round(calc_base * qty_mult, 1)
            price = round(price_base * price_mult * size_price_mult, 0)
            
            food_dict = {
                "name": full_name,
                "region": "west", # Maharashtra is west
                "diet_type": diet_type,
                "jain": jain,
                "slot": slot,
                "cal": cal,
                "protein": pro,
                "carbs": carb,
                "fat": fat,
                "fiber": fib,
                "iron": iron,
                "calcium": calc,
                "price": price,
                "allergens": allergens_base,
                "prep": prep_base,
                "season": "all_year",
                "ingredients": f"{ing_desc}. Basic ingredients tailored for {size_name}."
            }
            generated_foods.append(food_dict)

print(f"Generated {len(generated_foods)} Maharashtrian foods.")

# Read existing foods
with open('foods.json', 'r', encoding='utf-8') as f:
    existing_foods = json.load(f)

# Append and save
all_foods = existing_foods + generated_foods

with open('foods.json', 'w', encoding='utf-8') as f:
    json.dump(all_foods, f, indent=4)

print(f"Total foods now in foods.json: {len(all_foods)}")
