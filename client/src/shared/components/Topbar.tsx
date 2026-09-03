import { useAuthStore } from '../store/authStore'
import { useThemeStore } from '../store/themeStore'
import { Menu, Moon, Sun } from 'lucide-react'

type TopbarProps = { onMenuToggle: () => void }

export default function Topbar({ onMenuToggle }: TopbarProps) {
  const user = useAuthStore((state) => state.user)
  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)

  return (
    <header className="topbar">
      <div>
        <button type="button" className="icon-button menu-button" aria-label="Abrir menú" onClick={onMenuToggle}><Menu size={22} /></button>
        <p className="eyebrow">Sistema</p>
        <h2>Gestión comercial</h2>
      </div>

      <div className="topbar-actions">
        <button type="button" className="ghost-button" onClick={toggleTheme}>
          {theme === 'dark' ? <Sun size={17} aria-hidden="true" /> : <Moon size={17} aria-hidden="true" />}
          <span>{theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}</span>
        </button>

        <div className="user-chip">
          <span>{user?.rol ?? 'Admin'}</span>
          <strong>{user?.nombre ?? 'Usuario'}</strong>
        </div>

      </div>
    </header>
  )
}
