/**
 * NutriCalc - Supabase Authentication & Session Management
 * Handles Sign In, Sign Up, Password Recovery, Profile Sync, and Supabase client config.
 */

class AuthManager {
    constructor() {
        this.defaultUrl = 'https://gazqozzbookpqueplkpd.supabase.co';
        // Supabase anon key can be stored in localStorage or fallback
        this.defaultKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdhenFvenpib29rcHF1ZXBsa3BkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAzNTQ5ODUsImV4cCI6MjA1NTkzMDk4NX0.dummy_public_key';
        this.supabase = null;
        this.session = null;
        this.user = null;
        this.isConfigured = false;
        this.activeTab = 'signin';
    }

    getSupabaseUrl() {
        return localStorage.getItem('NUTRICALC_SUPABASE_URL') || this.defaultUrl;
    }

    getSupabaseKey() {
        return localStorage.getItem('NUTRICALC_SUPABASE_KEY') || this.defaultKey;
    }

    getAccessToken() {
        return this.session?.access_token || null;
    }

    getCurrentUser() {
        return this.user;
    }

    init() {
        this.initSupabaseClient();
        this.setupEventListeners();
        this.checkSession();
    }

    initSupabaseClient() {
        const url = this.getSupabaseUrl();
        const key = this.getSupabaseKey();

        if (typeof window.supabase !== 'undefined' && window.supabase.createClient) {
            try {
                this.supabase = window.supabase.createClient(url, key, {
                    auth: {
                        persistSession: true,
                        autoRefreshToken: true,
                        detectSessionInUrl: true,
                        storage: window.localStorage
                    }
                });
                this.isConfigured = true;

                // Subscribe to auth state updates
                this.supabase.auth.onAuthStateChange(async (event, session) => {
                    console.log('[SUPABASE AUTH EVENT]', event, session?.user?.email);
                    this.session = session;
                    this.user = session?.user || null;
                    
                    if (event === 'SIGNED_IN' && session) {
                        await this.onUserAuthenticated(session.user);
                    } else if (event === 'SIGNED_OUT') {
                        this.onUserSignedOut();
                    }
                });
            } catch (err) {
                console.warn('[SUPABASE INIT NOTICE]', err);
                this.isConfigured = false;
            }
        } else {
            console.warn('[SUPABASE] Supabase JS library not yet loaded in window.');
        }
    }

    setupEventListeners() {
        // Sign In form submit
        const signinForm = document.getElementById('form-signin');
        if (signinForm) {
            signinForm.addEventListener('submit', (e) => this.handleSignIn(e));
        }

        // Sign Up form submit
        const signupForm = document.getElementById('form-signup');
        if (signupForm) {
            signupForm.addEventListener('submit', (e) => this.handleSignUp(e));
        }

        // Forgot password form submit
        const forgotForm = document.getElementById('form-forgot-password');
        if (forgotForm) {
            forgotForm.addEventListener('submit', (e) => this.handleForgotPassword(e));
        }
    }

    async checkSession() {
        if (!this.supabase) return;
        try {
            const { data, error } = await this.supabase.auth.getSession();
            if (error) throw error;
            if (data?.session?.user) {
                this.session = data.session;
                this.user = data.session.user;
                await this.onUserAuthenticated(data.session.user);
                return;
            }
        } catch (err) {
            console.warn('[AUTH SESSION CHECK]', err);
        }

        // If no active Supabase session
        if (!app.state.userId) {
            app.navigate('auth');
        }
    }

    switchTab(tab) {
        this.activeTab = tab;
        const signinTabBtn = document.getElementById('tab-btn-signin');
        const signupTabBtn = document.getElementById('tab-btn-signup');
        const signinCard = document.getElementById('auth-card-signin');
        const signupCard = document.getElementById('auth-card-signup');

        if (tab === 'signup') {
            if (signinTabBtn) signinTabBtn.classList.remove('active');
            if (signupTabBtn) signupTabBtn.classList.add('active');
            if (signinCard) signinCard.classList.add('hidden');
            if (signupCard) signupCard.classList.remove('hidden');
        } else {
            if (signupTabBtn) signupTabBtn.classList.remove('active');
            if (signinTabBtn) signinTabBtn.classList.add('active');
            if (signupCard) signupCard.classList.add('hidden');
            if (signinCard) signinCard.classList.remove('hidden');
        }
    }

    togglePasswordVisibility(inputId, iconId) {
        const input = document.getElementById(inputId);
        const icon = document.getElementById(iconId);
        if (!input) return;
        if (input.type === 'password') {
            input.type = 'text';
            if (icon) icon.innerText = '🙈';
        } else {
            input.type = 'password';
            if (icon) icon.innerText = '👁️';
        }
    }

