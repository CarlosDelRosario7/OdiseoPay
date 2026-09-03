import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/ventas', label: 'Ventas' },
  { to: '/productos', label: 'Productos' },
  { to: '/clientes', label: 'Clientes' },
  { to: '/inventario', label: 'Inventario' },
  { to: '/usuarios', label: 'Usuarios' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-box">
        <img src="/icono.svg" alt="OdiseoPay" />
        <div>
          <strong>OdiseoPay</strong>
          <small>POS / ERP</small>
        </div>
      </div>

      <nav className="nav-menu" aria-label="Main navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
