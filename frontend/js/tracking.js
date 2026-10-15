const tracking = {
    waterAmount: 0,
    waterGoalMl: 2500,

    async ensureUser() {
        if (!app.state.user && app.state.userId) {
            await app.loadUser();
        }
        if (!app.state.userId) {
            try {
                const u = await api.getUser();
                if (u && u.id) {
                    app.state.user = u;
                    app.state.userId = u.id;
                    localStorage.setItem('ai_diet_user_id', u.id);
                    app.updateHeaderProfile();
                }
            } catch (e) {
                console.warn('Could not auto-load user profile:', e);
            }
        }
        if (!app.state.userId) {
            app.state.userId = 1;
            localStorage.setItem('ai_diet_user_id', '1');
        }
        return app.state.user;
    },

    async init() {
        // Bindings first so buttons always respond
        const addWaterBtn = document.getElementById('btn-add-water');
        if (addWaterBtn) addWaterBtn.onclick = () => this.addOneGlass();
        const logWtBtn = document.getElementById('btn-log-weight');
        if (logWtBtn) logWtBtn.onclick = () => this.logWeight();
        const logMealBtn = document.getElementById('btn-log-meal');
        if (logMealBtn) logMealBtn.onclick = () => this.logMeal();
        const foodInput = document.getElementById('input-log-food');
        if (foodInput) foodInput.addEventListener('input', () => this.searchFoods(foodInput.value));

        await this.ensureUser();
        const user = app.state.user;

        try {
            if (user && user.weight_kg) {
                try {
                    const waterTarget = await api.request(`/calculators/water-intake?weight_kg=${user.weight_kg}&activity_level=${user.activity_level}&climate=moderate`);
                    const rawLiters = (waterTarget && waterTarget.liters_per_day) ? waterTarget.liters_per_day : 2.5;
                    const calculatedGlasses = Math.max(1, Math.round((rawLiters * 1000) / 250) || 8);
                    this.waterGoalMl = calculatedGlasses * 250;
                } catch (calcErr) {
                    this.waterGoalMl = 2250;
                }
            } else {
                this.waterGoalMl = 2500;
            }

            const today = new Date().toISOString().split('T')[0];
            try {
                const track = await api.getTracking(today);
                if (track && typeof track.actual_water_ml === 'number') {
                    this.waterAmount = track.actual_water_ml;
                    localStorage.setItem('ai_diet_today_water_' + today, this.waterAmount);
                }
            } catch (netErr) {
                const saved = localStorage.getItem('ai_diet_today_water_' + today);
                if (saved !== null) {
                    this.waterAmount = Number(saved) || 0;
                }
            }
            this.updateWaterUI();

            this.initScanner();
        } catch (e) {
            console.error('Tracking init error', e);
            this.updateWaterUI();
        }
    },

    updateWaterUI(justRefilledIndex = null) {
        const glasses = Math.max(0, Math.floor(this.waterAmount / 250));
        const targetGlasses = Math.max(1, Math.round(this.waterGoalMl / 250) || 8);
        const targetMl = targetGlasses * 250;
        const currentMl = Math.round(this.waterAmount);
        
        const countEl = document.getElementById('water-count');
        if (countEl) {
            countEl.innerText = `${glasses} / ${targetGlasses} glasses (${currentMl} / ${targetMl} ml)`;
        }

        const pct = Math.min(100, Math.round((currentMl / targetMl) * 100)) || 0;
        const pctEl = document.getElementById('water-pct-label');
        if (pctEl) {
            pctEl.innerText = `${pct}%`;
        }
        
        const badgeEl = document.getElementById('water-refilled-badge');
        if (badgeEl) {
            badgeEl.innerText = `${glasses} / ${targetGlasses} Refilled`;
            if (glasses >= targetGlasses) {
                badgeEl.style.background = '#dcfce7';
                badgeEl.style.color = '#15803d';
            } else {
                badgeEl.style.background = '#e0f2fe';
                badgeEl.style.color = '#0284c7';
            }
        }

        const waterBadge = document.getElementById('water-badge');
        if (waterBadge) {
            if (glasses >= targetGlasses) {
                waterBadge.style.background = '#dcfce7';
                waterBadge.style.color = '#15803d';
                waterBadge.innerText = '🎯 Goal Met!';
            } else {
                waterBadge.style.background = '#e0f2fe';
                waterBadge.style.color = '#0284c7';
                waterBadge.innerText = 'Daily Target';
            }
        }

        const fillEl = document.getElementById('water-fill-level');
        if (fillEl) fillEl.style.width = `${pct}%`;

        // Update goal pin mark on progress bar
        const goalPin = document.getElementById('water-goal-pin');
        const goalPinText = document.getElementById('water-goal-pin-text');
        if (goalPin) {
            if (glasses >= targetGlasses) {
                goalPin.classList.add('reached');
                if (goalPinText) goalPinText.innerText = 'Goal Met! 🌟';
            } else {
                goalPin.classList.remove('reached');
                if (goalPinText) goalPinText.innerText = 'Daily Goal';
            }
        }

        // Render tick milestones along the progress bar for every glass
        const ticksContainer = document.getElementById('water-bar-ticks');
        if (ticksContainer) {
            let ticksHtml = '';
            for (let t = 1; t < targetGlasses; t++) {
                ticksHtml += `<div class="water-bar-tick" title="Glass ${t} (${t * 250} ml)"></div>`;
            }
            ticksContainer.innerHTML = ticksHtml;
        }

        // Render the interactive glasses refilled diagram
        this.renderGlassesGrid(glasses, targetGlasses, justRefilledIndex);

        // Calculate and update the time reminder (assuming 16 waking hours)
        const wakingHours = 16;
        const intervalHours = wakingHours / targetGlasses;
        const hrs = Math.floor(intervalHours);
        const mins = Math.round((intervalHours - hrs) * 60);
        
        const reminderEl = document.getElementById('water-reminder');
        if (reminderEl) {
            if (glasses >= targetGlasses) {
                reminderEl.innerHTML = `🌟 Daily hydration goal met! Outstanding job keeping your body refreshed!`;
                reminderEl.style.color = '#10b981';
            } else {
                const timeString = hrs > 0 
                    ? `${hrs}h ${mins > 0 ? mins + 'm' : ''}`.trim()
                    : `${mins} mins`;
                reminderEl.innerHTML = `⏰ Tip: Drink 1 glass (250ml) every <strong>${timeString}</strong> to reach your daily goal`;
                reminderEl.style.color = 'var(--primary-600)';
            }
        }
    },

    getGlassDiagramSVG(isFilled, glassNumber) {
        const uid = 'glass-diag-' + glassNumber;
        const liquidY = isFilled ? 14 : 58;
        const surfaceOpacity = isFilled ? 0.95 : 0;
        
        return `
        <svg viewBox="0 0 54 72" class="glass-diagram-svg ${isFilled ? 'filled' : 'empty'}" width="46" height="62" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="${uid}-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#38bdf8"/>
                    <stop offset="55%" stop-color="#0284c7"/>
                    <stop offset="100%" stop-color="#0369a1"/>
                </linearGradient>
                <clipPath id="${uid}-clip">
                    <path d="M 8 9 L 13 60 Q 14 65 19 65 L 35 65 Q 40 65 41 60 L 46 9 Z"/>
                </clipPath>
            </defs>
            <!-- Glass Shadow Base -->
            <ellipse cx="27" cy="67" rx="14" ry="2.5" fill="rgba(2, 132, 199, 0.12)"/>
            <!-- Glass Back / Body -->
            <path d="M 8 9 L 13 60 Q 14 65 19 65 L 35 65 Q 40 65 41 60 L 46 9 Z" class="glass-wall-bg"/>
            <!-- Water Liquid (Clipped to interior) -->
            <g clip-path="url(#${uid}-clip)">
                <rect class="glass-liquid-rect" x="0" y="${liquidY}" width="54" height="65" fill="url(#${uid}-grad)"/>
                <ellipse class="glass-liquid-surface" cx="27" cy="${liquidY}" rx="17" ry="3.5" fill="#bae6fd" opacity="${surfaceOpacity}"/>
                ${isFilled ? `
                <circle cx="20" cy="46" r="1.5" fill="rgba(255,255,255,0.7)"/>
                <circle cx="33" cy="36" r="2.2" fill="rgba(255,255,255,0.6)"/>
                <circle cx="26" cy="24" r="1.8" fill="rgba(255,255,255,0.8)"/>
                ` : ''}
            </g>
            <!-- Glass Stroke -->
            <path d="M 8 9 L 13 60 Q 14 65 19 65 L 35 65 Q 40 65 41 60 L 46 9 Z" class="glass-wall-stroke" fill="none"/>
            <!-- Glass Rim -->
            <ellipse cx="27" cy="9" rx="19" ry="3.8" class="glass-rim"/>
            <!-- Glass Sheen Highlights -->
            <path d="M 12 15 L 15 56" stroke="rgba(255,255,255,0.85)" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M 42 15 L 39 56" stroke="rgba(255,255,255,0.25)" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        `;
    },

    renderGlassesGrid(currentGlasses, targetGlasses, justRefilledIndex = null) {
        const grid = document.getElementById('water-glasses-grid');
        if (!grid) return;

        // Render at least targetGlasses, or more if user exceeded their goal
        const totalToRender = Math.max(targetGlasses, currentGlasses);
        let html = '';

        for (let i = 1; i <= totalToRender; i++) {
            const isFilled = i <= currentGlasses;
            const isJustRefilled = i === justRefilledIndex;
            let glassClass = isFilled ? 'water-glass-card filled' : 'water-glass-card empty';
            if (isJustRefilled) glassClass += ' just-refilled';

            const statusBadge = isFilled 
                ? '<span class="glass-status-badge refilled">✓ Refilled</span>' 
                : '<span class="glass-status-badge empty">+250 ml</span>';
            const tooltip = isFilled 
                ? `Glass ${i} (Refilled) · Click to remove` 
                : `Glass ${i} · Click to refill 1 glass`;

            html += `
                <div class="${glassClass}" onclick="tracking.clickGlass(${i})" title="${tooltip}">
                    ${this.getGlassDiagramSVG(isFilled, i)}
                    <div class="glass-label">Glass ${i}</div>
                    ${statusBadge}
                </div>
            `;
        }

        grid.innerHTML = html;
    },

    async addOneGlass() {
        // Adds strictly only one glass (250 ml)
        await this.logWater(250);
    },

    async clickGlass(glassNumber) {
        const currentGlasses = Math.floor(this.waterAmount / 250);
        if (glassNumber <= currentGlasses) {
            // Clicking any refilled glass removes only one glass
            await this.undoGlass();
        } else {
            // Clicking an empty glass adds only one glass
            await this.addOneGlass();
        }
    },

    async undoGlass() {
        if (this.waterAmount <= 0) {
            app.showToast("No water logged yet today to remove", "info");
            return;
        }
        await this.logWater(-250);
    },

    async resetWater() {
        if (!confirm("Are you sure you want to reset today's water intake to 0 ml?")) return;
        const today = new Date().toISOString().split('T')[0];
        this.waterAmount = 0;
        this.updateWaterUI();
        try {
            localStorage.setItem('ai_diet_today_water_' + today, '0');
        } catch (e) {}

        if (window.dashboard && typeof dashboard.loadTodayProgress === 'function') {
            dashboard.loadTodayProgress(app.state.user);
        }
        app.showToast("Water tracker reset to 0 ml");

        try {
            await api.resetWater();
        } catch (e) {
            console.warn("Backend reset water notice:", e);
        }
    },

    async logWater(amount) {
        await this.ensureUser();
        const today = new Date().toISOString().split('T')[0];
        const previousGlasses = Math.floor(this.waterAmount / 250);
        const targetGlasses = Math.max(1, Math.round(this.waterGoalMl / 250) || 8);

        // Optimistic UI update: immediately update waterAmount and UI
        this.waterAmount = Math.max(0, this.waterAmount + amount);
        const newGlasses = Math.floor(this.waterAmount / 250);
        const justRefilledIndex = (amount > 0 && newGlasses > previousGlasses) ? newGlasses : null;

        this.updateWaterUI(justRefilledIndex);
        try {
            localStorage.setItem('ai_diet_today_water_' + today, String(this.waterAmount));
        } catch (e) {}

        // Keep dashboard synchronized
        if (window.dashboard && typeof dashboard.loadTodayProgress === 'function') {
            dashboard.loadTodayProgress(app.state.user);
        }

        // Informative toasts
        if (amount === 250) {
            if (newGlasses >= targetGlasses && previousGlasses < targetGlasses) {
                app.showToast(`🎉 Goal achieved! ${newGlasses}/${targetGlasses} glasses refilled today! 💧`);
            } else {
                app.showToast(`Logged +1 glass (250ml)! Glass ${newGlasses} refilled. 💧`);
            }
        } else if (amount > 0) {
            app.showToast(`Logged +${amount}ml water! Stay hydrated. 💧`);
        } else if (amount < 0) {
            app.showToast(`Removed 1 glass (${Math.abs(amount)}ml) water.`);
        }

        // Persist to backend and reconcile if needed
        try {
            const result = await api.logWater(amount);
            if (result && typeof result.total_today_ml === 'number') {
                this.waterAmount = result.total_today_ml;
                this.updateWaterUI();
                try {
                    localStorage.setItem('ai_diet_today_water_' + today, String(this.waterAmount));
                } catch (e) {}
            }
        } catch (e) {
            console.warn('Backend sync failed, saved locally:', e);
        }
    },

    async logWeight() {
        if (!app.state.userId) {
            app.showToast('Please log in first to log weight', 'error');
            return;
        }
        const input = document.getElementById('input-log-weight');
        const val = parseFloat(input.value);
        if (!val || val < 20 || val > 300) {
            app.showToast('Please enter a valid weight between 20-300 kg', 'error');
            return;
        }
        try {
            await api.logWeight(val);
            app.showToast(`Weight updated to ${val} kg!`);
            input.value = '';
            if (app.state.user) {
                app.state.user.weight_kg = val;
            }
            if (window.dashboard && typeof dashboard.init === 'function') {
                dashboard.init();
            }
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
        if (!app.state.userId) {
            app.showToast('Please log in first to log meals', 'error');
            return;
        }
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
    },

    // ═══════════════════════════════════════════════════════
    // VISION: AI Food Scanner & IFCT Calibration
    // ═══════════════════════════════════════════════════════

    _visionResult: null,
    _calibrationData: null,
    _currentImageDataUrl: null,

    initScanner() {
        const cameraInput = document.getElementById('camera-food-input');
        const uploadInput = document.getElementById('upload-food-input');
        if (cameraInput) cameraInput.addEventListener('change', (e) => this.handleFoodImage(e));
        if (uploadInput) uploadInput.addEventListener('change', (e) => this.handleFoodImage(e));
    },

    async handleFoodImage(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Show preview
        const preview = document.getElementById('scanner-preview');
        const previewImg = document.getElementById('scanner-preview-img');
        const statusEl = document.getElementById('scanner-status');
        preview.classList.remove('hidden');
        statusEl.innerHTML = '<div class="scanner-spinner"></div><span>Analyzing plate with AI...</span>';

        // Read as data URL for preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            this._currentImageDataUrl = e.target.result;
        };
        reader.readAsDataURL(file);

        // Send to backend
        try {
            const formData = new FormData();
            formData.append('image', file);

            app.showToast('🔍 Analyzing food image...', 'info');
            const result = await api.analyzeFoodImage(formData);
            this._visionResult = result;

            statusEl.innerHTML = `<span style="color: var(--primary-700); font-weight: 700;">✅ Detected: ${result.detected_dish} (${Math.round(result.confidence * 100)}% confidence)</span>`;

            // Open calibration modal
            this.openCalibrationModal(result);
        } catch (err) {
            console.error('Vision analysis error:', err);
            statusEl.innerHTML = `<span style="color: var(--accent-coral); font-weight: 600;">❌ ${err.message || 'Analysis failed'}</span>`;
            app.showToast('Food analysis failed: ' + err.message, 'error');
        }

        // Reset file input so same file can be re-selected
        event.target.value = '';
    },

    openCalibrationModal(result) {
        const modal = document.getElementById('modal-food-calibration');
        if (!modal) return;

        // Set detected food info
        const nameEl = document.getElementById('calibration-food-name');
        const confEl = document.getElementById('calibration-confidence');
        const srcEl = document.getElementById('calibration-source');
        const imgEl = document.getElementById('calibration-food-img');

        nameEl.textContent = result.detected_dish;
        confEl.textContent = `${Math.round(result.confidence * 100)}% confidence`;
        confEl.style.background = result.confidence >= 0.9 ? '#dcfce7' : result.confidence >= 0.8 ? '#fef9c3' : '#fee2e2';
        confEl.style.color = result.confidence >= 0.9 ? '#166534' : result.confidence >= 0.8 ? '#854d0e' : '#991b1b';
        srcEl.textContent = `Source: ${result.detection_source.replace(/_/g, ' ')}`;

        if (this._currentImageDataUrl) {
            imgEl.src = this._currentImageDataUrl;
        }

        // Set portion slider to estimated
        const portionSlider = document.getElementById('calibration-portion');
        const portionVal = document.getElementById('calibration-portion-val');
        portionSlider.value = result.estimated_portion_grams || 150;
        portionVal.textContent = `${portionSlider.value}g`;

        // Reset prep style
        document.getElementById('calibration-prep').value = 'homestyle_sauteed';

        // Render alternatives
        const altContainer = document.getElementById('calibration-alternatives');
        altContainer.innerHTML = '';
        if (result.alternatives && result.alternatives.length > 0) {
            altContainer.innerHTML = '<p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;">Or did you mean:</p>' +
                result.alternatives.map(a =>
                    `<button class="chip alt-chip" onclick="tracking.switchToAlternative(${a.id}, '${a.name.replace(/'/g, "\\'")}')">${a.name} (${a.calories} kcal)</button>`
                ).join('');
        }

        // Show modal
        modal.classList.remove('hidden');

        // Initial calibration
        this.recalibrateLive();
    },

    closeCalibrationModal() {
        const modal = document.getElementById('modal-food-calibration');
        if (modal) modal.classList.add('hidden');
    },

    async switchToAlternative(foodId, foodName) {
        if (this._visionResult && this._visionResult.primary_match) {
            this._visionResult.primary_match.id = foodId;
            this._visionResult.primary_match.name = foodName;
            this._visionResult.detected_dish = foodName;
            document.getElementById('calibration-food-name').textContent = foodName;
            this.recalibrateLive();
        }
    },

    setPortionPreset(grams) {
        const slider = document.getElementById('calibration-portion');
        slider.value = grams;
        document.getElementById('calibration-portion-val').textContent = `${grams}g`;
        this.recalibrateLive();
    },

    async recalibrateLive() {
        if (!this._visionResult || !this._visionResult.primary_match) return;

        const portionGrams = parseFloat(document.getElementById('calibration-portion').value);
        const prepStyle = document.getElementById('calibration-prep').value;
        document.getElementById('calibration-portion-val').textContent = `${portionGrams}g`;

        const foodId = this._visionResult.primary_match.id;
        if (!foodId) {
            // Use client-side estimation from baseline
            const base = this._visionResult.primary_match.baseline_ifct;
            const scale = portionGrams / 150;
            document.getElementById('cal-live-val').textContent = Math.round(base.calories * scale);
            document.getElementById('pro-live-val').textContent = Math.round(base.protein_g * scale) + 'g';
            document.getElementById('carb-live-val').textContent = Math.round(base.carbs_g * scale) + 'g';
            document.getElementById('fat-live-val').textContent = Math.round(base.fat_g * scale) + 'g';
            return;
        }

        try {
            const result = await api.calibrateNutrition({
                food_id: foodId,
                portion_grams: portionGrams,
                prep_style: prepStyle,
                additions: []
            });
            this._calibrationData = result;

            // Update live macros
            document.getElementById('cal-live-val').textContent = Math.round(result.calibrated.calories);
            document.getElementById('pro-live-val').textContent = result.calibrated.protein_g + 'g';
            document.getElementById('carb-live-val').textContent = result.calibrated.carbs_g + 'g';
            document.getElementById('fat-live-val').textContent = result.calibrated.fat_g + 'g';

            // Variance
            const varianceEl = document.getElementById('calibration-variance');
            const delta = result.variance.calorie_delta;
            if (Math.abs(delta) > 5) {
                varianceEl.innerHTML = `<span style="color: ${delta > 0 ? '#dc2626' : '#16a34a'}; font-weight: 600;">${delta > 0 ? '▲' : '▼'} ${result.variance.explanation}</span>`;
            } else {
                varianceEl.innerHTML = '<span style="color: var(--text-muted);">≈ Matches IFCT baseline</span>';
            }
        } catch (err) {
            console.error('Calibration error:', err);
        }
    },

    async logCalibratedMeal() {
        if (!this._visionResult || !this._visionResult.primary_match) {
            app.showToast('No food detected to log', 'error');
            return;
        }

        const foodId = this._visionResult.primary_match.id;
        const mealSlot = document.getElementById('calibration-meal-slot').value;
        const portionGrams = parseFloat(document.getElementById('calibration-portion').value);
        const servings = portionGrams / 150;  // Scale relative to standard serving

        if (!foodId) {
            app.showToast('Could not match food to database', 'error');
            return;
        }

        try {
            await api.logMeal(parseInt(foodId), mealSlot, Math.round(servings * 10) / 10);
            const cal = this._calibrationData ? Math.round(this._calibrationData.calibrated.calories) : '?';
            app.showToast(`✅ Logged ${this._visionResult.detected_dish} (${cal} kcal) to ${mealSlot}!`);
            this.closeCalibrationModal();

            // Clear scanner preview
            const preview = document.getElementById('scanner-preview');
            if (preview) preview.classList.add('hidden');
        } catch (err) {
            app.showToast('Failed to log meal: ' + err.message, 'error');
        }
    }
};

window.tracking = tracking;

