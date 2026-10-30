import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import {
  Boxes,
  ClipboardList,
  FolderTree,
  LayoutDashboard,
  Link2,
  LogOut,
  Package,
  ShieldCheck,
  ShoppingCart,
  Truck,
  Unlink,
  Users,
  X,
} from 'lucide-react'

import { api } from '../lib/api'
import {
  clearLinkIntent,
  clearLinkResult,
  isAuth0Configured,
  readLinkResult,
  startLinkIntent,
} from '../lib/auth0'
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

function describeAuth0Error(error: unknown) {
  if (error && typeof error === 'object') {
    const authError = error as { error?: string; message?: string }
    const message = authError.message ?? ''

    if (message.includes('not authorized to access resource server')) {
      return 'La aplicación SPA no está autorizada para la API de OdiseoPay en Auth0. En el dashboard abre APIs → OdiseoPay API → Applications y autoriza la SPA KTIURFsJfii0Q3EcCfHSa8FL2RN49QWz.'
    }
    if (message.includes('Callback URL mismatch')) {
      return `La URL de callback no está autorizada en Auth0. Agrega ${window.location.origin}/login en Allowed Callback URLs de la SPA.`
    }

    if (authError.error === 'cancelled' || authError.error === 'access_denied') {
      return 'Cancelaste el proceso con Auth0.'
    }
    if (message) {
      return message
    }
  }

  return 'No se pudo completar la operación con Auth0.'
}

export default function Sidebar({ onClose }: SidebarProps) {
  const token = useAuthStore((state) => state.token)
  const user = useAuthStore((state) => state.user)
  const role = user?.rol
  const clearLocalSession = useAuthStore((state) => state.logout)
  const setSocialAccount = useAuthStore((state) => state.setSocialAccount)

  const {
    loginWithRedirect,
    logout: auth0Logout,
    isAuthenticated,
  } = useAuth0()

  const [initialLinkResult] = useState(readLinkResult)
  const [accountBusy, setAccountBusy] = useState(false)
  const [accountMessage, setAccountMessage] = useState(
    initialLinkResult?.type === 'success' ? initialLinkResult.message : '',
  )
  const [accountError, setAccountError] = useState(
    initialLinkResult?.type === 'error' ? initialLinkResult.message : '',
  )

  const hasSocialAccount = Boolean(user?.auth0_sub)

  useEffect(() => {
    clearLinkResult()
  }, [])

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

  const handleLinkAccount = () => {
    setAccountMessage('')
    setAccountError('')

    if (!token) {
      setAccountError('Tu sesión local expiró. Vuelve a iniciar sesión.')
      return
    }

    if (!isAuth0Configured) {
      setAccountError(
        'Auth0 no está configurado. Revisa client/.env y reinicia Vite.',
      )
      return
    }

    setAccountBusy(true)
    startLinkIntent(`${window.location.pathname}${window.location.search}`)

    void loginWithRedirect({
      authorizationParams: {
        prompt: 'login',
      },
    }).catch((error) => {
      clearLinkIntent()
      setAccountBusy(false)
      setAccountError(describeAuth0Error(error))
    })
  }

  const handleUnlinkAccount = async () => {
    setAccountMessage('')
    setAccountError('')

    if (!token) {
      setAccountError('Tu sesión local expiró. Vuelve a iniciar sesión.')
      return
    }

    const confirmed = window.confirm(
      '¿Desvincular tu cuenta social? Después podrás vincular Google o Facebook de nuevo.',
    )

    if (!confirmed) {
      return
    }

    try {
      setAccountBusy(true)

      await api.unlinkAuth0(token)

      setSocialAccount({ auth0_sub: null, auth0_provider: null })
      setAccountMessage('Cuenta social desvinculada correctamente.')
    } catch (error) {
      setAccountError(
        error instanceof Error
          ? error.message
          : 'No se pudo desvincular la cuenta social.',
      )
    } finally {
      setAccountBusy(false)
    }
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

      <div className="sidebar-account">
        <p className="sidebar-account-title">Cuenta social</p>

        {hasSocialAccount ? (
          <>
            <span className="sidebar-account-status">
              <ShieldCheck size={16} aria-hidden="true" />
              {user?.auth0_provider ?? 'Cuenta'} vinculada
            </span>

            <button
              type="button"
              className="secondary-button sidebar-account-button"
              onClick={handleUnlinkAccount}
              disabled={accountBusy}
            >
              <Unlink size={16} aria-hidden="true" />
              {accountBusy ? 'Desvinculando...' : 'Desvincular'}
            </button>
          </>
        ) : (
          <button
            type="button"
            className="secondary-button sidebar-account-button"
            onClick={handleLinkAccount}
            disabled={accountBusy || !isAuth0Configured}
            title={
              isAuth0Configured
                ? 'Vincular Google o Facebook a tu usuario'
                : 'Auth0 no está configurado'
            }
          >
            <Link2 size={16} aria-hidden="true" />
            {accountBusy ? 'Redirigiendo a Auth0...' : 'Vincular cuenta social'}
          </button>
        )}

        {accountMessage ? (
          <p className="success-message sidebar-account-message">
            {accountMessage}
          </p>
        ) : null}

        {accountError ? (
          <p className="error-message sidebar-account-message">
            {accountError}
          </p>
        ) : null}
      </div>

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
