import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

interface User {
  id: string;
  full_name: string;
  username?: string;
  role: 'student' | 'teacher' | 'admin';
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isAuthenticated: false,
        isLoading: true,

        setUser: (user) => {
          console.log('[Store:useAuthStore] setUser called', { user });
          set({ user, isAuthenticated: !!user, isLoading: false });
        },

        setLoading: (isLoading) => {
          console.log('[Store:useAuthStore] setLoading called', { isLoading });
          set({ isLoading });
        },

        logout: () => {
          console.log('[Store:useAuthStore] logout called');
          set({ user: null, isAuthenticated: false, isLoading: false });
        },
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'AuthStore' }
  )
);