    async handleSignIn(e) {
        if (e) e.preventDefault();
        const emailInput = document.getElementById('signin-email');
        const passInput = document.getElementById('signin-password');
        const btn = document.getElementById('btn-signin-submit');
        const errorEl = document.getElementById('signin-error-msg');

        if (!emailInput || !passInput) return;
        const email = emailInput.value.trim();
        const password = passInput.value;

        if (!email || !password) {
            this.showAuthError(errorEl, 'Please enter both email and password.');
            return;
        }

        this.clearAuthError(errorEl);
        this.setButtonLoading(btn, true, 'Signing in...');

        try {
            if (!this.supabase) {
                this.initSupabaseClient();
            }

            const { data, error } = await this.supabase.auth.signInWithPassword({
                email,
                password
            });

            if (error) {
                // If demo or local fallback needed
                if (error.message.includes('Invalid API key') || error.message.includes('FetchError') || error.message.includes('NetworkError')) {
                    throw new Error(error.message + '. (Tip: configure your Supabase Anon Key in Settings if not set).');
                }
                throw error;
            }

            app.showToast('Welcome back! Signed in successfully.', 'success');
            if (data?.user) {
                await this.onUserAuthenticated(data.user);
            }
        } catch (err) {
            console.error('[SIGN IN ERROR]', err);
            this.showAuthError(errorEl, err.message || 'Failed to sign in. Please verify your credentials.');
        } finally {
            this.setButtonLoading(btn, false, 'Sign In to NutriCalc');
        }
    }

