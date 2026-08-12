import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserProfile {
  id: string;
  email: string;
  name: string;
  provider: 'local' | 'supabase';
  organization_id?: string;
}

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  login: (email: string, password: string, provider?: 'local' | 'supabase') => Promise<void>;
  logout: () => void;
  setTokens: (accessToken: string, refreshToken?: string) => void;
  getAccessToken: () => string | null;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      accessToken: null,
      refreshToken: null,
      
      setTokens: (accessToken, refreshToken) => {
        set({
          accessToken,
          refreshToken: refreshToken || null,
        });
      },
      
      getAccessToken: () => get().accessToken,
      
      login: async (email, password, provider = 'local') => {
        if (!email || !password) return;

        if (provider === 'supabase') {
          // Redirect to Supabase OAuth flow - will handle callback in _app.tsx
          const { buildSupabaseAuthUrl } = await import('@/lib/supabase');
          window.location.href = buildSupabaseAuthUrl('google');
          return;
        }

        // Local provider: call backend auth and store JWT securely
        try {
          const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',  // Include cookies for CSRF tokens
            body: JSON.stringify({ email, password }),
          });
          
          if (!res.ok) {
            throw new Error(`Login failed: ${res.statusText}`);
          }
          
          const data = await res.json();
          const accessToken = data.access_token;
          const refreshToken = data.refresh_token;
          
          if (accessToken) {
            // Store tokens securely in sessionStorage (cleared on browser close)
            sessionStorage.setItem('access_token', accessToken);
            if (refreshToken) {
              sessionStorage.setItem('refresh_token', refreshToken);
            }
            
            // Decode jwt payload to extract user info
            try {
              const parts = accessToken.split('.');
              if (parts.length >= 2) {
                const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
                set({
                  user: {
                    id: payload.sub,
                    email: email,
                    name: payload.name || payload.sub,
                    provider: 'local',
                    organization_id: payload.org_id,
                  },
                  isAuthenticated: true,
                  accessToken,
                  refreshToken: refreshToken || null,
                });
              }
            } catch (decodeError) {
              console.error('Failed to decode JWT', decodeError);
            }
          }
        } catch (e) {
          console.error('Login failed', e);
          throw e;
        }
      },
      
      logout: () => {
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        set({
          user: null,
          isAuthenticated: false,
          accessToken: null,
          refreshToken: null,
        });
      },
    }),
    {
      name: 'carai-auth-storage',
      // Use sessionStorage instead of localStorage for better security
      storage: {
        getItem: (key) => {
          const item = sessionStorage.getItem(key);
          return item ? JSON.parse(item) : null;
        },
        setItem: (key, value) => {
          sessionStorage.setItem(key, JSON.stringify(value));
        },
        removeItem: (key) => {
          sessionStorage.removeItem(key);
        },
      },
    }
  )
);
