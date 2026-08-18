const app = {
    state: {
        userId: localStorage.getItem('ai_diet_user_id'),
        user: null,
        currentView: null
    },

    async init() {
        this.setupRouter();
        this.setupToast();
        
        // Initial route check
        if (!this.state.userId) {
            this.navigate('onboarding');
        } else {
            await this.loadUser();
            const hash = window.location.hash.replace('#', '') || 'dashboard';
            this.navigate(hash);
        }
    },

    async loadUser() {
        if (!this.state.userId) return;
        try {
            this.state.user = await api.getUser(this.state.userId);
            this.updateHeaderProfile();
        } catch (e) {
            console.error('Failed to load user', e);
            localStorage.removeItem('ai_diet_user_id');
            this.state.userId = null;
            this.state.user = null;
            this.navigate('onboarding');
        }
    },

    updateHeaderProfile() {
        const badgeContainer = document.getElementById('user-badge-container');
        const badgeAvatar = document.getElementById('badge-avatar');
        const badgeUsername = document.getElementById('badge-username');

        if (this.state.user) {
            badgeContainer.classList.remove('hidden');
            const name = this.state.user.name || 'User';
            badgeAvatar.innerText = name.charAt(0).toUpperCase();
            badgeUsername.innerText = name;
        } else {
            badgeContainer.classList.add('hidden');
        }
    },

    resetUser() {
        localStorage.removeItem('ai_diet_user_id');
        this.state.userId = null;
        this.state.user = null;
        this.updateHeaderProfile();
        this.navigate('onboarding');
        this.showToast('Profile reset. Choose or create a new profile.');
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
        // Fallback for unset profile
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
