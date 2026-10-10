import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy.orm import Session

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.models import User, Food
from app.ml_ranker import ranker
from app.seed_data import seed

sns.set_theme(style="whitegrid")

# Path to the artifacts directory
ARTIFACTS_DIR = r"C:\Users\LENOVO\.gemini\antigravity-ide\brain\4b7e9aaf-2acd-4068-8273-1bac317c2d8b"

def plot_scenario(db, title, filename, user_data, meal_slot, target_calories):
    # Get foods for slot
    query = db.query(Food).filter(Food.meal_slot == meal_slot)
    
    # Apply region filter if specified
    if user_data["region"] != "pan_india":
        query = query.filter((Food.region == user_data["region"]) | (Food.region == "pan_india"))
        
    foods = query.limit(100).all()
    if not foods:
        foods = db.query(Food).filter(Food.meal_slot == meal_slot).limit(100).all()
        
    user = User(**user_data)
    per_meal_budget = (user.weekly_budget_inr / 21) * 1.5 if user.weekly_budget_inr else None
    
    results = ranker.predict_score(
        user=user,
        candidates=foods,
        db=db,
        target_calories=target_calories,
        user_id=1,  # Mock ID
        per_meal_budget=per_meal_budget
    )
    
    top_results = results[:10]
    food_names = [r["food"].name for r in top_results]
    scores = [r["ml_score"] for r in top_results]
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=scores, y=food_names, hue=food_names, palette="magma", legend=False)
    plt.title(title, fontsize=14, pad=15)
    plt.xlabel("ML Prediction Score (0.0 - 1.0)", fontsize=12)
    plt.ylabel("", fontsize=12)
    plt.xlim(0, 1.0)
    plt.tight_layout()
    
    out_path = os.path.join(ARTIFACTS_DIR, filename)
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

def run_scenarios():
    seed()
    db = SessionLocal()
    try:
        # Scenario 1: Budget Student (Rahul) - Dinner, 700 kcal, North Indian, Low budget (₹500/week -> ~₹35/meal)
        plot_scenario(
            db=db,
            title="Scenario 1: Budget-Conscious Student (Rahul)\nNorth Indian | 700 kcal Target | Low Budget (₹500/week)",
            filename="scenario1_budget.png",
            user_data={"name": "Rahul", "region": "north", "weekly_budget_inr": 500, "diet_type": "vegetarian"},
            meal_slot="dinner",
            target_calories=700.0
        )
        
        # Scenario 2: Regional Traditionalist (Priya) - Breakfast, 300 kcal (Weight Loss), South Indian, High budget
        plot_scenario(
            db=db,
            title="Scenario 2: Weight-Loss Traditionalist (Priya)\nSouth Indian | 300 kcal Target | Breakfast",
            filename="scenario2_weightloss.png",
            user_data={"name": "Priya", "region": "south", "weekly_budget_inr": 3000, "diet_type": "vegetarian"},
            meal_slot="breakfast",
            target_calories=300.0
        )
        
        # Scenario 3: High-Protein Bodybuilder - Lunch, 800 kcal, Non-Veg/Any region
        plot_scenario(
            db=db,
            title="Scenario 3: High-Protein Diet (Aman)\nPan India (Non-Veg) | 800 kcal Target | Lunch",
            filename="scenario3_protein.png",
            user_data={"name": "Aman", "region": "pan_india", "weekly_budget_inr": 4000, "diet_type": "non_vegetarian"},
            meal_slot="lunch",
            target_calories=800.0
        )

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_scenarios()
