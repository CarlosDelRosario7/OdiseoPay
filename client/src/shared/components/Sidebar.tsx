import { NavLink } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Boxes, ClipboardList, LayoutDashboard, LogOut, Package, ShoppingCart, Truck, Users, X } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/ventas', label: 'Ventas', icon: ShoppingCart },
  { to: '/productos', label: 'Productos', icon: Package },
  { to: '/clientes', label: 'Clientes', icon: Users },
  { to: '/inventario', label: 'Inventario', icon: Boxes },
  { to: '/proveedores', label: 'Proveedores', icon: Truck },
  { to: '/usuarios', label: 'Usuarios', icon: ClipboardList },
]

type SidebarProps = { onClose: () => void }

export default function Sidebar({ onClose }: SidebarProps) {
  const role = useAuthStore((state) => state.user?.rol)
  const logout = useAuthStore((state) => state.logout)
  return (
    <aside className="sidebar">
      <div className="brand-box">
        <img src="/icono.svg" alt="OdiseoPay" />
        <div>
          <strong>OdiseoPay</strong>
          <small>POS / ERP</small>
        </div>
        <button type="button" className="icon-button sidebar-close" aria-label="Cerrar menú" onClick={onClose}><X size={20} /></button>
      </div>

      <nav className="nav-menu" aria-label="Main navigation">
        {navItems.filter((item) => item.to !== '/usuarios' || role === 'Admin').map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            onClick={onClose}
          >
            <item.icon size={18} aria-hidden="true" />{item.label}
          </NavLink>
        ))}
      </nav>
      <button type="button" className="sidebar-logout" onClick={logout}><LogOut size={18} aria-hidden="true" />Cerrar sesión</button>
    </aside>
  )
}
