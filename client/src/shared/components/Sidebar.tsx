import { NavLink } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import {
  Boxes,
  ClipboardList,
  FolderTree,
  LayoutDashboard,
  LogOut,
  Package,
  ShoppingCart,
  Truck,
  Users,
  X,
} from 'lucide-react'

import { useAuthStore } from '../store/authStore'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/ventas', label: 'Ventas', icon: ShoppingCart },
  { to: '/ventas/historial', label: 'Historial', icon: ClipboardList },
  { to: '/productos', label: 'Productos', icon: Package },
  { to: '/categorias', label: 'Categorías', icon: FolderTree },
  { to: '/clientes', label: 'Clientes', icon: Users },
  { to: '/inventario', label: 'Inventario', icon: Boxes },
  { to: '/proveedores', label: 'Proveedores', icon: Truck },
  { to: '/usuarios', label: 'Usuarios', icon: ClipboardList },
  {
    to: '/compras',
    label: 'Compras',
    icon: ShoppingCart,
    adminOnly: true,
  },
]

type SidebarProps = {
  onClose: () => void
}

export default function Sidebar({ onClose }: SidebarProps) {
  const role = useAuthStore((state) => state.user?.rol)
  const clearLocalSession = useAuthStore((state) => state.logout)

  const {
    logout: auth0Logout,
    isAuthenticated,
  } = useAuth0()

  const handleLogout = () => {
    // Elimina el JWT y el usuario guardado por OdiseoPay.
    clearLocalSession()

    // Si existe una sesión de Auth0, también la cerramos.
    if (isAuthenticated) {
      auth0Logout({
        logoutParams: {
          returnTo: `${window.location.origin}/login`,
        },
      })
      return
    }

    // Para sesiones iniciadas con usuario/contraseña local.
    window.location.href = '/login'
  }

  return (
    <aside className="sidebar">
      <div className="brand-box">
        <img src="/icono.svg" alt="OdiseoPay" />

        <div>
          <strong>OdiseoPay</strong>
          <small>POS / ERP</small>
        </div>

        <button
          type="button"
          className="icon-button sidebar-close"
          aria-label="Cerrar menú"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>

      <nav className="nav-menu" aria-label="Main navigation">
        {navItems
          .filter(
            (item) =>
              (!item.adminOnly && item.to !== '/usuarios') ||
              role === 'Admin',
          )
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
              onClick={onClose}
            >
              <item.icon size={18} aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
      </nav>

      <button
        type="button"
        className="sidebar-logout"
        onClick={handleLogout}
      >
        <LogOut size={18} aria-hidden="true" />
        Cerrar sesión
      </button>
    </aside>
  )
}