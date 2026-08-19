class ApiClient {
    constructor() {
        this.fallbackRenderUrl = 'https://nutricalc-backend.onrender.com';
    }

    getBaseUrl() {
        if (typeof window === 'undefined') return 'http://127.0.0.1:8000';
        if (window.API_BASE_URL) return window.API_BASE_URL.replace(/\/+$/, '');
        
        const stored = localStorage.getItem('NUTRICALC_API_BASE');
        if (stored) return stored.replace(/\/+$/, '');

        // If served from the same domain (e.g. unified full-stack on Render or localhost)
        if (window.location.origin.includes('onrender.com') || window.location.origin.includes(':8000')) {
            return '';
        }

        // Local development server (e.g. Python http.server on port 3000 / 5500)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'http://127.0.0.1:8000';
        }

        // Default to cloud backend on Vercel / Netlify / external hosting
        return this.fallbackRenderUrl;
    }

    setBaseUrl(url) {
        if (url && url.trim()) {
            localStorage.setItem('NUTRICALC_API_BASE', url.trim().replace(/\/+$/, ''));
        } else {
            localStorage.removeItem('NUTRICALC_API_BASE');
        }
    }

    async testConnection(customUrl = null) {
        const base = customUrl !== null ? (customUrl || '').replace(/\/+$/, '') : this.getBaseUrl();
        const testUrl = `${base}/api/health`;
        try {
            const res = await fetch(testUrl, { method: 'GET', signal: AbortSignal.timeout(5000) });
            return res.ok;
        } catch (e) {
            return false;
        }
    }

    async request(endpoint, options = {}) {
        const base = this.getBaseUrl();
        const url = `${base}${endpoint}`;
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
                throw new Error(typeof data === 'object' ? (data.detail || data.message || 'API request failed') : data);
            }
            return data;
        } catch (error) {
            if (error.name === 'TypeError' || error.message.includes('fetch')) {
                console.error('Network Connection Error to:', url);
                if (typeof app !== 'undefined' && app.showToast) {
                    app.showToast(`Cannot reach backend server. Check API URL in Settings.`, 'error');
                }
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

    // ── Food Preferences ──
    async getPreferences(userId) {
        return this.request(`/food-preferences/${userId}`);
    }
    async addPreference(userId, foodId) {
        return this.request('/food-preferences', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, food_id: foodId })
        });
    }
    async removePreference(userId, foodId) {
        return this.request(`/food-preferences/${userId}/${foodId}`, {
            method: 'DELETE'
        });
    }
}

const api = new ApiClient();

window.api = api;
