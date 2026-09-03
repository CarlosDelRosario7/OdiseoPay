import { useState } from 'react'

import { useAuthStore } from '../../../shared/store/authStore'
import { api } from '../../../shared/lib/api'
import { formatCurrency } from '../../../shared/utils/validation'

type SaleItem = {
  id_producto: number
  nombre: string
  cantidad: number
  precio: number
}

export default function SalesPage() {
  const token = useAuthStore((state) => state.token)
  const [items, setItems] = useState<SaleItem[]>([
    { id_producto: 1, nombre: 'Agua 600ml', cantidad: 2, precio: 8.5 },
  ])
  const [clienteId, setClienteId] = useState('1')
  const [montoRecibido, setMontoRecibido] = useState('200')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const subtotal = items.reduce((sum, item) => sum + item.cantidad * item.precio, 0)
  const itbis = subtotal * 0.18
  const total = subtotal + itbis
  const cambio = Number(montoRecibido || 0) - total

  const handleCreateSale = async () => {
    if (!token) return

    try {
      setError('')
      setSuccess('')

      await api.createSale(token, {
        id_cliente: Number(clienteId),
        detalles: items.map((item) => ({
          id_producto: item.id_producto,
          cantidad: item.cantidad,
          precio: String(item.precio),
        })),
      })

      setSuccess('Venta registrada correctamente.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar la venta.')
    }
  }

  return (
    <main className="page-shell sales-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Ventas</p>
          <h1>Nueva venta</h1>
        </div>
      </header>

      <section className="sale-layout">
        <div className="sale-panel">
          <label>
            ID del cliente
            <input value={clienteId} onChange={(e) => setClienteId(e.target.value)} />
          </label>

          <div className="sale-items">
            {items.map((item, index) => (
              <div key={`${item.id_producto}-${index}`} className="sale-item-row">
                <input value={item.nombre} readOnly />
                <input
                  type="number"
                  min={1}
                  value={item.cantidad}
                  onChange={(e) => {
                    const next = Number(e.target.value)
                    setItems((prev) =>
                      prev.map((entry, idx) =>
                        idx === index
                          ? { ...entry, cantidad: Number.isNaN(next) ? 1 : next }
                          : entry,
                      ),
                    )
                  }}
                />
                <input
                  type="number"
                  step="0.01"
                  value={item.precio}
                  onChange={(e) => {
                    const next = Number(e.target.value)
                    setItems((prev) =>
                      prev.map((entry, idx) =>
                        idx === index
                          ? { ...entry, precio: Number.isNaN(next) ? 0 : next }
                          : entry,
                      ),
                    )
                  }}
                />
              </div>
            ))}
          </div>

          <button type="button" className="secondary-button" onClick={() => setItems((prev) => [...prev, { id_producto: Date.now(), nombre: 'Producto', cantidad: 1, precio: 0 }])}>
            Agregar producto
          </button>
        </div>

        <aside className="summary-panel">
          <h2>Resumen</h2>
          <div className="summary-row">
            <span>Subtotal</span>
            <strong>{formatCurrency(subtotal)}</strong>
          </div>
          <div className="summary-row">
            <span>ITBIS</span>
            <strong>{formatCurrency(itbis)}</strong>
          </div>
          <div className="summary-row total">
            <span>Total</span>
            <strong>{formatCurrency(total)}</strong>
          </div>

          <label>
            Monto recibido
            <input value={montoRecibido} onChange={(e) => setMontoRecibido(e.target.value)} />
          </label>

          <div className="summary-row total">
            <span>Cambio</span>
            <strong>{formatCurrency(cambio)}</strong>
          </div>

          {error ? <p className="error-message">{error}</p> : null}
          {success ? <p className="success-message">{success}</p> : null}

          <button type="button" onClick={handleCreateSale}>Registrar venta</button>
        </aside>
      </section>
    </main>
  )
}
