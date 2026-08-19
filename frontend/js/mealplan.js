const mealplan = {
    planData: null,

    async init() {
        if (!app.state.user) return;
        await this.loadPlan();
        document.getElementById('btn-regen-plan').onclick = () => {
            app.showToast('Regenerating customized daily plan...');
            this.loadPlan();
        };
    },

    async loadPlan() {
        const container = document.getElementById('mealplan-content');
        if (!container) return;
        if (!app.state.userId) return;

        container.innerHTML = `
            <div class="shimmer-skeleton" style="height: 140px; margin-bottom: 16px;"></div>
            <div class="shimmer-skeleton" style="height: 140px; margin-bottom: 16px;"></div>
            <div class="shimmer-skeleton" style="height: 140px;"></div>
        `;

        try {
            const plan = await api.getDietPlan(app.state.userId);
            this.planData = plan;
            this.renderPlan();
        } catch (e) {
            console.error(e);
            container.innerHTML = `<p style="color:var(--accent-coral); text-align:center; padding: 2rem; font-weight: 600;">Failed to load meal plan. Make sure you've selected or created a profile.</p>`;
        }
    },

    renderPlan() {
        const container = document.getElementById('mealplan-content');
        if (!container || !this.planData) return;

        const plan = this.planData;

        // Recalculate totals based on current local state
        let currentTotalCals = 0;
        let currentTotalPro = 0;
        let currentTotalCost = 0;

        ['breakfast', 'lunch', 'snack', 'dinner'].forEach(slot => {
            if (plan[slot] && plan[slot].length > 0) {
                // Assuming first item is the primary pick
                const f = plan[slot][0].food;
                currentTotalCals += f.calories_per_serving;
                currentTotalPro += f.protein_g;
                currentTotalCost += f.price_inr_per_serving;
            }
        });

        // Update summary
        document.getElementById('mp-cals').innerText = `${Math.round(currentTotalCals || plan.total_calories || 0)} kcal`;
        document.getElementById('mp-pro').innerText = `${Math.round(currentTotalPro || plan.total_protein || 0)}g`;
        document.getElementById('mp-cost').innerText = `₹${Math.round(currentTotalCost || plan.total_cost || 0)}`;

        let html = '';
        const slotLabels = {
            breakfast: { icon: '☀️', label: 'Breakfast', time: plan.meal_timing?.breakfast || '8:00 AM' },
            lunch:     { icon: '🍛', label: 'Lunch',     time: plan.meal_timing?.lunch || '1:00 PM' },
            snack:     { icon: '🫖', label: 'Evening Snack', time: plan.meal_timing?.snack || '5:00 PM' },
            dinner:    { icon: '🌙', label: 'Dinner',    time: plan.meal_timing?.dinner || '8:30 PM' },
        };

        for (const [slot, meta] of Object.entries(slotLabels)) {
            const foods = plan[slot] || [];
            if (foods.length === 0) continue;

            html += `
                <div class="meal-slot-container">
                    <div class="meal-slot-header">
                        <span>${meta.icon} ${meta.label}</span>
                        <span class="meal-slot-time">⏰ ${meta.time}</span>
                    </div>
                    <div class="food-cards-grid">
            `;

            foods.forEach(item => {
                const food = item.food;
                const dietBadge = food.diet_type === 'non_vegetarian' ? 'non-veg' : food.diet_type === 'vegan' ? 'vegan' : 'veg';
                const isPreferred = (item.reason || '').includes('preferred');
                const preferredBadge = isPreferred ? '<span class="badge preferred" style="background: #fee2e2; color: #dc2626; font-weight: 700;">❤️ Preferred</span>' : '';
                html += `
                    <div class="food-card${isPreferred ? ' food-preferred' : ''}">
                        <div class="food-header">
                            <span class="food-name">${food.name}</span>
                            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                                ${preferredBadge}
                                <span class="badge ${dietBadge}">${food.diet_type.replace('_', '-')}</span>
                                <span class="badge region">${food.region}</span>
                            </div>
                        </div>
                        <div class="food-macros">
                            <span>🔥 ${food.calories_per_serving} kcal</span>
                            <span>🥩 ${food.protein_g}g Pro</span>
                            <span>🌾 ${food.carbs_g}g Carb</span>
                            <span>🧈 ${food.fat_g}g Fat</span>
                            <span>🌱 ${food.fiber_g || 0}g Fib</span>
                        </div>
                        <div class="food-footer">
                            <div>
                                <span style="font-weight: 800; color: var(--primary-800);">₹${food.price_inr_per_serving}</span>
                                <div style="font-size: 0.75rem; color: var(--text-light);">${item.reason || 'AI Target Match'}</div>
                            </div>
                            <div style="display: flex; gap: 6px;">
                                <button class="btn btn-outline small" onclick="mealplan.substitute('${slot}', ${food.id})">Swap</button>
                                <button class="btn btn-secondary small" onclick="mealplan.quickLogFood(${food.id}, '${slot}', '${food.name.replace(/'/g, "\\'")}')">✓ Eaten</button>
                            </div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }

        // Hydration advice card
        if (plan.water) {
            html += `
                <div class="card" style="background: linear-gradient(135deg, #e0f2fe 0%, #ffffff 100%); border-color: #bae6fd; text-align: center; margin-top: 10px;">
                    <h3 style="color: #0369a1; font-size: 1.1rem; margin-bottom: 6px;">💧 Recommended Daily Hydration</h3>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">
                        Aim for <strong>${plan.water.liters_per_day} Liters</strong> (${plan.water.glasses_per_day} glasses) spaced evenly across your meals.
                    </p>
                </div>
            `;
        }

        container.innerHTML = html;
    },

    async quickLogFood(foodId, slot, name) {
        try {
            await api.logMeal(app.state.userId, foodId, slot, 1.0);
            app.showToast(`Logged "${name}" to ${slot}!`);
        } catch (e) {
            app.showToast(`Failed to log ${name}`, 'error');
        }
    },

    async substitute(slot, foodId) {
        // Show loading modal immediately
        const loadingModalId = `sub-modal-${Date.now()}`;
        this.showSubModalLoading(loadingModalId);

        try {
            const subs = await api.request(`/diet-plan/${app.state.userId}/substitute`, {
                method: 'POST',
                body: JSON.stringify({ meal_slot: slot, food_id: foodId, reason: "user requested swap" })
            });

            const modal = document.getElementById(loadingModalId);
            if (!modal) return; // User closed it early

            if (subs && subs.length > 0) {
                this.currentSubs = subs;
                this.updateSubModalContent(modal, slot, foodId, subs);
            } else {
                modal.remove();
                app.showToast('No direct substitute matches found for your criteria.', 'info');
            }
        } catch (e) {
            console.error('Substitute error', e);
            const modal = document.getElementById(loadingModalId);
            if (modal) modal.remove();
            app.showToast('Could not load alternatives', 'error');
        }
    },

    showSubModalLoading(modalId) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = modalId;
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };

        const skeletons = Array(3).fill(`
            <div class="shimmer-skeleton" style="height: 100px; margin-bottom: 12px; border-radius: var(--radius-md);"></div>
        `).join('');

        modal.innerHTML = `
            <div class="modal-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3 style="font-size: 1.2rem; font-weight: 700; color: var(--primary-900);">Available Substitutions</h3>
                    <button class="btn btn-secondary small" onclick="this.closest('.modal-overlay').remove()">✕</button>
                </div>
                <div id="sub-modal-content-area">${skeletons}</div>
            </div>
        `;
        document.body.appendChild(modal);
    },

    updateSubModalContent(modal, slot, originalFoodId, subs) {
        const contentArea = modal.querySelector('#sub-modal-content-area');
        if (!contentArea) return;

        let itemsHtml = subs.map((s, index) => {
            const f = s.food;
            return `
                <div class="food-card" style="margin-bottom: 12px; cursor: pointer;" onclick="mealplan.applySwap('${slot}', ${originalFoodId}, ${index}, this)">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>${f.name}</strong>
                        <span class="badge veg">Match: ${Math.round(s.similarity * 100)}%</span>
                    </div>
                    <div class="food-macros" style="margin: 6px 0;">
                        <span>🔥 ${f.calories_per_serving} kcal (${s.calorie_diff > 0 ? '+' : ''}${s.calorie_diff} cal)</span>
                        <span>🥩 ${f.protein_g}g P</span>
                        <span>₹${f.price_inr_per_serving}</span>
                    </div>
                    <button class="btn btn-primary small w-100" style="margin-top: 6px;">Select This Substitute</button>
                </div>
            `;
        }).join('');

        contentArea.innerHTML = itemsHtml;
    },

    applySwap(slot, originalFoodId, subIndex, element) {
        const modal = element.closest('.modal-overlay');
        if (modal) modal.remove();

        const selectedSub = this.currentSubs[subIndex];
        if (!selectedSub) return;

        // Find and replace the food in the local state
        const slotItems = this.planData[slot];
        if (slotItems) {
            const itemIndex = slotItems.findIndex(i => i.food.id === originalFoodId);
            if (itemIndex !== -1) {
                slotItems[itemIndex] = {
                    food: selectedSub.food,
                    score: 1.0,
                    reason: "Swapped by you ✨"
                };
            }
        }

        app.showToast(`Swapped to ${selectedSub.food.name}!`);
        this.renderPlan(); // Instantly update the UI without reloading
    }
};

window.mealplan = mealplan;