    async handleSignUp(e) {
        if (e) e.preventDefault();
        const nameInput = document.getElementById('signup-name');
        const emailInput = document.getElementById('signup-email');
        const passInput = document.getElementById('signup-password');
        const confirmPassInput = document.getElementById('signup-password-confirm');
        const btn = document.getElementById('btn-signup-submit');
        const errorEl = document.getElementById('signup-error-msg');

        if (!emailInput || !passInput || !nameInput) return;
        const fullName = nameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passInput.value;
        const confirmPassword = confirmPassInput ? confirmPassInput.value : password;

        if (!fullName) {
            this.showAuthError(errorEl, 'Please enter your full name.');
            return;
        }
        if (!email || !password) {
            this.showAuthError(errorEl, 'Please fill in all required fields.');
            return;
        }
        if (password.length < 6) {
            this.showAuthError(errorEl, 'Password must be at least 6 characters long.');
            return;
        }
        if (password !== confirmPassword) {
            this.showAuthError(errorEl, 'Passwords do not match.');
            return;
        }

        this.clearAuthError(errorEl);
        this.setButtonLoading(btn, true, 'Creating account...');

        try {
            if (!this.supabase) {
                this.initSupabaseClient();
            }

            const { data, error } = await this.supabase.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        full_name: fullName
                    }
                }
            });

            if (error) {
                throw error;
            }

            if (data?.session) {
                app.showToast('Account created successfully!', 'success');
                await this.onUserAuthenticated(data.user, fullName);
            } else if (data?.user && !data.session) {
                // Email confirmation required by Supabase project settings
                this.showAuthSuccess(errorEl, 'Account created! Please check your email inbox to confirm your account, then sign in.');
                app.showToast('Verification email sent! Please check your inbox.', 'info');
            }
        } catch (err) {
            console.error('[SIGN UP ERROR]', err);
            this.showAuthError(errorEl, err.message || 'Failed to create account. Please try again.');
        } finally {
            this.setButtonLoading(btn, false, 'Create Free Account');
        }
    }

    async handleForgotPassword(e) {
        if (e) e.preventDefault();
        const emailInput = document.getElementById('forgot-email');
        const btn = document.getElementById('btn-forgot-submit');
        const msgEl = document.getElementById('forgot-status-msg');

        if (!emailInput) return;
        const email = emailInput.value.trim();
        if (!email) {
            if (msgEl) {
                msgEl.innerHTML = '<span style="color: var(--accent-coral);">Please enter your email address.</span>';
            }
            return;
        }

        this.setButtonLoading(btn, true, 'Sending link...');
        try {
            const { error } = await this.supabase.auth.resetPasswordForEmail(email, {
                redirectTo: window.location.origin
            });
            if (error) throw error;

            if (msgEl) {
                msgEl.innerHTML = '<span style="color: #059669; font-weight: 600;">Password reset email sent! Check your inbox.</span>';
            }
            app.showToast('Password reset link sent to ' + email, 'info');
            setTimeout(() => {
                this.closeForgotPasswordModal();
            }, 3000);
        } catch (err) {
            if (msgEl) {
                msgEl.innerHTML = `<span style="color: var(--accent-coral);">${err.message || 'Failed to send reset link.'}</span>`;
            }
        } finally {
            this.setButtonLoading(btn, false, 'Send Reset Link');
        }
    }

    async handleDemoLogin() {
        app.showToast('Entering demo mode with sample profile...', 'info');
        // Set sample user state
        const demoUser = {
            id: 'demo-user-1',
            email: 'rahul.demo@nutricalc.ai',
            user_metadata: { full_name: 'Rahul Sharma' }
        };
        this.user = demoUser;
        await this.onUserAuthenticated(demoUser, 'Rahul Sharma');
    }

    async onUserAuthenticated(supabaseUser, optionalName = null) {
        if (!supabaseUser) return;
        this.user = supabaseUser;

        const uid = supabaseUser.id;
        const email = supabaseUser.email || '';
        const name = optionalName || supabaseUser.user_metadata?.full_name || email.split('@')[0] || 'User';

        // Check if NutriCalc backend profile already exists for this Supabase user
        try {
            let profile = null;
            try {
                profile = await api.getUserBySupabaseUid(uid);
            } catch (notFoundByUid) {
                // Try finding by email
                if (email) {
                    try {
                        profile = await api.getUserByEmail(email);
                    } catch (notFoundByEmail) {
                        profile = null;
                    }
                }
            }

            if (profile && profile.id) {
                // Existing profile found! Load user & go to dashboard
                localStorage.setItem('ai_diet_user_id', profile.id);
                app.state.userId = profile.id;
                app.state.user = profile;
                app.state.supabaseUser = supabaseUser;
                app.updateHeaderProfile();
                
                const hash = window.location.hash.replace('#', '');
                if (hash && hash !== 'auth' && hash !== 'onboarding') {
                    app.navigate(hash);
                } else {
                    app.navigate('dashboard');
                }
                return;
            }
        } catch (err) {
            console.log('[USER PROFILE SYNC NOTICE]', err);
        }

        // New user or no profile found yet: Pre-fill onboarding with auth details
        app.state.supabaseUser = supabaseUser;
        if (typeof onboarding !== 'undefined') {
            onboarding.data.name = name;
            onboarding.data.email = email;
            onboarding.data.supabase_uid = uid;
            onboarding.currentStep = 1;
        }

        app.showToast(`Hello ${name}! Let's customize your diet plan in a few quick steps.`);
        app.navigate('onboarding');
    }

    async signOut() {
        try {
            if (this.supabase) {
                await this.supabase.auth.signOut();
            }
        } catch (err) {
            console.warn('[SIGN OUT NOTICE]', err);
        }
        this.onUserSignedOut();
    }

    onUserSignedOut() {
        this.session = null;
        this.user = null;
        localStorage.removeItem('ai_diet_user_id');
        app.state.userId = null;
        app.state.user = null;
        app.state.supabaseUser = null;
        app.updateHeaderProfile();
        app.showToast('You have signed out.', 'info');
        app.navigate('auth');
    }

    showAuthError(el, msg) {
        if (!el) return;
        el.innerHTML = `⚠️ ${msg}`;
        el.classList.remove('hidden');
    }

    showAuthSuccess(el, msg) {
        if (!el) return;
        el.innerHTML = `✅ ${msg}`;
        el.style.backgroundColor = 'var(--primary-50)';
        el.style.borderColor = 'var(--primary-300)';
        el.style.color = 'var(--primary-800)';
        el.classList.remove('hidden');
    }

    clearAuthError(el) {
        if (!el) return;
        el.innerHTML = '';
        el.classList.add('hidden');
    }

    setButtonLoading(btn, isLoading, defaultText) {
        if (!btn) return;
        if (isLoading) {
            btn.disabled = true;
            btn.setAttribute('data-original-text', btn.innerHTML);
            btn.innerHTML = `<span class="spinner" style="display:inline-block; width:16px; height:16px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; vertical-align:middle; margin-right:6px;"></span> ${defaultText}`;
        } else {
            btn.disabled = false;
            btn.innerHTML = defaultText;
        }
    }

    openForgotPasswordModal() {
        const modal = document.getElementById('modal-forgot-password');
        if (modal) modal.classList.remove('hidden');
    }

    closeForgotPasswordModal() {
        const modal = document.getElementById('modal-forgot-password');
        if (modal) modal.classList.add('hidden');
    }

    openSupabaseConfigModal() {
        const modal = document.getElementById('modal-supabase-config');
        const urlInput = document.getElementById('input-supabase-url');
        const keyInput = document.getElementById('input-supabase-key');
        if (urlInput) urlInput.value = this.getSupabaseUrl();
        if (keyInput) keyInput.value = this.getSupabaseKey();
        if (modal) modal.classList.remove('hidden');
    }

    closeSupabaseConfigModal() {
        const modal = document.getElementById('modal-supabase-config');
        if (modal) modal.classList.add('hidden');
    }

    saveSupabaseConfig() {
        const urlInput = document.getElementById('input-supabase-url');
        const keyInput = document.getElementById('input-supabase-key');
        const url = urlInput ? urlInput.value.trim() : '';
        const key = keyInput ? keyInput.value.trim() : '';

        if (url) localStorage.setItem('NUTRICALC_SUPABASE_URL', url);
        if (key) localStorage.setItem('NUTRICALC_SUPABASE_KEY', key);

        this.initSupabaseClient();
        this.closeSupabaseConfigModal();
        app.showToast('Supabase configuration updated successfully!', 'success');
    }
}

const authManager = new AuthManager();
window.authManager = authManager;
