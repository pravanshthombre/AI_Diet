const app = {
    state: {
        userId: localStorage.getItem('ai_diet_user_id'),
        user: null,
        supabaseUser: null,
        currentView: null
    },

    async init() {
        this.setupRouter();
        this.setupToast();

        // Initialize Supabase Auth Manager
        if (typeof authManager !== 'undefined') {
            authManager.init();
        }

        // Initial route check
        if (this.state.userId) {
            await this.loadUser();
            const hash = window.location.hash.replace('#', '') || 'dashboard';
            if (hash === 'auth') {
                this.navigate('dashboard');
            } else {
                this.navigate(hash);
            }
        } else {
            const hash = window.location.hash.replace('#', '');
            if (hash === 'foods') {
                this.navigate(hash);
            } else {
                this.navigate('onboarding');
            }
        }
    },

    async loadUser() {
        if (!this.state.userId) return;
        try {
            this.state.user = await api.getUser();
            this.updateHeaderProfile();
        } catch (e) {
            console.error('Failed to load user', e);
            localStorage.removeItem('ai_diet_user_id');
            this.state.userId = null;
            this.state.user = null;
            this.updateHeaderProfile();
            this.navigate('onboarding');
        }
    },

    updateHeaderProfile() {
        const badgeContainer = document.getElementById('user-badge-container');
        const badgeAvatar = document.getElementById('badge-avatar');
        const badgeUsername = document.getElementById('badge-username');
        const restartBtn = document.getElementById('btn-restart-onboarding');

        const currentUser = this.state.user;

        if (currentUser) {
            if (badgeContainer) badgeContainer.classList.remove('hidden');
            if (restartBtn) restartBtn.classList.remove('hidden');
            
            const name = this.state.user?.name || 'User';
            if (badgeAvatar) badgeAvatar.innerText = name.charAt(0).toUpperCase();
            if (badgeUsername) badgeUsername.innerText = name;
        } else {
            if (badgeContainer) badgeContainer.classList.add('hidden');
            if (restartBtn) restartBtn.classList.add('hidden');
        }
    },

    async logout() {
        localStorage.removeItem('ai_diet_user_id');
        this.state.userId = null;
        this.state.user = null;
        this.updateHeaderProfile();
        this.navigate('onboarding');
    },

    resetUser() {
        localStorage.removeItem('ai_diet_user_id');
        this.state.userId = null;
        this.state.user = null;
        this.updateHeaderProfile();
        this.navigate('onboarding');
        this.showToast('Profile reset. Choose or create a new profile.');
    },

    openProfileModal() {
        const modal = document.getElementById('modal-profile-switch');
        if (!modal) return;

        // Populate current profile info
        const avatar = document.getElementById('profile-modal-avatar');
        const nameEl = document.getElementById('profile-modal-name');
        const detailsEl = document.getElementById('profile-modal-details');
        const emailEl = document.getElementById('profile-modal-email');

        const currentUser = this.state.user || this.state.supabaseUser;

        if (currentUser) {
            const name = this.state.user?.name || this.state.supabaseUser?.user_metadata?.full_name || 'User';
            const email = this.state.user?.email || this.state.supabaseUser?.email || '';
            if (avatar) avatar.innerText = name.charAt(0).toUpperCase();
            if (nameEl) nameEl.innerText = name;
            if (emailEl) emailEl.innerText = email ? `📧 ${email}` : '';
            
            const parts = [];
            if (this.state.user?.age) parts.push(`${this.state.user.age} yrs`);
            if (this.state.user?.sex) parts.push(this.state.user.sex.charAt(0).toUpperCase() + this.state.user.sex.slice(1));
            if (this.state.user?.region) parts.push(this.state.user.region.charAt(0).toUpperCase() + this.state.user.region.slice(1) + ' Indian');
            if (this.state.user?.diet_type) parts.push(this.state.user.diet_type.replace('_', '-'));
            if (detailsEl) detailsEl.innerText = parts.join(' · ') || (email ? 'Supabase Auth Active' : 'Profile active');
        } else {
            if (avatar) avatar.innerText = '?';
            if (nameEl) nameEl.innerText = 'No Profile';
            if (emailEl) emailEl.innerText = '';
            if (detailsEl) detailsEl.innerText = 'Create an account or sign in to get started';
        }

        modal.classList.remove('hidden');
        modal.onclick = (e) => {
            if (e.target === modal) this.closeProfileModal();
        };
    },

    closeProfileModal() {
        const modal = document.getElementById('modal-profile-switch');
        if (modal) modal.classList.add('hidden');
    },

    resumeProfile() {
        this.closeProfileModal();
        if (this.state.userId && this.state.currentView) {
            this.navigate(this.state.currentView);
        } else if (this.state.userId) {
            this.navigate('dashboard');
        }
        this.showToast('Welcome back! Continuing your profile.');
    },

    restartProfile() {
        this.closeProfileModal();
        // Clear current user but data remains saved on the server
        localStorage.removeItem('ai_diet_user_id');
        this.state.userId = null;
        this.state.user = null;
        this.updateHeaderProfile();

        // Reset onboarding form to step 1
        if (typeof onboarding !== 'undefined') {
            onboarding.currentStep = 1;
            onboarding.data = {
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
            };
        }

        this.navigate('onboarding');
        this.showToast('Starting fresh! Fill in your new profile details.');
    },

    openApiModal() {
        const modal = document.getElementById('modal-api-config');
        const input = document.getElementById('input-api-url');
        const status = document.getElementById('api-connection-status');
        if (input) input.value = localStorage.getItem('NUTRICALC_API_BASE') || '';
        if (status) status.innerHTML = `Current Base: <code>${api.getBaseUrl() || '(Relative root)'}</code>`;
        if (modal) {
            modal.classList.remove('hidden');
            modal.onclick = (e) => {
                if (e.target === modal) this.closeApiModal();
            };
        }
    },

    closeApiModal() {
        const modal = document.getElementById('modal-api-config');
        if (modal) modal.classList.add('hidden');
    },

    async testApiServer() {
        const input = document.getElementById('input-api-url');
        const status = document.getElementById('api-connection-status');
        const url = input ? input.value.trim() : null;
        if (status) status.innerHTML = `Testing connection to <code>${url || api.getBaseUrl()}</code>...`;
        const ok = await api.testConnection(url);
        if (status) {
            status.innerHTML = ok 
                ? `<span style="color: #059669; font-weight: 700;">🟢 Connected successfully!</span>`
                : `<span style="color: #dc2626; font-weight: 700;">🔴 Could not reach server. Verify URL & ensure backend is live.</span>`;
        }
    },

    async saveApiServer() {
        const input = document.getElementById('input-api-url');
        const url = input ? input.value.trim() : '';
        api.setBaseUrl(url);
        this.showToast('Backend API URL saved and connected!', 'success');
        this.closeApiModal();
        if (this.state.userId) {
            await this.loadUser();
        } else {
            this.navigate('onboarding');
        }
        if (this.state.currentView) {
            this.navigate(this.state.currentView);
        }
    },



    setupRouter() {
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.replace('#', '');
            if (hash) this.showView(hash);
        });

        // Desktop nav listeners
        document.querySelectorAll('.desktop-nav .nav-link').forEach(item => {
            item.addEventListener('click', (e) => {
                const target = e.currentTarget.dataset.target;
                this.navigate(target);
            });
        });

        // Mobile Bottom nav listeners
        document.querySelectorAll('.bottom-nav .nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const target = e.currentTarget.dataset.target;
                this.navigate(target);
            });
        });
    },

    navigate(viewId) {
        window.location.hash = viewId;
        this.showView(viewId);
    },

    showView(viewId) {
        // Fallback for unauthenticated users
        if (!this.state.userId && viewId !== 'onboarding' && viewId !== 'foods') {
            viewId = 'onboarding';
            window.location.hash = 'onboarding';
        }

        // Hide all views
        document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
        
        // Update nav state
        const bottomNav = document.getElementById('bottom-nav');
        if (viewId === 'onboarding') {
            if (bottomNav) bottomNav.classList.add('hidden');
        } else {
            if (bottomNav) bottomNav.classList.remove('hidden');
        }

        // Update active class on both nav bars
        document.querySelectorAll('.desktop-nav .nav-link').forEach(nav => {
            if (nav.dataset.target === viewId) nav.classList.add('active');
            else nav.classList.remove('active');
        });

        document.querySelectorAll('.bottom-nav .nav-item').forEach(nav => {
            if (nav.dataset.target === viewId) nav.classList.add('active');
            else nav.classList.remove('active');
        });

        // Show target view
        const viewEl = document.getElementById(viewId);
        if (viewEl) {
            viewEl.classList.remove('hidden');
            this.state.currentView = viewId;
            
            // Trigger view-specific init
            const views = {
                onboarding: typeof onboarding !== 'undefined' ? onboarding : null,
                dashboard: typeof dashboard !== 'undefined' ? dashboard : null,
                mealplan: typeof mealplan !== 'undefined' ? mealplan : null,
                tracking: typeof tracking !== 'undefined' ? tracking : null,
                foods: typeof foodsExplorer !== 'undefined' ? foodsExplorer : null,
                chat: typeof chat !== 'undefined' ? chat : null
            };
            
            if (views[viewId] && typeof views[viewId].init === 'function') {
                views[viewId].init();
            }
        }
    },

    setupToast() {
        this.toastContainer = document.getElementById('toast-container');
    },

    showToast(message, type = 'info') {
        if (!this.toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerText = message;
        this.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

window.app = app;
