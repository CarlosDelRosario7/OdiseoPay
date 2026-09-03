import { create } from 'zustand'

export type ThemeMode = 'dark' | 'light'

type ThemeState = {
  theme: ThemeMode
  toggleTheme: () => void
  setTheme: (theme: ThemeMode) => void
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: 'dark',
  toggleTheme: () =>
    set((state) => ({
      theme: state.theme === 'dark' ? 'light' : 'dark',
    })),
  setTheme: (theme) => set({ theme }),
}))
