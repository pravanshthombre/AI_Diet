const foodsExplorer = {
    allFoods: [],

    async init() {
        this.setupListeners();
        await this.loadFoods();
    },

    setupListeners() {
        const searchInput = document.getElementById('food-search-query');
        const regionSelect = document.getElementById('food-filter-region');
        const dietSelect = document.getElementById('food-filter-diet');
        const slotSelect = document.getElementById('food-filter-slot');

        let debounceTimer;
        searchInput.oninput = () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => this.loadFoods(), 250);
        };

        regionSelect.onchange = () => this.loadFoods();
        dietSelect.onchange = () => this.loadFoods();
        slotSelect.onchange = () => this.loadFoods();
    },

    async loadFoods() {
        const container = document.getElementById('food-explorer-list');
        container.innerHTML = `
            <div class="shimmer-skeleton" style="height: 160px;"></div>
            <div class="shimmer-skeleton" style="height: 160px;"></div>
            <div class="shimmer-skeleton" style="height: 160px;"></div>
        `;

        const search = document.getElementById('food-search-query').value.trim();
        const region = document.getElementById('food-filter-region').value;
        const diet = document.getElementById('food-filter-diet').value;
        const slot = document.getElementById('food-filter-slot').value;

        let queryParams = [];
        if (search) queryParams.push(`search=${encodeURIComponent(search)}`);
        if (region) queryParams.push(`region=${encodeURIComponent(region)}`);
        if (diet) queryParams.push(`diet_type=${encodeURIComponent(diet)}`);
        if (slot) queryParams.push(`meal_slot=${encodeURIComponent(slot)}`);

        const qs = queryParams.length > 0 ? `?${queryParams.join('&')}` : '';

        try {
            const foods = await api.request(`/foods${qs}`);
            this.allFoods = foods;
            this.renderFoods(foods);
        } catch (e) {
            console.error('Foods load error', e);
            container.innerHTML = `<p style="color: var(--accent-coral); text-align: center; grid-column: 1/-1; padding: 30px;">Error loading food items.</p>`;
        }
    },

    renderFoods(foods) {
        const container = document.getElementById('food-explorer-list');
        if (!foods || foods.length === 0) {
            container.innerHTML = `<p style="color: var(--text-muted); text-align: center; grid-column: 1/-1; padding: 40px; font-weight: 600;">No foods found matching your search criteria.</p>`;
            return;
        }

        container.innerHTML = foods.map(food => {
            const dietBadge = food.diet_type === 'non_vegetarian' ? 'non-veg' : food.diet_type === 'vegan' ? 'vegan' : 'veg';
            return `
                <div class="food-card">
                    <div class="food-header">
                        <span class="food-name">${food.name}</span>
                        <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                            <span class="badge ${dietBadge}">${food.diet_type.replace('_', '-')}</span>
                            <span class="badge region">${food.region}</span>
                        </div>
                    </div>
                    <div class="food-macros">
                        <span>🔥 ${food.calories_per_serving} kcal</span>
                        <span>🥩 ${food.protein_g}g Pro</span>
                        <span>🌾 ${food.carbs_g}g Carb</span>
                        <span>🧈 ${food.fat_g}g Fat</span>
                        <span>🌱 ${food.fiber_g || 0}g Fiber</span>
                    </div>
                    <div class="food-footer">
                        <span style="font-weight: 800; color: var(--primary-800); font-size: 1rem;">₹${food.price_inr_per_serving} <small style="font-size: 0.75rem; font-weight: 500; color: var(--text-muted);">/ serving</small></span>
                        <button class="btn btn-outline small" onclick="foodsExplorer.quickLog(${food.id}, '${food.name.replace(/'/g, "\\'")}')">+ Log Meal</button>
                    </div>
                </div>
            `;
        }).join('');
    },

    async quickLog(foodId, foodName) {
        if (!app.state.userId) {
            app.showToast('Please set up or select a profile first', 'error');
            return;
        }
        try {
            await api.logMeal(app.state.userId, foodId, 'lunch', 1.0);
            app.showToast(`Logged ${foodName} to Lunch!`);
        } catch (e) {
            app.showToast(`Failed to log ${foodName}`, 'error');
        }
    }
};

window.foodsExplorer = foodsExplorer;
