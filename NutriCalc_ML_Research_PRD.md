# NutriCalc Recommendation Engine — Complete Product Requirements Document (PRD)

## 1. Product Overview & Problem Statement
### 1.1 Problem Statement
Traditional calorie-tracking and diet apps treat nutrition as purely mathematical (e.g., "eat 1500 calories"), ignoring cultural context, regional taste, budget, and dietary restrictions. Users in India face a unique challenge: generic diet apps recommend Western foods (e.g., Avocado Toast, Quinoa) that are culturally unfamiliar, expensive, or locally inaccessible, leading to high churn rates and low diet adherence.

### 1.2 The Solution
NutriCalc is an AI-powered, hyper-localized Indian diet and calorie calculator. The core of the product is the **NutriCalc Recommendation Engine**, a machine learning system that dynamically generates meal plans by balancing strict macro/micronutrient goals with human preference, regional Indian cuisines, and budget constraints.

---

## 2. Target Audience & Personas
- **The Budget-Conscious Student (Rahul):** Wants to hit 120g of protein daily but only has ₹1500/week to spend on food. Needs cheap, local, high-protein options (e.g., Soya Chunks, Sprouts).
- **The Regional Traditionalist (Priya):** Wants to lose weight but refuses to give up South Indian staples (e.g., Idli, Dosa). Needs a diet plan that incorporates her cultural foods in healthy portion sizes.
- **The Allergy-Restricted User (Aman):** Has strict dietary constraints (e.g., lactose intolerant, gluten-free) and needs an intelligent engine that never hallucinates unsafe foods.

---

## 3. Success Metrics (KPIs)
To evaluate the success of the ML Recommendation Engine, we will track:
1. **Diet Adherence Rate (Primary):** Percentage of users who stick to >80% of the recommended meal plan for 7 consecutive days.
2. **Recommendation Acceptance Rate:** The ratio of ML-suggested meals that are logged vs. manually swapped/replaced.
3. **Cold-Start Conversion:** Percentage of new users who complete onboarding and log at least 3 meals on their first day using the fallback heuristic model.
4. **Latency (NFR):** The P95 response time for generating a daily meal plan must be < 1.2 seconds.

---

## 4. Functional Requirements & User Stories
| Feature ID | User Story | Priority |
|---|---|---|
| **ML-01** | As a user, I want meals recommended from my specific Indian state so I can eat familiar foods. | P0 |
| **ML-02** | As a user, I want the system to learn my tastes over time so it stops recommending foods I dislike. | P0 |
| **ML-03** | As a user on a budget, I want the ML engine to filter out expensive meals that exceed my weekly limit. | P1 |
| **ML-04** | As a user with allergies, I want a 100% guarantee that my allergens will never appear in my meal plan. | P0 (Critical Safety) |
| **ML-05** | As a user, I want to see a balanced mix of historical favorites and new, similar foods to avoid diet fatigue. | P2 |

---

## 5. Machine Learning Architecture (Research Methodology)

### 5.1 Algorithm Selection
**Model:** `scikit-learn.ensemble.GradientBoostingRegressor`
- **Type:** Supervised Learning (Regression)
- **Objective:** Predict a continuous preference score (0.0 to 1.0) for a given `(User, Food)` pair.
- **Why Gradient Boosting?** 
  - Handles non-linear nutritional relationships (e.g., protein has diminishing returns after a certain threshold).
  - Highly interpretable feature importances for debugging.

### 5.2 Feature Engineering
The model extracts a 6-dimensional feature vector `X` for every candidate pair:

| Feature Name | Description & Impact |
|---|---|
| `calorie_fit` | Inverse absolute difference between the food's calories and the user's meal-slot target. Prevents recommending heavy 800kcal meals for a 300kcal snack slot. |
| `region_match` | Binary (0/1). Exact match between user's preferred region (e.g., "South Indian") and the food's origin. |
| `state_match` | Binary (0/1). Hyper-local exact match (e.g., User: Maharashtra, Food: Misal Pav). |
| `budget_fit` | Measures how well the food's `price_inr_per_serving` fits within the user's per-meal budget threshold. |
| `protein_norm` | Normalized protein content, capped at 30g per serving to favor high-protein options without strictly requiring them. |
| `rating_norm` | Historical explicit feedback. 5-stars = `1.0`, 1-star = `0.2`. Untried foods = `0.0`. |

### 5.3 Training Methodology & Telemetry
The model uses a hybrid **Explicit + Implicit Data Collection** pipeline to prevent cold-start starvation.
- **Explicit Feedback:** User ratings (1-5 stars) from the UI.
- **Implicit Feedback:** If a user logs a meal >3 times without rating it, the system infers positive affinity and assigns a training label of `0.75`.

