"""
Rule-based AI chat assistant.
Understands user intents and calls structured services (never invents
nutrition facts). Per the PRD's most important design decision.

Supported intents:
  - change meal / substitute
  - high protein / specific nutrient requests
  - regional cuisine requests
  - explain warnings / nutrition gaps
  - budget meals
  - general nutrition questions
"""
from sqlalchemy.orm import Session
from . import calculators
from .recommender import recommend_meals, _parse_csv_field
from .substitution import find_substitutes
from .nutrition_gap import calculate_nutrition_gaps
from .models import User, Food


GREETINGS = ["hello", "hi", "hey", "namaste", "good morning", "good evening"]

INTENT_KEYWORDS = {
    "substitute": ["change", "swap", "replace", "substitute", "switch", "different"],
    "high_protein": ["high protein", "protein rich", "more protein", "protein food"],
    "low_calorie": ["low calorie", "light meal", "diet food", "fewer calories"],
    "regional": ["maharashtra", "south indian", "north indian", "bengali", "rajasthani",
                 "gujarati", "kerala", "punjabi", "northeast", "tamil"],
    "budget": ["budget", "cheap", "affordable", "save money", "low cost", "inexpensive"],
    "explain_warning": ["warning", "gap", "deficiency", "explain", "why", "concern"],
    "water": ["water", "hydration", "drink", "fluid"],
    "bmi": ["bmi", "body mass", "weight status"],
    "calories": ["calorie", "how many calories", "daily calories", "tdee"],
    "snack": ["snack", "evening snack", "healthy snack"],
    "breakfast": ["breakfast", "morning meal"],
    "lunch": ["lunch", "afternoon meal"],
    "dinner": ["dinner", "evening meal", "night meal"],
}

REGION_MAP = {
    "maharashtra": "west", "gujarati": "west", "rajasthani": "west",
    "punjabi": "north", "north indian": "north",
    "south indian": "south", "kerala": "south", "tamil": "south",
    "bengali": "east", "northeast": "northeast",
}


