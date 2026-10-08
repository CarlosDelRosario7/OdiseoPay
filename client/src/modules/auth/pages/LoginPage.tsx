import { type FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import { Eye, EyeOff, Moon, Sun } from 'lucide-react'

import { api } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'
import { useThemeStore } from '../../../shared/store/themeStore'
import { validatePassword } from '../../../shared/utils/validation'

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

  const [form, setForm] = useState({
    usuario: '',
    contrasena: '',
  })

  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return
    }

    let cancelled = false

    const loginWithAuth0 = async () => {
      try {
        setIsSubmitting(true)
        setError('')

        const auth0Token = await getAccessTokenSilently()

        if (!auth0Token) {
          throw new Error(
            'Auth0 no devolvió un token de acceso.',
          )
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
    navigate,
  ])

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

    if (
      !form.usuario.trim() ||
      !validatePassword(form.contrasena)
    ) {
      setError(
        'Usuario y contraseña válidos son requeridos.',
      )
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
        },
      })

      navigate('/', { replace: true })
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo iniciar sesión.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleAuth0Login = async () => {
    setError('')

    try {
      await loginWithRedirect({
        authorizationParams: {
          prompt: 'login',
        },
      })
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo iniciar sesión con Auth0.',
      )
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
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
          {theme === 'dark' ? (
            <Sun size={19} />
          ) : (
            <Moon size={19} />
          )}
        </button>

        <div className="brand-block">
          <img
            src="/icono.svg"
            alt="OdiseoPay"
            className="brand-icon"
          />

          <h1>OdiseoPay</h1>

          <p>
            Gestión de ventas, inventario y clientes.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >
          <label>
            Usuario
            <input
              type="text"
              value={form.usuario}
              onChange={(event) =>
                handleChange(
                  'usuario',
                  event.target.value,
                )
              }
              placeholder="admin"
            />
          </label>

          <label>
            Contraseña

            <span className="password-field">
              <input
                type={
                  showPassword
                    ? 'text'
                    : 'password'
                }
                value={form.contrasena}
                onChange={(event) =>
                  handleChange(
                    'contrasena',
                    event.target.value,
                  )
                }
                placeholder="••••••••"
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
                  setShowPassword(
                    (visible) => !visible,
                  )
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
            <p className="error-message">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={isSubmitting}
          >
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

        <button
          type="button"
          onClick={handleAuth0Login}
          disabled={isSubmitting || isLoading}
        >
          {isLoading
            ? 'Cargando Auth0...'
            : isSubmitting
              ? 'Ingresando...'
              : 'Continuar con Auth0'}
        </button>

        {auth0Error ? (
          <p className="error-message">
            {auth0Error.message}
          </p>
        ) : null}
      </section>
    </main>
  )
}