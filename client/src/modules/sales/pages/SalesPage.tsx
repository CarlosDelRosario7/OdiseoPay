import { useEffect, useState } from 'react'
import { Search, Trash2 } from 'lucide-react'

import { api, type ClientSummary, type InventoryItem, type ProductSummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'
import { formatCurrency } from '../../../shared/utils/validation'

type SaleItem = {
  id_producto: number
  nombre: string
  cantidad: number
  precio: number
}

async function fetchInventory(token: string): Promise<InventoryItem[]> {
  const firstPage = await api.getInventory(token)
  const entries = [...firstPage.items]
  for (let page = 2; page <= firstPage.pages; page += 1) {
    const response = await api.getInventory(token, page)
    entries.push(...response.items)
  }
  return entries
}

export default function SalesPage() {
  const token = useAuthStore((state) => state.token)
  const [products, setProducts] = useState<ProductSummary[]>([])
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [loadingInventory, setLoadingInventory] = useState(true)
  const [clients, setClients] = useState<ClientSummary[]>([])
  const [items, setItems] = useState<SaleItem[]>([])
  const [clienteId, setClienteId] = useState('')
  const [montoRecibido, setMontoRecibido] = useState('200')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [productSearch, setProductSearch] = useState('')

  const subtotal = items.reduce((sum, item) => sum + item.cantidad * item.precio, 0)
  const itbis = subtotal * 0.18
  const total = subtotal + itbis
  const received = Number(montoRecibido || 0)
  const cambio = received - total
  const stockByProduct = new Map(inventory.map((entry) => [entry.id_producto, entry.cantidad]))
  const invalidQuantity = items.some((item) =>
    !Number.isInteger(item.cantidad) ||
    item.cantidad < 1 ||
    item.cantidad > (stockByProduct.get(item.id_producto) ?? 0),
  )
  const suggestions = products
    .filter((product) =>
      product.nombre.toLowerCase().includes(productSearch.toLowerCase()) &&
      !items.some((item) => item.id_producto === product.id_producto),
    )
    .slice(0, 6)

  useEffect(() => {
    if (!token) return
    let active = true
    void api.getProducts(token, 1, 100)
      .then((response) => { if (active) setProducts(response.items) })
      .catch((err) => { if (active) setError(err instanceof Error ? err.message : 'No se pudieron cargar los productos.') })
    void api.getClientes(token)
      .then((response) => { if (active) setClients(response.items) })
      .catch((err) => { if (active) setError(err instanceof Error ? err.message : 'No se pudieron cargar los clientes.') })
    void fetchInventory(token)
      .then((entries) => { if (active) setInventory(entries) })
      .catch((err) => { if (active) setError(err instanceof Error ? err.message : 'No se pudo consultar el inventario.') })
      .finally(() => { if (active) setLoadingInventory(false) })
    return () => { active = false }
  }, [token])

  const handleCreateSale = async () => {
    if (!token || submitting) return
    if (!clienteId || !items.length || invalidQuantity || !Number.isFinite(received) || cambio < 0) {
      setError('Selecciona un cliente y verifica las cantidades y el monto recibido.')
      return
    }

    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      // La comprobación final de stock y precio también se realiza en el backend.
      const latest = await fetchInventory(token)
      setInventory(latest)
      const latestStock = new Map(latest.map((entry) => [entry.id_producto, entry.cantidad]))
      if (items.some((item) => item.cantidad > (latestStock.get(item.id_producto) ?? 0))) {
        throw new Error('El inventario cambió. Ajusta las cantidades antes de registrar la venta.')
      }

      await api.createSale(token, {
        id_cliente: Number(clienteId),
        detalles: items.map((item) => ({
          id_producto: item.id_producto,
          cantidad: item.cantidad,
          precio: String(item.precio),
        })),
      })

      setSuccess('Venta registrada correctamente. Inventario actualizado.')
      setItems([])
      setClienteId('')
      setProductSearch('')
      try {
        const [newProducts, newInventory] = await Promise.all([
          api.getProducts(token, 1, 100),
          fetchInventory(token),
        ])
        setProducts(newProducts.items)
        setInventory(newInventory)
      } catch {
        setError('La venta se registró, pero no se pudieron actualizar los datos. Recarga la página.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar la venta.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="page-shell sales-shell">
      <header className="page-header">
        <div><p className="eyebrow">Ventas</p><h1>Nueva venta</h1></div>
      </header>

      <section className="sale-layout">
        <div className="sale-panel">
          <label>
            Cliente
            <select required value={clienteId} onChange={(event) => setClienteId(event.target.value)}>
              <option value="">Selecciona un cliente</option>
              {clients.map((client) => (
                <option key={client.id_cliente} value={client.id_cliente}>
                  {client.nombre} {client.apellido}
                </option>
              ))}
            </select>
          </label>

          <div className="sale-items">
            {items.map((item, index) => {
              const available = stockByProduct.get(item.id_producto) ?? 0
              const insufficient = !loadingInventory && item.cantidad > available
              const invalid = !Number.isInteger(item.cantidad) || item.cantidad < 1

              return (
                <div key={item.id_producto} style={{ width: '100%', marginBottom: '16px' }}>
                  <div className="sale-item-row">
                    <div className="sale-product-info">
                      <input value={item.nombre} readOnly />
                      <small>Disponibles: {loadingInventory ? 'Consultando...' : available} unidades</small>
                    </div>
                    <input
                      type="number"
                      min={1}
                      max={available}
                      step={1}
                      aria-label={`Cantidad a vender de ${item.nombre}`}
                      aria-invalid={insufficient || invalid}
                      value={item.cantidad}
                      onChange={(event) => {
                        const next = Number(event.target.value)
                        setItems((previous) => previous.map((entry, idx) =>
                          idx === index ? { ...entry, cantidad: Number.isNaN(next) ? 0 : next } : entry,
                        ))
                      }}
                    />
                    <input
                      type="number"
                      step="0.01"
                      value={item.precio}
                      aria-label={`Precio de ${item.nombre}`}
                      readOnly
                    />
                    <button
                      type="button"
                      className="icon-button remove-item"
                      aria-label={`Quitar ${item.nombre}`}
                      onClick={() => setItems((previous) => previous.filter((_, idx) => idx !== index))}
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                  {insufficient && (
                    <div role="alert" className="error-message">
                      Solo hay disponibles {available} unidades de {item.nombre}. Reduce la cantidad para continuar.
                    </div>
                  )}
                  {!insufficient && invalid && (
                    <div role="alert" className="error-message">
                      La cantidad debe ser un número entero mayor que cero.
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          <label>
            Buscar producto
            <span className="search-field">
              <Search size={18} />
              <input
                value={productSearch}
                onChange={(event) => setProductSearch(event.target.value)}
                placeholder="Escribe el nombre del producto"
              />
            </span>
          </label>
          {productSearch && (
            <div className="suggestions" role="listbox">
              {suggestions.map((product) => {
                const available = stockByProduct.get(product.id_producto) ?? 0
                return (
                  <button
                    type="button"
                    key={product.id_producto}
                    disabled={loadingInventory || available < 1}
                    onClick={() => {
                      setItems((previous) => [...previous, {
                        id_producto: product.id_producto,
                        nombre: product.nombre,
                        cantidad: 1,
                        precio: Number(product.precio_venta),
                      }])
                      setProductSearch('')
                      setError('')
                    }}
                  >
                    {product.nombre}
                    <span>{formatCurrency(Number(product.precio_venta))} · Stock: {loadingInventory ? '...' : available}</span>
                  </button>
                )
              })}
              {!suggestions.length && <p>No hay productos coincidentes.</p>}
            </div>
          )}
        </div>

        <aside className="summary-panel">
          <h2>Resumen</h2>
          <div className="summary-row"><span>Subtotal</span><strong>{formatCurrency(subtotal)}</strong></div>
          <div className="summary-row"><span>ITBIS</span><strong>{formatCurrency(itbis)}</strong></div>
          <div className="summary-row total"><span>Total</span><strong>{formatCurrency(total)}</strong></div>
          <label>
            Monto recibido
            <input type="number" min="0" step="0.01" value={montoRecibido} onChange={(event) => setMontoRecibido(event.target.value)} />
          </label>
          <div className="summary-row total"><span>Cambio</span><strong>{formatCurrency(cambio)}</strong></div>
          {error && <p className="error-message">{error}</p>}
          {success && <p className="success-message">{success}</p>}
          <button
            type="button"
            disabled={submitting || loadingInventory || !items.length || !clienteId || invalidQuantity || !Number.isFinite(received) || cambio < 0}
            onClick={handleCreateSale}
          >
            {submitting ? 'Registrando...' : 'Registrar venta'}
          </button>
        </aside>
      </section>
    </main>
  )
}
