const API_BASE = (typeof window !== 'undefined' && window.location.origin && window.location.origin.includes(':8000')) ? '' : 'http://127.0.0.1:8000';

class ApiClient {
    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const headers = { 'Content-Type': 'application/json', ...options.headers };
        const config = { ...options, headers };

        try {
            const response = await fetch(url, config);
            const contentType = response.headers.get("content-type");
            let data = null;
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                console.error('API Error:', data);
                throw new Error(data.detail || data.message || 'API request failed');
            }
            return data;
        } catch (error) {
            if (error.message && error.message !== 'API request failed') {
                console.error('Network Error:', error);
            }
            throw error;
        }
    }

    // ── Users ──
    async createUser(userData) {
        return this.request('/users', { method: 'POST', body: JSON.stringify(userData) });
    }
    async getUser(userId) {
        return this.request(`/users/${userId}`);
    }
    async updateUser(userId, userData) {
        return this.request(`/users/${userId}`, { method: 'PUT', body: JSON.stringify(userData) });
    }

    // ── Calculators ──
    async getBMI(weight, height) {
        return this.request(`/calculators/bmi?weight_kg=${weight}&height_cm=${height}`);
    }
    async getBMR(weight, height, age, sex, activityLevel) {
        return this.request(`/calculators/bmr-tdee?weight_kg=${weight}&height_cm=${height}&age=${age}&sex=${sex}&activity_level=${activityLevel}`);
    }

    // ── Diet Plan ──
    async getDietPlan(userId) {
        return this.request(`/diet-plan/${userId}`);
    }

    // ── Food Database ──
    async searchFoods(query) {
        return this.request(`/foods?search=${encodeURIComponent(query)}`);
    }

    // ── Logging ──
    async logMeal(userId, foodId, mealSlot, servings) {
        return this.request('/log-meal', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, food_id: foodId, meal_slot: mealSlot, servings })
        });
    }
    async logWater(userId, amountMl) {
        return this.request('/log-water', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, amount_ml: amountMl })
        });
    }
    async logWeight(userId, weightKg) {
        return this.request('/log-weight', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, weight_kg: weightKg })
        });
    }

    // ── Tracking ──
    async getTracking(userId, dateStr) {
        return this.request(`/tracking/${userId}?date=${dateStr}`);
    }

    // ── Chat ──
    async chat(userId, message) {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, message })
        });
    }

    // ── Feedback ──
    async submitFeedback(userId, foodId, liked, rating) {
        return this.request('/feedback', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, food_id: foodId, liked, rating })
        });
    }
}

const api = new ApiClient();

window.api = api;