def process_chat(db: Session, user_id: int, message: str) -> dict:
    """Process a chat message and return structured response."""
    msg = message.lower().strip()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"reply": "Please complete your profile first to get personalized advice.", "intent": "no_user", "data": None}

    # Greeting
    if any(g in msg for g in GREETINGS):
        return {
            "reply": f"Hi {user.name}! 👋 I'm your NutriCalc assistant. I can help you with:\n"
                     f"• Finding meals (\"suggest a high protein lunch\")\n"
                     f"• Swapping foods (\"change my breakfast\")\n"
                     f"• Nutrition info (\"what's my BMI?\")\n"
                     f"• Budget meals (\"suggest affordable dinner\")\n"
                     f"• Regional cuisine (\"South Indian breakfast\")\n"
                     f"What would you like help with?",
            "intent": "greeting",
            "data": None,
        }

    # Calculate user's targets for context
    bmr = calculators.calculate_bmr(user.weight_kg, user.height_cm, user.age, user.sex)
    tdee = calculators.calculate_tdee(bmr, user.activity_level)
    cal_plan = calculators.calculate_daily_calorie_target(tdee, user.goal, user.sex)
    daily_cal = cal_plan["daily_calorie_target"]

    # Detect intent
    intent = _detect_intent(msg)

    if intent == "explain_warning":
        gaps = calculate_nutrition_gaps(db, user_id, user.sex, user.weight_kg, user.goal, tdee, days=3)
        gap_list = gaps.get("gaps", [])
        if not gap_list:
            reply = "You haven't logged enough meals yet to analyze nutrition gaps. Try logging your meals for a few days!"
        else:
            lines = ["Here's your nutrition analysis (last 3 days):\n"]
            for g in gap_list:
                emoji = "✅" if g["level"] == "good" else "⚠️" if g["level"] == "low" else "🔴"
                lines.append(f"{emoji} **{g['nutrient']}**: {g['actual']:.0f}/{g['target']:.0f} ({g['percentage']:.0f}%) — {g['message']}")
            lines.append(f"\n⚕️ {gaps.get('disclaimer', '')}")
            reply = "\n".join(lines)
        return {"reply": reply, "intent": "explain_warning", "data": gaps}

    if intent == "bmi":
        bmi = calculators.calculate_bmi(user.weight_kg, user.height_cm)
        reply = (f"📊 Your BMI is **{bmi['bmi']}** ({bmi['category']}).\n"
                 f"Healthy weight range for your height: {bmi['healthy_weight_range']}.\n"
                 f"BMI is a screening measure, not a diagnosis.")
        return {"reply": reply, "intent": "bmi", "data": bmi}

    if intent == "calories":
        reply = (f"🔥 Your daily numbers:\n"
                 f"• BMR: {bmr:.0f} kcal (resting metabolism)\n"
                 f"• TDEE: {tdee:.0f} kcal (with activity)\n"
                 f"• Daily target: **{daily_cal:.0f} kcal** (goal: {user.goal})\n"
                 f"• Protein: {cal_plan['protein_g']:.0f}g | Carbs: {cal_plan['carbs_g']:.0f}g | Fat: {cal_plan['fat_g']:.0f}g")
        return {"reply": reply, "intent": "calories", "data": cal_plan}

    if intent == "water":
        water = calculators.calculate_water_intake(user.weight_kg, user.activity_level)
        reply = (f"💧 You should aim for **{water['liters_per_day']}L** "
                 f"({water['glasses_per_day']} glasses) of water daily.\n"
                 f"Tip: Drink a glass when you wake up and before each meal!")
        return {"reply": reply, "intent": "water", "data": water}

    # Meal slot detection for recommendations
    slot = _detect_meal_slot(msg)
    region = user.region or "pan_india"

    # Regional override
    for keyword, reg in REGION_MAP.items():
        if keyword in msg:
            region = reg
            break

    if intent in ("high_protein", "low_calorie", "budget", "regional") or slot:
        meal_slot = slot or "lunch"
        slot_weights = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}
        slot_target = daily_cal * slot_weights.get(meal_slot, 0.25)

        allergies = _parse_csv_field(user.allergies)
        food_dislikes = _parse_csv_field(user.food_dislikes)
        recs = recommend_meals(
            db=db, user_id=user_id, region=region,
            diet_type=user.diet_type, meal_slot=meal_slot,
            target_calories_for_slot=slot_target,
            weekly_budget_inr=user.weekly_budget_inr,
            allergies=allergies,
            food_dislikes=food_dislikes,
            top_n=3,
        )

        if recs:
            lines = [f"🍽️ Here are {meal_slot} suggestions for you:\n"]
            for i, r in enumerate(recs, 1):
                f = r["food"]
                lines.append(
                    f"{i}. **{f.name}** — {f.calories_per_serving:.0f} kcal, "
                    f"{f.protein_g:.0f}g protein, ₹{f.price_inr_per_serving:.0f}\n"
                    f"   _{r['reason']}_"
                )
            reply = "\n".join(lines)
        else:
            reply = f"I couldn't find matching {meal_slot} options. Try adjusting your preferences."

        return {"reply": reply, "intent": intent or "recommend", "data": {"recommendations": [{"food_id": r["food"].id, "name": r["food"].name} for r in recs] if recs else []}}

    if intent == "substitute":
        reply = ("To swap a food, go to your meal plan and tap the 'Swap' button on any food item. "
                 "I'll find nutritionally similar alternatives that match your diet preferences!")
        return {"reply": reply, "intent": "substitute", "data": None}

    # General fallback
    return {
        "reply": f"I can help you with meal suggestions, nutrition info, food swaps, and more! "
                 f"Try asking:\n"
                 f"• \"Suggest a high protein lunch\"\n"
                 f"• \"What's my BMI?\"\n"
                 f"• \"Show me budget-friendly dinners\"\n"
                 f"• \"Explain my nutrition warnings\"\n"
                 f"• \"South Indian breakfast options\"",
        "intent": "general",
        "data": None,
    }


def _detect_intent(msg: str) -> str | None:
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return intent
    return None


def _detect_meal_slot(msg: str) -> str | None:
    if any(w in msg for w in ["breakfast", "morning meal"]):
        return "breakfast"
    if any(w in msg for w in ["lunch", "afternoon"]):
        return "lunch"
    if any(w in msg for w in ["dinner", "night meal", "evening meal"]):
        return "dinner"
    if any(w in msg for w in ["snack", "evening snack"]):
        return "snack"
    return None
