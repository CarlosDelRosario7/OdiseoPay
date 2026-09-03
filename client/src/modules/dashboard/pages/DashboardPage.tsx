import { useEffect, useState } from 'react'
import { api } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const [stats, setStats] = useState({ sales: 0, products: 0, clients: 0 })
  const [error, setError] = useState('')
  useEffect(() => {
    if (!token) return
    void Promise.all([api.getSales(token), api.getProducts(token, 1, 100), user?.rol === 'Admin' ? api.getClientes(token) : Promise.resolve({ items: [] })])
      .then(([sales, products, clients]) => setStats({ sales: sales.items.length, products: products.items.length, clients: clients.items.length }))
      .catch((err) => setError(err instanceof Error ? err.message : 'No se pudieron cargar las métricas.'))
  }, [token, user?.rol])

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Panel principal</p>
          <h1>Bienvenido, {user?.nombre ?? 'Usuario'}</h1>
        </div>
      </header>
      {error && <p className="error-message">{error}</p>}

      <section className="stats-grid">
        <article className="stat-card">
          <span>Ventas del día</span>
          <strong>{stats.sales}</strong>
        </article>
        <article className="stat-card">
          <span>Productos</span>
          <strong>{stats.products}</strong>
        </article>
        <article className="stat-card">
          <span>Clientes</span>
          <strong>{stats.clients}</strong>
        </article>
      </section>
    </main>
  )
}
