import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'
import { validatePassword } from '../../../shared/utils/validation'
import { Eye, EyeOff, Moon, Sun } from 'lucide-react'
import { useThemeStore } from '../../../shared/store/themeStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)
  const [form, setForm] = useState({ usuario: '', contrasena: '' })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)

  const handleChange = (field: 'usuario' | 'contrasena', value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')

    if (!form.usuario.trim() || !validatePassword(form.contrasena)) {
      setError('Usuario y contraseña válidos son requeridos.')
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
          id: 0,
          nombre: result.usuario,
          usuario: result.usuario,
          rol: result.rol as 'Admin' | 'Vendedor',
        },
      })

      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar sesión.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <button type="button" className="theme-toggle icon-button" aria-label={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'} onClick={toggleTheme}>
          {theme === 'dark' ? <Sun size={19} /> : <Moon size={19} />}
        </button>
        <div className="brand-block">
          <img src="/icono.svg" alt="OdiseoPay" className="brand-icon" />
          <h1>OdiseoPay</h1>
          <p>Gestión de ventas, inventario y clientes.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Usuario
            <input
              type="text"
              value={form.usuario}
              onChange={(event) => handleChange('usuario', event.target.value)}
              placeholder="admin"
            />
          </label>

          <label>
            Contraseña
            <span className="password-field">
              <input type={showPassword ? 'text' : 'password'} value={form.contrasena} onChange={(event) => handleChange('contrasena', event.target.value)} placeholder="••••••••" />
              <button type="button" className="icon-button" aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'} onClick={() => setShowPassword((visible) => !visible)}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button>
            </span>
          </label>

          {error ? <p className="error-message">{error}</p> : null}

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? <><img src="/icono.svg" alt="" className="button-loader" />Ingresando...</> : 'Iniciar sesión'}
          </button>
        </form>
      </section>
    </main>
  )
}
