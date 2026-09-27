const dashboard = {
    async init() {
        if (!app.state.user && app.state.userId) {
            await app.loadUser();
        }
        if (!app.state.user) return;
        const user = app.state.user;

        document.getElementById('dash-greeting-name').innerText = `Namaste, ${user.name}`;
        const opts = { weekday: 'long', month: 'short', day: 'numeric' };
        document.getElementById('dash-date').innerText = new Date().toLocaleDateString('en-IN', opts);
        
        const subtitleEl = document.getElementById('dash-user-subtitle');
        if (subtitleEl) {
            subtitleEl.innerText = `${user.region.toUpperCase()} cuisine · ${user.diet_type.replace('_', '-')} · Goal: ${user.goal.replace('_', ' ')}`;
        }

        const wtEl = document.getElementById('dash-current-wt');
        if (wtEl) wtEl.innerText = user.weight_kg;

        await this.loadMetrics(user);
        await this.loadTodayProgress(user);
        await this.loadWeightTrend(user);
    },

    async loadMetrics(user) {
        try {
            const bmiData = await api.getBMI(user.weight_kg, user.height_cm);
            const bmrData = await api.getBMR(user.weight_kg, user.height_cm, user.age, user.sex, user.activity_level);
            const targetData = await api.request(`/calculators/calorie-target?tdee=${bmrData.tdee}&goal=${user.goal}&sex=${user.sex}`);
            const waterTarget = await api.request(`/calculators/water-intake?weight_kg=${user.weight_kg}&activity_level=${user.activity_level}&climate=moderate`);

            document.getElementById('dash-bmi-val').innerText = bmiData.bmi.toFixed(1);
            document.getElementById('dash-bmi-status').innerText = `${bmiData.category || 'Normal'} Weight`;
            document.getElementById('dash-bmr-val').innerText = Math.round(bmrData.bmr);
            document.getElementById('dash-tdee-val').innerText = Math.round(targetData.daily_calorie_target);
            document.getElementById('dash-water-val').innerText = waterTarget.liters_per_day.toFixed(1);

            setTimeout(() => {
                charts.drawGauge('bmi-gauge', bmiData.bmi, 15, 35, 'BMI');
            }, 80);
        } catch (e) {
            console.error("Metrics load error", e);
        }
    },

    async loadTodayProgress(user) {
        try {
            const today = new Date().toISOString().split('T')[0];
            const tracking = await api.getTracking(today);

            const calPct = Math.min(100, (tracking.actual_calories / (tracking.target_calories || 2000)) * 100) || 0;
            const proPct = Math.min(100, (tracking.actual_protein / (tracking.target_protein || 60)) * 100) || 0;
            const fibPct = Math.min(100, (tracking.actual_fiber / (tracking.target_fiber || 30)) * 100) || 0;
            const h2oPct = Math.min(100, (tracking.actual_water_ml / (tracking.target_water_ml || 2500)) * 100) || 0;

            setTimeout(() => {
                charts.drawProgressRing('cal-ring', calPct, '#10b981', 'Calories');
                charts.drawProgressRing('protein-ring', proPct, '#f97316', 'Protein');
                charts.drawProgressRing('fiber-ring', fibPct, '#047857', 'Fiber');
                charts.drawProgressRing('water-ring', h2oPct, '#0284c7', 'Water');
            }, 80);

            // Goal Reached Celebrations (tracked individually)
            const goals = [
                { id: 'cal', pct: calPct, name: 'Calorie' },
                { id: 'pro', pct: proPct, name: 'Protein' },
                { id: 'fib', pct: fibPct, name: 'Fiber' },
                { id: 'h2o', pct: h2oPct, name: 'Hydration' }
            ];

            let newlyCompletedGoal = null;

            for (const goal of goals) {
                const storageKey = `celebrated_${goal.id}_today`;
                if (goal.pct >= 100 && !sessionStorage.getItem(storageKey)) {
                    sessionStorage.setItem(storageKey, 'true');
                    newlyCompletedGoal = goal;
                    break; // Only celebrate one at a time to prevent overlapping modals
                }
            }
            
            if (newlyCompletedGoal) {
                setTimeout(() => {
                    const modal = document.getElementById('goalModal');
                    if (modal) {
                        modal.classList.remove('hidden');
                        
                        const textEl = document.getElementById('goalModalText');
                        if(textEl) textEl.innerText = `You've hit your daily ${newlyCompletedGoal.name} target!`;
                    }
                    
                    // Generate Confetti
                    const colors = ['#10b981', '#f97316', '#047857', '#0ea5e9'];
                    for(let i = 0; i < 60; i++) {
                        const confetti = document.createElement('div');
                        confetti.classList.add('confetti-piece');
                        confetti.style.left = Math.random() * 100 + 'vw';
                        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                        confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';
                        confetti.style.animationDelay = (Math.random() * 0.5) + 's';
                        document.body.appendChild(confetti);
                        
                        setTimeout(() => confetti.remove(), 5000); // Clean up
                    }
                }, 800); // Small delay before modal shows after rings draw
            }


            // Nutrition gap alerts
            try {
                const gaps = await api.request(`/nutrition-gaps/${user.id}?days=1`);
                const alertsEl = document.getElementById('dash-alerts');
                if (gaps.gaps && gaps.gaps.length > 0) {
                    const warnings = gaps.gaps.filter(g => g.level !== 'good');
                    if (warnings.length > 0) {
                        alertsEl.innerHTML = warnings.map(g => {
                            const alertClass = g.level === 'high_concern' ? 'alert-card danger' : g.level === 'moderate_concern' ? 'alert-card warning' : 'alert-card';
                            const icon = g.level === 'high_concern' ? '⚠️' : '💡';
                            return `<div class="${alertClass}">
                                <span style="font-size: 1.2rem;">${icon}</span>
                                <div>
                                    <strong>${g.nutrient} Alert:</strong> ${g.message}
                                </div>
                            </div>`;
                        }).join('');
                    } else {
                        alertsEl.innerHTML = `<div class="alert-card" style="border-left-color: var(--primary-500);">
                            <span>✨</span>
                            <div><strong>All Nutrition Targets Balanced:</strong> Great job maintaining your Indian meal macros today!</div>
                        </div>`;
                    }
                }
            } catch (e) { /* no alerts */ }
        } catch (e) {
            console.error("Progress load error", e);
        }
    },

    async loadWeightTrend(user) {
        try {
            const history = await api.request(`/weight-history/${user.id}?limit=7`);
            if (history && history.length > 0) {
                const data = history.map(h => h.weight_kg);
                const labels = history.map(h => {
                    const d = new Date(h.date);
                    return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
                });
                setTimeout(() => charts.drawLineChart('weight-chart', data, labels), 80);
            } else {
                const mockData = [user.weight_kg + 0.8, user.weight_kg + 0.5, user.weight_kg + 0.4, user.weight_kg + 0.2, user.weight_kg];
                setTimeout(() => charts.drawLineChart('weight-chart', mockData, ['D-4', 'D-3', 'D-2', 'D-1', 'Today']), 80);
            }
        } catch (e) {
            console.error("Weight trend error", e);
        }
    }
};

window.dashboard = dashboard;
