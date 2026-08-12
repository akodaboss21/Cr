import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserProfile {
  id: string;
  email: string;
  name: string;
  provider: 'local' | 'supabase';
}

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, provider?: 'local' | 'supabase') => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      login: async (email, password, provider = 'local') => {
        if (!email || !password) return;

        if (provider === 'supabase') {
          // Redirect to Supabase OAuth flow
          const { buildSupabaseAuthUrl } = await import('@/lib/supabase');
          window.location.href = buildSupabaseAuthUrl('google');
          return;
        }

        // Local provider: call backend auth and store JWT
        try {
          const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          });
          if (!res.ok) return;
          const data = await res.json();
          const token = data.access_token;
          if (token) {
            localStorage.setItem('access_token', token);
            // decode jwt payload
            const parts = token.split('.');
            if (parts.length >= 2) {
              const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
              set({
                user: {
                  id: payload.sub,
                  email: email,
                  name: payload.sub,
                  provider: 'local',
                },
                isAuthenticated: true,
              });
            }
          }
        } catch (e) {
          console.error('Login failed', e);
        }
      },
      logout: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: 'carai-auth-storage',
    }
  )
);
