# NutriCalc — AI/ML-Powered Diet & Calorie Calculator

An intelligent dietary recommendation and nutrition planning system tailored for Indian regional diets and wellness goals. Built with FastAPI, scikit-learn ML recommendation ranking, and a dynamic web interface.

---

## 🌟 Key Features

- **Personalized Health Calculators**: BMI, BMR, TDEE, macronutrient distribution, water intake, and optimal meal timings.
- **ML-Powered Meal Recommendations**: Content-based and feature-driven meal recommendations tailored to user dietary restrictions (Vegetarian, Non-Vegetarian, Vegan, Jain, Eggetarian, etc.) and regional cuisines.
- **Automated Daily Meal Planner**: Generates balanced daily meal plans (Breakfast, Lunch, Snacks, Dinner) meeting caloric and macronutrient goals.
- **Nutrition Gap Detection**: Identifies micro and macro nutrient deficiencies based on logged intake.
- **Interactive Tracking & Analytics**: Visual charts for calorie distribution, macros, and weight trends.
- **AI Dietary Chat Assistant**: Context-aware nutritional guidance and food substitution suggestions.

---

## 🏗️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, Pydantic, Scikit-learn, NumPy, Uvicorn
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+), Chart.js
- **Machine Learning**: Scikit-learn cosine similarity & feature ranking engine

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Web browser

### 1. Clone Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd AI_diet
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed the database with food nutrition data
python -m app.seed_data

# Run the backend server
uvicorn app.main:app --reload
```

The FastAPI backend server will start at `http://localhost:8000`.
- Interactive API Docs (Swagger): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 3. Frontend Setup

Open `frontend/index.html` in your web browser, or serve it using any static file server:

```bash
# Using Python's built-in HTTP server from the frontend directory:
cd frontend
python -m http.server 3000
```

Visit `http://localhost:3000` in your browser.

---

## 📁 Project Structure

```
AI_diet/
├── backend/
│   ├── app/
│   │   ├── calculators.py       # BMI, BMR, TDEE, Macro calculators
│   │   ├── chat.py              # AI chat logic
│   │   ├── database.py          # SQLAlchemy database setup
│   │   ├── features.py          # Feature extraction & preprocessing
│   │   ├── main.py              # FastAPI application & API endpoints
│   │   ├── meal_planner.py      # Automated meal planning algorithms
│   │   ├── ml_ranker.py         # ML ranking model
│   │   ├── models.py            # Database models (User, Food, Logs, etc.)
│   │   ├── nutrition_gap.py     # Nutrient deficit detection
│   │   ├── optimizer.py         # Goal optimization algorithms
│   │   ├── recommender.py       # Food recommendation engine
│   │   ├── schemas.py           # Pydantic schemas / request models
│   │   ├── seed_data.py         # Nutritional database seeding script
│   │   └── substitution.py      # Food substitution finder
│   ├── bootstrap.py             # Setup bootstrap script
│   ├── requirements.txt         # Python dependencies
│   └── test_suite.py            # Backend test suite
├── frontend/
│   ├── css/
│   │   └── styles.css           # UI Styling & theme
│   ├── js/
│   │   ├── api.js               # API service layer
│   │   ├── app.js               # Main application orchestration
│   │   ├── charts.js            # Chart rendering utilities
│   │   ├── chat.js              # Chat interface handler
│   │   ├── dashboard.js         # Dashboard view controller
│   │   ├── foods.js             # Food catalog view
│   │   ├── mealplan.js          # Meal plan view controller
│   │   ├── onboarding.js        # User onboarding wizard
│   │   └── tracking.js          # Daily tracking logic
│   └── index.html               # Main frontend entry point
└── README.md
```

---

## 🧪 Testing

Run backend tests:

```bash
cd backend
python test_suite.py
```

---

## 📄 License

This project is licensed under the MIT License.
"# AI_Diet" 
