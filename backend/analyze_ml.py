import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, Base, engine
from app.models import User, Food
from app.ml_ranker import ranker
from app.seed_data import seed

# Set seaborn style
sns.set_theme(style="whitegrid")

def run_analysis():
    # Ensure DB is seeded
    seed()
    
    db = SessionLocal()
    try:
        # Check if we have foods
        foods = db.query(Food).filter(Food.meal_slot == "lunch").limit(50).all()
        if not foods:
            print("No foods found for lunch.")
            return

        # Create a mock user if one doesn't exist
        user = db.query(User).first()
        if not user:
            user = User(
                name="Rahul",
                age=25,
                sex="male",
                height_cm=175,
                weight_kg=70,
                activity_level="moderate",
                goal="maintain",
                region="west",
                state="Maharashtra",
                diet_type="vegetarian",
                weekly_budget_inr=1500,
                supabase_uid="mock-user-123"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        target_calories = 500.0
        per_meal_budget = (user.weekly_budget_inr / 21) * 1.5 if user.weekly_budget_inr else None

        print(f"Mock User: {user.name}, Region: {user.region}, Budget/Meal: {per_meal_budget if per_meal_budget is None else f'{per_meal_budget:.1f}'}")
        
        # Predict scores
        results = ranker.predict_score(
            user=user,
            candidates=foods,
            db=db,
            target_calories=target_calories,
            user_id=user.id,
            per_meal_budget=per_meal_budget
        )
        
        # Take top 15
        top_results = results[:15]
        
        food_names = [r["food"].name for r in top_results]
        scores = [r["ml_score"] for r in top_results]
        
        # Feature Breakdown for top 5 to show in text
        print("\nTop 5 Feature Breakdown:")
        for r in top_results[:5]:
            f = r["food"]
            features = ranker.extract_features(user, f, target_calories, None, per_meal_budget)
            print(f"- {f.name}: Score {r['ml_score']:.3f} | Features: CalFit={features[0]:.2f}, Reg={features[1]:.0f}, State={features[2]:.0f}, Budg={features[3]:.2f}, Prot={features[4]:.2f}")

        # Plotting
        plt.figure(figsize=(10, 8))
        sns.barplot(x=scores, y=food_names, hue=food_names, palette="viridis", legend=False)
        plt.title(f"ML Model Predictions for Lunch (Target: {target_calories} kcal)", fontsize=14)
        plt.xlabel("Prediction Score (0.0 - 1.0)", fontsize=12)
        plt.ylabel("Food Item", fontsize=12)
        plt.xlim(0, 1.0)
        plt.tight_layout()
        
        output_path = os.path.abspath("ml_predictions.png")
        plt.savefig(output_path, dpi=300)
        print(f"\nSaved prediction graph to {output_path}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_analysis()
