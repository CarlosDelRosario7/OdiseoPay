import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type UserRole = 'Admin' | 'Vendedor'

export type AuthUser = {
  id: number | string
  nombre: string
  usuario: string
  rol: UserRole
}

type AuthState = {
  token: string | null
  user: AuthUser | null
  login: (payload: { token: string; user: AuthUser }) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      login: ({ token, user }) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: 'odiseopay-auth',
    },
  ),
)
