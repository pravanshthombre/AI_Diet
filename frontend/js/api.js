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

        // Local file execution
        if (window.location.protocol === 'file:') {
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
        
        // Attach Supabase access token if available
        if (typeof authManager !== 'undefined' && authManager.getAccessToken()) {
            headers['Authorization'] = `Bearer ${authManager.getAccessToken()}`;
        }

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
    async getUser() {
        return this.request('/users/me');
    }
    async getUserBySupabaseUid(uid) {
        return this.request(`/users/by-supabase/${encodeURIComponent(uid)}`);
    }
    async getUserByEmail(email) {
        return this.request(`/users/by-email/${encodeURIComponent(email)}`);
    }
    async updateUser(userData) {
        return this.request('/users/me', { method: 'PUT', body: JSON.stringify(userData) });
    }

    // ── Calculators ──
    async getBMI(weight, height) {
        return this.request(`/calculators/bmi?weight_kg=${weight}&height_cm=${height}`);
    }
    async getBMR(weight, height, age, sex, activityLevel) {
        return this.request(`/calculators/bmr-tdee?weight_kg=${weight}&height_cm=${height}&age=${age}&sex=${sex}&activity_level=${activityLevel}`);
    }

    // ── Diet Plan ──
    async getDietPlan() {
        return this.request('/diet-plan');
    }

    // ── Food Database ──
    async searchFoods(query) {
        return this.request(`/foods?search=${encodeURIComponent(query)}`);
    }

    // ── Logging ──
    async logMeal(foodId, mealSlot, servings = 1.0) {
        return this.request('/log-meal', {
            method: 'POST',
            body: JSON.stringify({
                food_id: foodId,
                meal_slot: mealSlot,
                servings: servings
            })
        });
    }

    async logWater(amountMl) {
        return this.request('/log-water', {
            method: 'POST',
            body: JSON.stringify({ amount_ml: Number(amountMl) })
        });
    }

    async logWeight(weightKg) {
        return this.request('/log-weight', {
            method: 'POST',
            body: JSON.stringify({ weight_kg: Number(weightKg) })
        });
    }

    // ── Tracking ──
    async getTracking(arg1, arg2) {
        const dateStr = (arg2 !== undefined) ? arg2 : (arg1 || '');
        const query = dateStr ? `?date=${encodeURIComponent(dateStr)}` : '';
        return this.request(`/tracking${query}`);
    }

    // ── Chat ──
    async chat(arg1, arg2) {
        const message = (arg2 !== undefined) ? arg2 : arg1;
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({ message })
        });
    }

    // ── Feedback ──
    async submitFeedback(foodId, liked, rating) {
        return this.request('/feedback', {
            method: 'POST',
            body: JSON.stringify({ food_id: foodId, liked, rating })
        });
    }

    // ── Food Preferences ──
    async getPreferences() {
        return this.request('/food-preferences');
    }
    async addPreference(arg1, arg2) {
        const foodId = (arg2 !== undefined) ? arg2 : arg1;
        return this.request('/food-preferences', {
            method: 'POST',
            body: JSON.stringify({ food_id: foodId })
        });
    }
    async removePreference(arg1, arg2) {
        const foodId = (arg2 !== undefined) ? arg2 : arg1;
        return this.request(`/food-preferences/${foodId}`, {
            method: 'DELETE'
        });
    }

    // ── Vision / Food Image Analysis ──
    async analyzeFoodImage(formData) {
        const base = this.getBaseUrl();
        const url = `${base}/vision/analyze-plate`;
        const headers = {};
        if (typeof authManager !== 'undefined' && authManager.getAccessToken()) {
            headers['Authorization'] = `Bearer ${authManager.getAccessToken()}`;
        }
        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: formData  // FormData with 'image' field — no Content-Type header (browser sets multipart boundary)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Food image analysis failed');
        }
        return response.json();
    }

    async calibrateNutrition(payload) {
        return this.request('/vision/calibrate', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async getPrepStyles() {
        return this.request('/vision/prep-styles');
    }
}

const api = new ApiClient();

window.api = api;
