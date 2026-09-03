import { useAuthStore } from '../store/authStore'
import { useThemeStore } from '../store/themeStore'

export default function Topbar() {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)

  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Sistema</p>
        <h2>Gestión comercial</h2>
      </div>

      <div className="topbar-actions">
        <button type="button" className="ghost-button" onClick={toggleTheme}>
          {theme === 'dark' ? 'Light mode' : 'Dark mode'}
        </button>

        <div className="user-chip">
          <span>{user?.rol ?? 'Admin'}</span>
          <strong>{user?.nombre ?? 'Usuario'}</strong>
        </div>

        <button type="button" className="ghost-button" onClick={logout}>
          Cerrar sesión
        </button>
      </div>
    </header>
  )
}