### 5.4 The Cold-Start Fallback
When a new user signs up, the system lacks enough data (requires `n >= 10` samples) to train a personalized GBR model.
- **Fallback:** A static, heuristically weighted rule-based ranker.
- **Weights:** `calorie_fit` (35%), `region_match` (15%), `budget_fit` (15%), `rating_norm` (15%), `state_match` (10%), `protein_norm` (10%).

---

## 6. Safety & Constraint Enforcement (Hard Filters)
Machine Learning models can occasionally hallucinate. NutriCalc uses a strict **"Hard Constraints First, ML Second"** pipeline. 

Before any food enters the ML model for scoring, it must pass a strict boolean filter:
1. **Allergen Filter:** Substring and word-boundary matching (e.g., Peanuts, Lactose) drops the food from the candidate pool instantly.
2. **Dietary Integrity:** A vegan user will *never* see paneer, regardless of ML scoring.
3. **Explicit Dislikes:** Token-based boundary matching filters out specific ingredients the user hates (e.g., "eggplant").

---

## 7. Real-Time Blending & Scoring
To maintain dietary variety and avoid the "echo chamber" effect (where the ML just recommends the same 5 foods forever), the final score is a blend of **Content-Based Similarity** and **ML Prediction**:

$$Final Score = 0.6 \times (Cosine Similarity) + 0.4 \times (ML Score)$$

- **Cosine Similarity:** Uses L2-normalized `[calories, protein, carbs, fat, fiber, iron]` vectors to find nutritionally similar foods to the user's historical favorites.
- **ML Score:** The Gradient Boosting prediction representing taste and budget fit.

---

## 8. Technical Stack & Dependencies
- **Backend Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL (Supabase) + SQLAlchemy ORM
- **ML Libraries:** `scikit-learn`, `numpy`
- **Deployment:** Render (Stateless containerized deployment)

---

## 9. Future Roadmap & Research Opportunities
1. **Contextual Bandits for Exploration:** Implementing an Epsilon-Greedy approach to occasionally recommend foods outside the user's historical preferences to gather new training data.
2. **Time-Series Features:** Adding features for "Time since last eaten" to naturally penalize the model from recommending the exact same meal 5 days in a row (dietary fatigue).
3. **Micronutrient Boosting:** Adding Vitamin B12 and Calcium as features specifically for vegetarian profiles to ensure long-term health integrity.

---

## 10. Appendix: Mathematical Formulas & Calculations
Below are the exact mathematical formulas used during feature engineering to map raw nutritional and user data into the `[0, 1]` continuous vector space required by the model.

### 10.1 Calorie Fit
Penalizes foods that deviate from the user's exact calorie target for a specific meal slot.
$$CalorieFit = \max\left(0,\ 1 - \frac{|FoodCalories - TargetCalories|}{TargetCalories}\right)$$

### 10.2 Budget Fit
Determines the user's maximum allowable spend per meal, then penalizes foods that exceed it.
$$PerMealBudget = \frac{WeeklyBudget}{7 \times MealsPerDay}$$
$$BudgetFit = \begin{cases} 1.0, & \text{if } FoodPrice \le PerMealBudget \\ \max\left(0,\ 1 - \frac{FoodPrice - PerMealBudget}{PerMealBudget}\right), & \text{if } FoodPrice > PerMealBudget \end{cases}$$

### 10.3 Protein Normalization
Normalizes the protein content of a food up to a ceiling of 30 grams. Any food with $\ge 30g$ protein receives the maximum score of 1.0.
$$ProteinNorm = \min\left(1.0,\ \frac{FoodProtein_{grams}}{30.0}\right)$$

### 10.4 Rating Normalization (Explicit Feedback)
Maps a 1-to-5 star user rating into a continuous `[0.2, 1.0]` multiplier.
$$RatingNorm = \left( \frac{StarRating - 1}{4} \right) \times 0.8 + 0.2$$

### 10.5 Content-Based Cosine Similarity
Calculates the nutritional similarity between a candidate food (Vector $A$) and the user's historical favorite foods (Vector $B$). The feature space for vectors is: `[calories, protein, carbs, fat, fiber, iron]`.
$$CosineSimilarity(A, B) = \frac{A \cdot B}{||A|| \times ||B||} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$$

### 10.6 Final Hybrid Scoring Blend
Combines the deterministic nutritional cosine similarity with the ML model's preference prediction to calculate the final ranking score.
$$FinalScore = (0.6 \times CosineSimilarity) + (0.4 \times ML\_Prediction\_Score)$$
