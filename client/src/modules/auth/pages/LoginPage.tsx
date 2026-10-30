import { type FormEvent, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import {
  Boxes,
  Eye,
  EyeOff,
  Moon,
  ShieldCheck,
  Sun,
  TrendingUp,
} from 'lucide-react'

import { api } from '../../../shared/lib/api'
import {
  auth0Connections,
  clearLinkIntent,
  consumeLinkReturnTo,
  hasLinkIntent,
  isAuth0Configured,
  setLinkResult,
} from '../../../shared/lib/auth0'
import { useAuthStore } from '../../../shared/store/authStore'
import { useThemeStore } from '../../../shared/store/themeStore'

type SocialProvider = 'google' | 'facebook'

function GoogleIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
      />
      <path
        fill="#4285F4"
        d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
      />
      <path
        fill="#FBBC05"
        d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
      />
      <path
        fill="#34A853"
        d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
      />
    </svg>
  )
}

function FacebookIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#1877F2"
        d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.68.24 2.68.24v2.95h-1.51c-1.49 0-1.95.93-1.95 1.88v2.28h3.32l-.53 3.49h-2.79V24C19.61 23.1 24 18.1 24 12.07z"
      />
    </svg>
  )
}

function describeAuth0LoginError(message: string) {
  const normalized = message.toLowerCase()

  if (
    normalized.includes('access_denied') ||
    normalized.includes('cancelled') ||
    normalized.includes('canceled') ||
    normalized.includes('did not authorize')
  ) {
    return 'Cancelaste el proceso con Auth0.'
  }

  if (message.includes('not authorized to access resource server')) {
    return (
      'La aplicación SPA no está autorizada para la API de OdiseoPay en Auth0. ' +
      'En el dashboard abre APIs → OdiseoPay API → Applications y autoriza ' +
      'la SPA KTIURFsJfii0Q3EcCfHSa8FL2RN49QWz.'
    )
  }

  if (message.includes('Callback URL mismatch')) {
    return (
      'La URL de callback no está autorizada en Auth0. Agrega ' +
      `${window.location.origin}/login en Allowed Callback URLs de la SPA.`
    )
  }

  return message
}

