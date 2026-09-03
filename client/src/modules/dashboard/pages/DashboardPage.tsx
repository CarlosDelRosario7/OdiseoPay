import { useAuthStore } from '../../../shared/store/authStore'

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user)

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Panel principal</p>
          <h1>Bienvenido, {user?.nombre ?? 'Usuario'}</h1>
        </div>
      </header>

      <section className="stats-grid">
        <article className="stat-card">
          <span>Ventas del día</span>
          <strong>0</strong>
        </article>
        <article className="stat-card">
          <span>Productos</span>
          <strong>0</strong>
        </article>
        <article className="stat-card">
          <span>Clientes</span>
          <strong>0</strong>
        </article>
      </section>
    </main>
  )
}
