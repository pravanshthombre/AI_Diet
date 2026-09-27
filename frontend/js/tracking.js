const tracking = {
    waterAmount: 0,
    waterGoalMl: 2500,

    async init() {
        if (!app.state.user && app.state.userId) {
            await app.loadUser();
        }
        if (!app.state.user) return;
        const user = app.state.user;

        try {
            const waterTarget = await api.request(`/calculators/water-intake?weight_kg=${user.weight_kg}&activity_level=${user.activity_level}&climate=moderate`);
            this.waterGoalMl = (waterTarget.liters_per_day || 2.5) * 1000;

            const today = new Date().toISOString().split('T')[0];
            const track = await api.getTracking(today);
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

            // Initialize AI Food Scanner
            this.initScanner();
        } catch (e) {
            console.error('Tracking init error', e);
        }
    },

    updateWaterUI() {
        const glasses = Math.floor(this.waterAmount / 250);
        const targetGlasses = Math.floor(this.waterGoalMl / 250) || 8;
        
        const countEl = document.getElementById('water-count');
        if (countEl) {
            countEl.innerText = `${glasses} / ${targetGlasses} glasses (${this.waterAmount} / ${this.waterGoalMl} ml)`;
        }
        
        let pct = Math.min(100, (this.waterAmount / this.waterGoalMl) * 100);
        const fillEl = document.getElementById('water-fill-level');
        if (fillEl) fillEl.style.width = `${pct}%`;

        // Calculate and update the time reminder (assuming 16 waking hours in a 24-hour period)
        const wakingHours = 16;
        const intervalHours = wakingHours / targetGlasses;
        const hrs = Math.floor(intervalHours);
        const mins = Math.round((intervalHours - hrs) * 60);
        
        const reminderEl = document.getElementById('water-reminder');
        if (reminderEl) {
            if (glasses >= targetGlasses) {
                reminderEl.innerHTML = `🌟 Daily goal met! Great job staying hydrated.`;
                reminderEl.style.color = '#10b981';
            } else {
                const timeString = hrs > 0 
                    ? `${hrs}h ${mins > 0 ? mins + 'm' : ''}`.trim()
                    : `${mins} mins`;
                reminderEl.innerHTML = `⏰ Tip: Drink 1 glass (250ml) every <strong>${timeString}</strong>`;
                reminderEl.style.color = 'var(--primary-600)';
            }
        }
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

