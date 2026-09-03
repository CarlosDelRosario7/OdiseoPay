import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'
import { validatePassword } from '../../../shared/utils/validation'

export default function LoginPage() {
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)
  const [form, setForm] = useState({ usuario: '', contrasena: '' })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

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
            <input
              type="password"
              value={form.contrasena}
              onChange={(event) => handleChange('contrasena', event.target.value)}
              placeholder="••••••••"
            />
          </label>

          {error ? <p className="error-message">{error}</p> : null}

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Ingresando...' : 'Iniciar sesión'}
          </button>
        </form>
      </section>
    </main>
  )
}