export default function LoginPage() {
  const navigate = useNavigate()

  const {
    loginWithRedirect,
    getAccessTokenSilently,
    isAuthenticated,
    isLoading,
    error: auth0Error,
  } = useAuth0()

  const login = useAuthStore((state) => state.login)
  const localToken = useAuthStore((state) => state.token)
  const setSocialAccount = useAuthStore((state) => state.setSocialAccount)

  const [form, setForm] = useState({
    usuario: '',
    contrasena: '',
  })

  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [socialLoading, setSocialLoading] = useState<SocialProvider | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const authModeRef = useRef<'link' | 'login' | null>(null)
  const linkStartedRef = useRef(false)

  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)

  useEffect(() => {
    document.body.classList.add('auth-page')
    return () => document.body.classList.remove('auth-page')
  }, [])

  useEffect(() => {
    // La vinculación usa redirección en la misma pestaña. Si la página se
    // carga dentro de una ventana emergente, no se procesa el login.
    if (window.opener) {
      return
    }

    if (isLoading || !isAuthenticated) {
      return
    }

    if (authModeRef.current === null) {
      authModeRef.current = hasLinkIntent() ? 'link' : 'login'
    }

    if (authModeRef.current === 'link') {
      if (linkStartedRef.current) {
        return
      }

      linkStartedRef.current = true
      const returnTo = consumeLinkReturnTo()
      clearLinkIntent()

      const linkAccount = async () => {
        try {
          setIsSubmitting(true)
          setError('')

          const auth0Token = await getAccessTokenSilently()

          if (!auth0Token) {
            throw new Error('Auth0 no devolvió un token de acceso.')
          }

          if (!localToken) {
            throw new Error(
              'Tu sesión local expiró. Vuelve a iniciar sesión y vincula la cuenta de nuevo.',
            )
          }

          const result = await api.linkAuth0(localToken, auth0Token)

          setSocialAccount({
            auth0_sub: result.auth0_sub,
            auth0_provider: result.auth0_provider,
          })
          setLinkResult({
            type: 'success',
            message: result.message,
          })
        } catch (err) {
          setLinkResult({
            type: 'error',
            message:
              err instanceof Error
                ? err.message
                : 'No se pudo vincular la cuenta social.',
          })
        } finally {
          navigate(returnTo, { replace: true })
        }
      }

      void linkAccount()
      return
    }

    let cancelled = false

    const loginWithAuth0 = async () => {
      try {
        setIsSubmitting(true)
        setError('')

        const auth0Token = await getAccessTokenSilently()

        if (!auth0Token) {
          throw new Error('Auth0 no devolvió un token de acceso.')
        }

        const result = await api.auth0Login(auth0Token)

        if (cancelled) {
          return
        }

        login({
          token: result.access_token,
          user: {
            id: result.id_usuario,
            nombre: result.nombre,
            usuario: result.usuario,
            rol: result.rol as 'Admin' | 'Vendedor',
            auth0_sub: result.auth0_sub,
            auth0_provider: result.auth0_provider,
          },
        })

        navigate('/', { replace: true })
      } catch (err) {
        if (cancelled) {
          return
        }

        setError(
          err instanceof Error
            ? err.message
            : 'No se pudo iniciar sesión con Auth0.',
        )
      } finally {
        if (!cancelled) {
          setIsSubmitting(false)
        }
      }
    }

    loginWithAuth0()

    return () => {
      cancelled = true
    }
  }, [
    isAuthenticated,
    isLoading,
    getAccessTokenSilently,
    login,
    localToken,
    setSocialAccount,
    navigate,
  ])

  useEffect(() => {
    if (!auth0Error || !hasLinkIntent()) {
      return
    }

    const returnTo = consumeLinkReturnTo()
    clearLinkIntent()
    setLinkResult({
      type: 'error',
      message: describeAuth0LoginError(auth0Error.message),
    })
    navigate(returnTo, { replace: true })
  }, [auth0Error, navigate])

  const handleChange = (
    field: 'usuario' | 'contrasena',
    value: string,
  ) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')

    if (!form.usuario.trim() || !form.contrasena.trim()) {
      setError('Usuario y contraseña son requeridos.')
      return
    }

    try {
      setIsSubmitting(true)

      const result = await api.login({
        usuario: form.usuario,
        contrasena: form.contrasena,
      })

      login({
        token: result.access_token,
        user: {
          id: result.id_usuario,
          nombre: result.nombre,
          usuario: result.usuario,
          rol: result.rol as 'Admin' | 'Vendedor',
          auth0_sub: result.auth0_sub,
          auth0_provider: result.auth0_provider,
        },
      })

      navigate('/', { replace: true })
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'No se pudo iniciar sesión.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSocialLogin = async (provider: SocialProvider) => {
    setError('')

    if (!isAuth0Configured) {
      setError(
        'Auth0 no está configurado. Revisa client/.env y reinicia Vite.',
      )
      return
    }

    try {
      setSocialLoading(provider)

      await loginWithRedirect({
        authorizationParams: {
          connection: auth0Connections[provider],
          prompt: 'login',
        },
      })
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo iniciar sesión con Auth0.',
      )
      setSocialLoading(null)
    }
  }

  const busy = isSubmitting || socialLoading !== null || isLoading

  return (
    <main className="auth-shell">
      <section className="auth-frame">
        <aside className="auth-hero">
          <div className="auth-hero-top">
            <img src="/icono.svg" alt="" />
            <strong>OdiseoPay</strong>
          </div>

          <div className="auth-hero-content">
            <p className="auth-hero-eyebrow">POS / ERP</p>
            <h1>
              Tu negocio,
              <br />
              <span>en orden.</span>
            </h1>
            <p className="auth-hero-copy">
              Ventas, inventario y clientes en un solo lugar, con la
              información siempre a la mano.
            </p>

            <div className="auth-hero-points">
              <span>
                <ShieldCheck size={16} aria-hidden="true" />
                Acceso seguro
              </span>
              <span>
                <Boxes size={16} aria-hidden="true" />
                Inventario en tiempo real
              </span>
              <span>
                <TrendingUp size={16} aria-hidden="true" />
                Reportes claros
              </span>
            </div>
          </div>
        </aside>

        <section className="auth-panel">
          <button
            type="button"
            className="theme-toggle icon-button"
            aria-label={
              theme === 'dark'
                ? 'Cambiar a modo claro'
                : 'Cambiar a modo oscuro'
            }
            onClick={toggleTheme}
          >
            {theme === 'dark' ? <Sun size={19} /> : <Moon size={19} />}
          </button>

          <div className="auth-panel-inner">
            <div className="auth-brand">
              <img src="/icono.svg" alt="OdiseoPay" />
              <div>
                <strong>OdiseoPay</strong>
                <span>Gestión comercial</span>
              </div>
            </div>

            <div className="auth-heading">
              <h2>Bienvenido de nuevo</h2>
              <p>Ingresa con tu cuenta para continuar.</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <label>
                Usuario
                <input
                  type="text"
                  value={form.usuario}
                  onChange={(event) =>
                    handleChange('usuario', event.target.value)
                  }
                  placeholder="admin"
                  autoComplete="username"
                  disabled={busy}
                />
              </label>

              <label>
                Contraseña
                <span className="password-field">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={form.contrasena}
                    onChange={(event) =>
                      handleChange('contrasena', event.target.value)
                    }
                    placeholder="••••••••"
                    autoComplete="current-password"
                    disabled={busy}
                  />

                  <button
                    type="button"
                    className="icon-button"
                    aria-label={
                      showPassword
                        ? 'Ocultar contraseña'
                        : 'Mostrar contraseña'
                    }
                    onClick={() =>
                      setShowPassword((visible) => !visible)
                    }
                  >
                    {showPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </span>
              </label>

              {error ? (
                <p className="error-message" role="alert">
                  {error}
                </p>
              ) : null}

              {auth0Error ? (
                <p className="error-message" role="alert">
                  {describeAuth0LoginError(auth0Error.message)}
                </p>
              ) : null}

              <button type="submit" disabled={busy}>
                {isSubmitting ? (
                  <>
                    <img
                      src="/icono.svg"
                      alt=""
                      className="button-loader"
                    />
                    Ingresando...
                  </>
                ) : (
                  'Iniciar sesión'
                )}
              </button>
            </form>

            <div className="auth-divider">
              <span>o continúa con</span>
            </div>

            <div className="auth-social">
              <button
                type="button"
                className="social-button"
                onClick={() => handleSocialLogin('google')}
                disabled={busy}
              >
                <GoogleIcon />
                <span>
                  {socialLoading === 'google'
                    ? 'Conectando...'
                    : 'Google'}
                </span>
              </button>

              <button
                type="button"
                className="social-button"
                onClick={() => handleSocialLogin('facebook')}
                disabled={busy}
              >
                <FacebookIcon />
                <span>
                  {socialLoading === 'facebook'
                    ? 'Conectando...'
                    : 'Facebook'}
                </span>
              </button>
            </div>

            <p className="auth-hint">
              <ShieldCheck size={15} aria-hidden="true" />
              ¿Primera vez con Google o Facebook? Inicia sesión con tu
              usuario y contraseña y vincula tu cuenta desde el menú
              lateral.
            </p>
          </div>
        </section>
      </section>
    </main>
  )
}
