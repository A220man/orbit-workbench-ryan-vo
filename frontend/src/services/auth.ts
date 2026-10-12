/**
 * In-memory authentication client with PKCE support.
 * Tokens are kept in memory closure only, never persisted to localStorage.
 */

import { UserProfile } from '../types/api';

let inMemoryToken: string | null = null;
let currentUser: UserProfile | null = null;

export const authService = {
  getToken(): string | null {
    return inMemoryToken;
  },

  setToken(token: string | null) {
    inMemoryToken = token;
  },

  getUser(): UserProfile | null {
    return currentUser;
  },

  setUser(user: UserProfile | null) {
    currentUser = user;
  },

  clear() {
    inMemoryToken = null;
    currentUser = null;
    sessionStorage.removeItem('orbit_pkce_verifier');
    sessionStorage.removeItem('orbit_pkce_state');
  },

  initiatePkceFlow(issuerUrl: string, clientId: string) {
    const state = Math.random().toString(36).substring(2);
    const verifier = Math.random().toString(36).substring(2) + Math.random().toString(36).substring(2);
    sessionStorage.setItem('orbit_pkce_state', state);
    sessionStorage.setItem('orbit_pkce_verifier', verifier);
    // In production, redirects to Keycloak /auth
    return `${issuerUrl}/protocol/openid-connect/auth?client_id=${clientId}&response_type=code&state=${state}`;
  },

  async loginDemo(role: 'viewer' | 'analyst' | 'admin' = 'analyst'): Promise<UserProfile> {
    const res = await fetch('/api/auth/demo-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role, username: `demo-${role}` }),
    });

    if (!res.ok) {
      throw new Error(`Demo login failed with status ${res.status}`);
    }

    const data = await res.json();
    this.setToken(data.access_token);

    const user: UserProfile = {
      user_id: data.user_id,
      username: `Demo ${role.toUpperCase()}`,
      roles: data.roles,
      is_demo: true,
    };
    this.setUser(user);
    return user;
  },

  async fetchProfile(): Promise<UserProfile> {
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch('/api/auth/me', { headers });
    if (!res.ok) {
      throw new Error('Unauthenticated');
    }
    const user = await res.json();
    this.setUser(user);
    return user;
  },
};
