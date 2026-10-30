import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type UserRole = 'Admin' | 'Vendedor'

export type AuthUser = {
  id: number | string
  nombre: string
  usuario: string
  rol: UserRole
  auth0_sub?: string | null
  auth0_provider?: string | null
}

type AuthState = {
  token: string | null
  user: AuthUser | null
  login: (payload: { token: string; user: AuthUser }) => void
  setSocialAccount: (payload: {
    auth0_sub: string | null
    auth0_provider?: string | null
  }) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      login: ({ token, user }) => set({ token, user }),
      setSocialAccount: ({ auth0_sub, auth0_provider = null }) =>
        set((state) => ({
          user: state.user
            ? { ...state.user, auth0_sub, auth0_provider }
            : state.user,
        })),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: 'odiseopay-auth',
    },
  ),
)
