import { useEffect, useState } from 'react'

import { api, type LowStockResponse } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'

export default function LowStockPage() {
  const token = useAuthStore((state) => state.token)
  const [input, setInput] = useState('')
  const [threshold, setThreshold] = useState<number | null>(null)
  const [page, setPage] = useState(1)
  const [report, setReport] = useState<LowStockResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    let active = true
    void api.getLowStock(token, page, threshold)
      .then((result) => {
        if (active) {
          setReport(result)
          setError('')
        }
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : 'No se pudo cargar el reporte.')
      })
    return () => { active = false }
  }, [token, page, threshold])

  const applyThreshold = () => {
    const value = Number(input)
    if (!input.trim() || !Number.isInteger(value) || value < 0) {
      setError('El umbral debe ser un entero mayor o igual a 0.')
      return
    }
    setError('')
    setPage(1)
    setThreshold(value)
  }

  const useProductMinimum = () => {
    setError('')
    setInput('')
    setPage(1)
    setThreshold(null)
  }

  return (
    <section className="page-shell">
      <header className="page-header">
        <div><p className="eyebrow">Reportes</p><h1>Productos con bajo stock</h1></div>
      </header>
      <section className="panel-card filters">
        <label>Umbral global<input type="number" min="0" step="1" value={input} onChange={(event) => setInput(event.target.value)} /></label>
        <button type="button" onClick={applyThreshold}>Aplicar umbral</button>
        <button type="button" onClick={useProductMinimum}>Usar stock mínimo de cada producto</button>
      </section>
      <p className="muted-text">
        {threshold === null ? 'Comparando con el mínimo de cada producto.' : `Comparando con el umbral global de ${threshold}.`}
        {' '}Se muestran existencias inferiores al umbral.
      </p>
      {error && <p className="error-message">{error}</p>}
      <section className="panel-card table-panel">
        <table>
          <thead><tr><th>Producto</th><th>Existencias</th><th>Stock mínimo</th><th>Ubicación</th></tr></thead>
          <tbody>
            {report?.items.map((item) => (
              <tr key={item.id_inventario}>
                <td>{item.nombre_producto ?? `Producto #${item.id_producto}`}</td>
                <td>{item.cantidad}</td><td>{item.stock_minimo}</td><td>{item.ubicacion || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {report && <p className="muted-text">{report.total} productos encontrados. Página {report.page} de {Math.max(report.pages, 1)}.</p>}
      <div>
        <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Anterior</button>
        <button type="button" disabled={!report || page >= report.pages} onClick={() => setPage((value) => value + 1)}>Siguiente</button>
      </div>
    </section>
  )
}
