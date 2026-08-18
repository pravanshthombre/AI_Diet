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
        container.innerHTML = `
            <div class="shimmer-skeleton" style="height: 140px; margin-bottom: 16px;"></div>
            <div class="shimmer-skeleton" style="height: 140px; margin-bottom: 16px;"></div>
            <div class="shimmer-skeleton" style="height: 140px;"></div>
        `;

        try {
            const plan = await api.getDietPlan(app.state.userId);
            this.planData = plan;

            // Update summary
            document.getElementById('mp-cals').innerText = `${Math.round(plan.total_calories || 0)} kcal`;
            document.getElementById('mp-pro').innerText = `${Math.round(plan.total_protein || 0)}g`;
            document.getElementById('mp-cost').innerText = `₹${Math.round(plan.total_cost || 0)}`;

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
                    html += `
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
                                <span>🌱 ${food.fiber_g || 0}g Fib</span>
                            </div>
                            <div class="food-footer">
                                <div>
                                    <span style="font-weight: 800; color: var(--primary-800);">₹${food.price_inr_per_serving}</span>
                                    <div style="font-size: 0.75rem; color: var(--text-light);">${item.reason || 'AI Target Match'}</div>
                                </div>
                                <div style="display: flex; gap: 6px;">
                                    <button class="btn btn-outline small" onclick="mealplan.substitute('${slot}', ${food.id})">🔄 Swap</button>
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
        } catch (e) {
            console.error(e);
            container.innerHTML = `<p style="color:var(--accent-coral); text-align:center; padding: 2rem; font-weight: 600;">Failed to load meal plan. Make sure you've selected or created a profile.</p>`;
        }
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
        app.showToast('Finding Indian cuisine alternatives...');
        try {
            const subs = await api.request(`/diet-plan/${app.state.userId}/substitute`, {
                method: 'POST',
                body: JSON.stringify({ meal_slot: slot, food_id: foodId, reason: "user requested swap" })
            });

            if (subs && subs.length > 0) {
                this.showSubModal(slot, subs);
            } else {
                app.showToast('No direct substitute matches found for your criteria.', 'info');
            }
        } catch (e) {
            console.error('Substitute error', e);
            app.showToast('Could not load alternatives', 'error');
        }
    },

    showSubModal(slot, subs) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };

        let itemsHtml = subs.map(s => {
            const f = s.food;
            return `
                <div class="food-card" style="margin-bottom: 12px; cursor: pointer;" onclick="mealplan.applySwap('${slot}', ${f.id}, '${f.name.replace(/'/g, "\\'")}', this)">
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

        modal.innerHTML = `
            <div class="modal-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3 style="font-size: 1.2rem; font-weight: 700; color: var(--primary-900);">Available Substitutions</h3>
                    <button class="btn btn-secondary small" onclick="this.closest('.modal-overlay').remove()">✕</button>
                </div>
                <div>${itemsHtml}</div>
            </div>
        `;
        document.body.appendChild(modal);
    },

    async applySwap(slot, foodId, name, element) {
        const modal = element.closest('.modal-overlay');
        if (modal) modal.remove();
        app.showToast(`Swapped to ${name}!`);
        await this.loadPlan();
    }
};

window.mealplan = mealplan;
