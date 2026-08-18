const tracking = {
    waterAmount: 0,
    waterGoalMl: 2500,

    async init() {
        if (!app.state.user) return;
        const user = app.state.user;

        try {
            const waterTarget = await api.request(`/calculators/water-intake?weight_kg=${user.weight_kg}&activity_level=${user.activity_level}&climate=moderate`);
            this.waterGoalMl = (waterTarget.liters_per_day || 2.5) * 1000;

            const today = new Date().toISOString().split('T')[0];
            const track = await api.getTracking(user.id, today);
            this.waterAmount = track.actual_water_ml || 0;
            this.updateWaterUI();

            // Setup bindings
            const addWaterBtn = document.getElementById('btn-add-water');
            if (addWaterBtn) addWaterBtn.onclick = () => this.logWater(250);

            const logWtBtn = document.getElementById('btn-log-weight');
            if (logWtBtn) logWtBtn.onclick = () => this.logWeight();

            const logMealBtn = document.getElementById('btn-log-meal');
            if (logMealBtn) logMealBtn.onclick = () => this.logMeal();

            // Setup food search autocomplete
            const foodInput = document.getElementById('input-log-food');
            if (foodInput) {
                foodInput.addEventListener('input', () => this.searchFoods(foodInput.value));
            }
        } catch (e) {
            console.error('Tracking init error', e);
        }
    },

    updateWaterUI() {
        const glasses = Math.floor(this.waterAmount / 250);
        const targetGlasses = Math.floor(this.waterGoalMl / 250);
        const countEl = document.getElementById('water-count');
        if (countEl) {
            countEl.innerText = `${glasses} / ${targetGlasses} glasses (${this.waterAmount} / ${this.waterGoalMl} ml)`;
        }
        let pct = Math.min(100, (this.waterAmount / this.waterGoalMl) * 100);
        const fillEl = document.getElementById('water-fill-level');
        if (fillEl) fillEl.style.width = `${pct}%`;
    },

    async logWater(amount) {
        try {
            const result = await api.logWater(app.state.userId, amount);
            this.waterAmount = result.total_today_ml || (this.waterAmount + amount);
            this.updateWaterUI();
            app.showToast(`Logged +${amount}ml water! Stay hydrated.`);
        } catch (e) {
            app.showToast('Failed to log water', 'error');
        }
    },

    async logWeight() {
        const input = document.getElementById('input-log-weight');
        const val = parseFloat(input.value);
        if (!val || val < 20 || val > 300) {
            app.showToast('Please enter a valid weight between 20-300 kg', 'error');
            return;
        }
        try {
            await api.logWeight(app.state.userId, val);
            app.showToast(`Weight updated to ${val} kg!`);
            input.value = '';
            app.state.user.weight_kg = val;
        } catch (e) {
            app.showToast('Failed to log weight', 'error');
        }
    },

    async searchFoods(query) {
        if (!query || query.length < 2) {
            this.clearSuggestions();
            return;
        }
        try {
            const foods = await api.request(`/foods?search=${encodeURIComponent(query)}`);
            this.showSuggestions(foods.slice(0, 6));
        } catch (e) { /* ignore */ }
    },

    showSuggestions(foods) {
        this.clearSuggestions();
        if (foods.length === 0) return;
        const input = document.getElementById('input-log-food');
        const parent = input.parentElement;
        
        const suggestions = document.createElement('div');
        suggestions.id = 'food-suggestions';
        suggestions.style.cssText = 'background:#ffffff; border:1px solid var(--border-subtle); border-radius:12px; max-height:220px; overflow-y:auto; position:absolute; top:calc(100% + 4px); left:0; width:100%; z-index:100; box-shadow:var(--shadow-md);';
        
        foods.forEach(f => {
            const item = document.createElement('div');
            item.style.cssText = 'padding:10px 14px; cursor:pointer; border-bottom:1px solid #f1f5f3; font-size:0.9rem; display:flex; justify-content:space-between; align-items:center;';
            item.innerHTML = `
                <div>
                    <strong>${f.name}</strong>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${f.diet_type.replace('_', '-')} · ${f.region}</div>
                </div>
                <span style="font-weight:700; color:var(--primary-700);">${f.calories_per_serving} kcal</span>
            `;
            item.onclick = () => {
                input.value = f.name;
                input.dataset.foodId = f.id;
                this.clearSuggestions();
            };
            item.onmouseenter = () => item.style.background = 'var(--primary-50)';
            item.onmouseleave = () => item.style.background = '#ffffff';
            suggestions.appendChild(item);
        });
        parent.appendChild(suggestions);
    },

    clearSuggestions() {
        const el = document.getElementById('food-suggestions');
        if (el) el.remove();
    },

    async logMeal() {
        const input = document.getElementById('input-log-food');
        const sel = document.getElementById('sel-log-meal');
        const srv = document.getElementById('input-log-servings');

        const foodId = input.dataset.foodId;
        const mealSlot = sel.value;
        const servings = parseFloat(srv.value) || 1.0;

        if (!foodId) {
            app.showToast('Please search and select a food from the dropdown list', 'error');
            return;
        }

        try {
            await api.logMeal(app.state.userId, parseInt(foodId), mealSlot, servings);
            app.showToast(`Logged food to ${mealSlot}!`);
            input.value = '';
            delete input.dataset.foodId;
        } catch (e) {
            app.showToast('Failed to log meal', 'error');
        }
    }
};

window.tracking = tracking;
