const onboarding = {
    currentStep: 1,
    totalSteps: 8,
    data: {
        name: '',
        age: 28,
        sex: 'male',
        height_cm: 172,
        weight_kg: 72,
        activity_level: 'moderate',
        goal: 'maintain',
        region: 'north',
        diet_type: 'vegetarian',
        weekly_budget_inr: 2500,
        allergies: '',
        food_dislikes: '',
        wake_time: '07:00',
        sleep_time: '23:00',
        exercise_time: '',
        meals_per_day: 4
    },

    init() {
        this.renderStep();
        document.getElementById('btn-next').onclick = () => this.nextStep();
        document.getElementById('btn-prev').onclick = () => this.prevStep();
    },

    async loadPreset(type) {
        app.showToast('Setting up sample profile...');
        let preset = {};
        if (type === 'north_veg') {
            preset = {
                name: 'Rahul Sharma',
                age: 29,
                sex: 'male',
                height_cm: 175,
                weight_kg: 74,
                activity_level: 'moderate',
                goal: 'lose_weight',
                region: 'north',
                diet_type: 'vegetarian',
                weekly_budget_inr: 2500,
                allergies: '',
                food_dislikes: '',
                wake_time: '06:30',
                sleep_time: '23:00',
                meals_per_day: 4
            };
        } else {
            preset = {
                name: 'Priya Nair',
                age: 27,
                sex: 'female',
                height_cm: 165,
                weight_kg: 60,
                activity_level: 'active',
                goal: 'maintain',
                region: 'south',
                diet_type: 'non_vegetarian',
                weekly_budget_inr: 3000,
                allergies: '',
                food_dislikes: '',
                wake_time: '06:00',
                sleep_time: '22:30',
                meals_per_day: 4
            };
        }

        try {
            const user = await api.createUser(preset);
            localStorage.setItem('ai_diet_user_id', user.id);
            app.state.userId = user.id;
            app.state.user = user;
            app.updateHeaderProfile();
            app.showToast(`Welcome ${user.name}! Profile activated.`, 'info');
            app.navigate('dashboard');
        } catch (e) {
            console.error('Preset error', e);
            app.showToast('Failed to create sample profile. Please fill manually.', 'error');
        }
    },

    updateProgress() {
        const pct = (this.currentStep / this.totalSteps) * 100;
        document.getElementById('onboarding-progress').style.width = `${pct}%`;
        document.getElementById('step-indicator').innerText = `Step ${this.currentStep} of ${this.totalSteps}`;
        const btnPrev = document.getElementById('btn-prev');
        const btnNext = document.getElementById('btn-next');
        if (this.currentStep === 1) btnPrev.classList.add('hidden');
        else btnPrev.classList.remove('hidden');
        btnNext.innerText = this.currentStep === this.totalSteps ? 'Generate My AI Diet Plan' : 'Continue →';
    },

    setVal(key, val) {
        this.data[key] = val;
        this.renderStep();
    },

    async nextStep() {
        // Collect current step data
        if (this.currentStep === 1) {
            const nameInput = document.getElementById('ob-name');
            if (nameInput && nameInput.value.trim()) {
                this.data.name = nameInput.value.trim();
            } else {
                app.showToast('Please enter your name', 'error');
                return;
            }
        } else if (this.currentStep === 2) {
            const ageInput = document.getElementById('ob-age');
            if (ageInput) this.data.age = parseInt(ageInput.value) || 28;
        } else if (this.currentStep === 3) {
            const h = document.getElementById('ob-height');
            const w = document.getElementById('ob-weight');
            if (h) this.data.height_cm = parseFloat(h.value) || 170;
            if (w) this.data.weight_kg = parseFloat(w.value) || 70;
        } else if (this.currentStep === 7) {
            const b = document.getElementById('ob-budget');
            if (b) this.data.weekly_budget_inr = parseInt(b.value) || 2000;
            const al = document.getElementById('ob-allergies');
            if (al) this.data.allergies = al.value.trim();
        }

        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            this.renderStep();
        } else {
            await this.finish();
        }
    },

    prevStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.renderStep();
        }
    },

    renderStep() {
        const container = document.getElementById('onboarding-step-content');
        container.innerHTML = '';
        this.updateProgress();

        let html = '';
        switch (this.currentStep) {
            case 1:
                html = `
                    <div style="text-align: center; margin-bottom: 20px;">
                        <span style="font-size: 2.5rem;">👋</span>
                        <h2 style="font-family: var(--font-serif); font-size: 1.8rem; color: var(--primary-900); margin-top: 8px;">What should we call you?</h2>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">Your personalized diet and nutrition assistant</p>
                    </div>
                    <div class="input-group" style="max-width: 400px; margin: 0 auto;">
                        <label class="field-label">Your Name</label>
                        <input type="text" id="ob-name" value="${this.data.name}" placeholder="e.g. Ananya, Vikram" autofocus>
                    </div>
                `;
                break;
            case 2:
                html = `
                    <h2 style="font-family: var(--font-serif); font-size: 1.6rem; color: var(--primary-900); margin-bottom: 16px;">Basic Profile</h2>
                    <div class="input-group mb-4">
                        <label class="field-label">Age (years)</label>
                        <input type="number" id="ob-age" value="${this.data.age}" min="12" max="100">
                    </div>
                    <label class="field-label">Biological Sex</label>
                    <div style="display: flex; gap: 1rem; margin-top: 8px;">
                        <div class="selectable-card ${this.data.sex === 'male' ? 'selected' : ''}" style="flex:1" onclick="onboarding.setVal('sex', 'male')">
                            <div style="font-size: 2.2rem;">👨</div>
                            <div style="font-weight: 700; margin-top: 4px;">Male</div>
                        </div>
                        <div class="selectable-card ${this.data.sex === 'female' ? 'selected' : ''}" style="flex:1" onclick="onboarding.setVal('sex', 'female')">
                            <div style="font-size: 2.2rem;">👩</div>
                            <div style="font-weight: 700; margin-top: 4px;">Female</div>
                        </div>
                    </div>
                `;
                break;
            case 3:
                html = `
                    <h2 style="font-family: var(--font-serif); font-size: 1.6rem; color: var(--primary-900); margin-bottom: 16px;">Body Dimensions</h2>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
                        <div class="input-group">
                            <label class="field-label">Height (cm)</label>
                            <input type="number" id="ob-height" value="${this.data.height_cm}" min="100" max="250" oninput="onboarding.updateBMIPreview()">
                        </div>
                        <div class="input-group">
                            <label class="field-label">Weight (kg)</label>
                            <input type="number" id="ob-weight" value="${this.data.weight_kg}" min="25" max="250" oninput="onboarding.updateBMIPreview()">
                        </div>
                    </div>
                    <div class="card" style="text-align: center; padding: 14px; background: var(--bg-subtle); margin-top: 12px;">
                        <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">Estimated BMI Status</span><br>
                        <span id="ob-bmi-value" style="font-size: 1.6rem; font-weight: 800; color: var(--primary-800);">--</span>
                    </div>
                `;
                setTimeout(() => this.updateBMIPreview(), 50);
                break;
            case 4:
                const acts = ['sedentary', 'light', 'moderate', 'active', 'very_active'];
                const actLabels = ['Sedentary (Desk job, little exercise)', 'Lightly Active (1-2 days workout/wk)', 'Moderate (3-5 days workout/wk)', 'Very Active (6-7 days intense sport)', 'Extra Active (Athlete / Heavy Labor)'];
                const actIcons = ['💻', '🚶', '🏃', '🏋️', '⚡'];
                html = `<h2 style="font-family: var(--font-serif); font-size: 1.6rem; color: var(--primary-900); margin-bottom: 14px;">Activity Level</h2>`;
                acts.forEach((a, i) => {
                    html += `
                        <div class="selectable-card ${this.data.activity_level === a ? 'selected' : ''}" onclick="onboarding.setVal('activity_level', '${a}')" style="display: flex; align-items: center; gap: 14px; text-align: left; padding: 12px 16px; margin-bottom: 8px;">
                            <span style="font-size: 1.6rem;">${actIcons[i]}</span>
                            <div>
                                <div style="font-weight: 700; font-size: 0.95rem;">${actLabels[i].split('(')[0]}</div>
                                <div style="font-size: 0.78rem; color: var(--text-muted);">${actLabels[i]}</div>
                            </div>
                        </div>
                    `;
                });
                break;
            case 5:
                const goals = [
                    { id: 'lose_weight', label: 'Lose Weight (Deficit)', icon: '📉', desc: 'Fat loss with high protein retention' },
                    { id: 'maintain', label: 'Maintain Weight (Health)', icon: '⚖️', desc: 'Energy balance and vitality' },
                    { id: 'gain_weight', label: 'Gain Muscle (Surplus)', icon: '📈', desc: 'Hypertrophy and lean muscle mass' }
                ];
                html = `<h2 style="font-family: var(--font-serif); font-size: 1.6rem; color: var(--primary-900); margin-bottom: 14px;">Your Primary Goal</h2>`;
                goals.forEach(g => {
                    html += `
                        <div class="selectable-card ${this.data.goal === g.id ? 'selected' : ''}" onclick="onboarding.setVal('goal', '${g.id}')" style="display: flex; align-items: center; gap: 14px; text-align: left; padding: 14px 18px; margin-bottom: 10px;">
                            <span style="font-size: 1.8rem;">${g.icon}</span>
                            <div>
                                <div style="font-weight: 700; font-size: 1rem;">${g.label}</div>
                                <div style="font-size: 0.8rem; color: var(--text-muted);">${g.desc}</div>
                            </div>
                        </div>
                    `;
                });
                break;
            case 6:
                const regions = [
                    { id: 'north', label: 'North Indian', desc: 'Roti, Dal, Paneer, Rajma, Curries' },
                    { id: 'south', label: 'South Indian', desc: 'Idli, Dosa, Sambar, Rasam, Rice' },
                    { id: 'east', label: 'East Indian', desc: 'Rice, Fish, Mustard gravies, Lentils' },
                    { id: 'west', label: 'West Indian', desc: 'Bhakri, Thepla, Dal Dhokli, Sprouts' },
                    { id: 'pan_india', label: 'Pan-Indian Mix', desc: 'Balanced blend from all cuisines' }
                ];
                html = `<h2 style="font-family: var(--font-serif); font-size: 1.6rem; color: var(--primary-900); margin-bottom: 14px;">Indian Regional Cuisine</h2>`;
                html += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px;">`;
                regions.forEach(r => {
                    html += `
                        <div class="selectable-card ${this.data.region === r.id ? 'selected' : ''}" onclick="onboarding.setVal('region', '${r.id}')" style="padding: 12px;">
                            <div style="font-weight: 700; font-size: 0.95rem;">${r.label}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">${r.desc}</div>
                        </div>
                    `;
                });
                html += `</div>`;
                html += `<label class="field-label">Dietary Preference</label>`;
                html += `<div style="display: flex; gap: 8px; margin-top: 6px;">
                    <div class="selectable-card ${this.data.diet_type === 'vegetarian' ? 'selected' : ''}" style="flex:1; padding: 10px;" onclick="onboarding.setVal('diet_type', 'vegetarian')">🥬 Veg</div>
                    <div class="selectable-card ${this.data.diet_type === 'non_vegetarian' ? 'selected' : ''}" style="flex:1; padding: 10px;" onclick="onboarding.setVal('diet_type', 'non_vegetarian')">🍗 Non-Veg</div>
                    <div class="selectable-card ${this.data.diet_type === 'vegan' ? 'selected' : ''}" style="flex:1; padding: 10px;" onclick="onboarding.setVal('diet_type', 'vegan')">🌱 Vegan</div>
                </div>`;
                break;
            case 7:
                html = `
                    <h2 style="font-family: var(--font-serif); font-size: 1.6rem; color: var(--primary-900); margin-bottom: 14px;">Budget & Allergies</h2>
                    <div class="input-group mb-4">
                        <label class="field-label">Weekly Food Budget (₹ INR)</label>
                        <input type="number" id="ob-budget" value="${this.data.weekly_budget_inr}" min="500" max="25000" step="100">
                    </div>
                    <div class="input-group">
                        <label class="field-label">Allergies (comma separated, optional)</label>
                        <input type="text" id="ob-allergies" value="${this.data.allergies}" placeholder="e.g. peanuts, lactose, gluten">
                    </div>
                `;
                break;
            case 8:
                html = `
                    <div style="text-align: center; padding: 10px 0;">
                        <span style="font-size: 3rem;">✨</span>
                        <h2 style="font-family: var(--font-serif); font-size: 2rem; color: var(--primary-900); margin: 8px 0;">You're All Set!</h2>
                        <p style="color: var(--text-muted); font-size: 0.95rem; max-width: 460px; margin: 0 auto 20px;">
                            NutriCalc will calculate your exact BMR, target calories, macro splits, and generate regional Indian meal plans for ${this.data.name || 'you'}.
                        </p>
                        <div class="card" style="text-align: left; background: var(--bg-subtle); padding: 16px;">
                            <div style="font-size: 0.88rem; margin-bottom: 6px;">📍 <strong>Region:</strong> ${this.data.region.toUpperCase()}</div>
                            <div style="font-size: 0.88rem; margin-bottom: 6px;">🥗 <strong>Diet:</strong> ${this.data.diet_type.replace('_', '-')}</div>
                            <div style="font-size: 0.88rem;">🎯 <strong>Goal:</strong> ${this.data.goal.replace('_', ' ')}</div>
                        </div>
                    </div>
                `;
                break;
        }

        container.innerHTML = html;
    },

    updateBMIPreview() {
        const hEl = document.getElementById('ob-height');
        const wEl = document.getElementById('ob-weight');
        const out = document.getElementById('ob-bmi-value');
        if (!hEl || !wEl || !out) return;

        const h = parseFloat(hEl.value);
        const w = parseFloat(wEl.value);
        if (h && w && h > 50 && w > 20) {
            const bmi = w / ((h / 100) * (h / 100));
            let status = 'Normal';
            if (bmi < 18.5) status = 'Underweight';
            else if (bmi >= 25 && bmi < 30) status = 'Overweight';
            else if (bmi >= 30) status = 'Obese';
            out.innerText = `${bmi.toFixed(1)} (${status})`;
        }
    },

    async finish() {
        app.showToast('Generating personalized diet profile...');
        try {
            const user = await api.createUser(this.data);
            localStorage.setItem('ai_diet_user_id', user.id);
            app.state.userId = user.id;
            app.state.user = user;
            app.updateHeaderProfile();
            app.showToast('Profile created successfully!', 'info');
            app.navigate('dashboard');
        } catch (e) {
            console.error('Create user error', e);
            app.showToast('Failed to create profile: ' + e.message, 'error');
        }
    }
};

window.onboarding = onboarding;
