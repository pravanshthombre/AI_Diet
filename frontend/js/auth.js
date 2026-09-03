/**
 * NutriCalc - Local Device Identity Management
 * Automatically manages local device tokens without any login or Supabase dependency.
 */

class AuthManager {
    constructor() {
        this.tokenKey = 'ai_diet_device_token';
        this.token = localStorage.getItem(this.tokenKey);
        if (!this.token) {
            this.token = 'device_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            localStorage.setItem(this.tokenKey, this.token);
        }
    }

    getAccessToken() {
        return this.token;
    }

    getCurrentUser() {
        return {
            id: this.token,
            email: 'local@user.internal'
        };
    }

    init() {
        // No-op since we don't have login forms or remote auth
    }

    async signOut() {
        localStorage.removeItem('ai_diet_user_id');
        localStorage.removeItem(this.tokenKey);
        window.location.reload();
    }
}

const authManager = new AuthManager();
window.authManager = authManager;
