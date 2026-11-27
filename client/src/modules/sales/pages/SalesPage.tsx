
import { useEffect, useState } from 'react'

import { useAuthStore } from '../../../shared/store/authStore'
import { api } from '../../../shared/lib/api'
import { formatCurrency } from '../../../shared/utils/validation'
import type {
  ClientSummary,
  InventoryItem,
  ProductSummary,
} from '../../../shared/lib/api'
import { Search, Trash2 } from 'lucide-react'

type SaleItem = {
  id_producto: number
  nombre: string
  cantidad: number
  precio: number
}

export default function SalesPage() {
  const token = useAuthStore((state) => state.token)
  const role = useAuthStore((state) => state.user?.rol)

  const [products, setProducts] = useState<ProductSummary[]>([])
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [loadingInventory, setLoadingInventory] = useState(true)
  const [saving, setSaving] = useState(false)
  const [clients, setClients] = useState<ClientSummary[]>([])
  const [items, setItems] = useState<SaleItem[]>([])
  const [clienteId, setClienteId] = useState('')
  const [montoRecibido, setMontoRecibido] = useState('200')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [productSearch, setProductSearch] = useState('')

  const subtotal = items.reduce(
    (sum, item) => sum + item.cantidad * item.precio,
    0,
  )

  const itbis = subtotal * 0.18
  const total = subtotal + itbis
  const cambio = Number(montoRecibido || 0) - total

  const stockByProduct = new Map(
    inventory.map((entry) => [entry.id_producto, entry.cantidad]),
  )

  const invalidQuantity = items.some(
    (item) =>
      !Number.isInteger(item.cantidad) ||
      item.cantidad < 1 ||
      item.cantidad > (stockByProduct.get(item.id_producto) ?? 0),
  )

  const suggestions = products
    .filter(
      (product) =>
        product.nombre
          .toLowerCase()
          .includes(productSearch.toLowerCase()) &&
        !items.some(
          (item) => item.id_producto === product.id_producto,
        ),
    )
    .slice(0, 6)

  const refreshInventory = async (currentToken: string) => {
    const response = await api.getInventory(currentToken)
    setInventory(response.items)
  }

  useEffect(() => {
    if (!token) return

    void api
      .getProducts(token, 1, 100)
      .then((response) => setProducts(response.items))
      .catch((err) =>
        setError(
          err instanceof Error
            ? err.message
            : 'No se pudieron cargar los productos.',
        ),
      )

    setLoadingInventory(true)

    void refreshInventory(token)
      .catch((err) =>
        setError(
          err instanceof Error
            ? err.message
            : 'No se pudo consultar el inventario.',
        ),
      )
      .finally(() => setLoadingInventory(false))

    if (role === 'Admin') {
      void api
        .getClientes(token)
        .then((response) => setClients(response.items))
        .catch(() => undefined)
    }
  }, [token, role])

  const handleCreateSale = async () => {
    if (!token || saving) return

    if (!clienteId || items.length === 0 || invalidQuantity) {
      setError(
        'Selecciona un cliente y verifica que todas las cantidades sean válidas y estén disponibles.',
      )
      return
    }

    try {
      setSaving(true)
      setError('')
      setSuccess('')

      // Comprobar nuevamente las existencias antes de registrar.
      const latest = await api.getInventory(token)

      const latestStock = new Map(
        latest.items.map((entry) => [
          entry.id_producto,
          entry.cantidad,
        ]),
      )

      setInventory(latest.items)

      if (
        items.some(
          (item) =>
            item.cantidad >
            (latestStock.get(item.id_producto) ?? 0),
        )
      ) {
        throw new Error(
          'El inventario cambió. Ajusta las cantidades antes de registrar la venta.',
        )
      }

      await api.createSale(token, {
        id_cliente: Number(clienteId),
        detalles: items.map((item) => ({
          id_producto: item.id_producto,
          cantidad: item.cantidad,
          precio: String(item.precio),
        })),
      })

      setSuccess(
        'Venta registrada correctamente. Inventario actualizado.',
      )

      setItems([])
      setProductSearch('')

      await refreshInventory(token)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo registrar la venta.',
      )
    } finally {
      setSaving(false)
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
            Cliente

            {role === 'Admin' ? (
              <select
                required
                value={clienteId}
                onChange={(e) => setClienteId(e.target.value)}
              >
                <option value="">
                  Selecciona un cliente
                </option>

                {clients.map((client) => (
                  <option
                    key={client.id_cliente}
                    value={client.id_cliente}
                  >
                    {client.nombre} {client.apellido}
                  </option>
                ))}
              </select>
            ) : (
              <input
                required
                type="number"
                min="1"
                placeholder="ID del cliente"
                value={clienteId}
                onChange={(e) => setClienteId(e.target.value)}
              />
            )}
          </label>

          <div className="sale-items">
            {items.map((item, index) => {
              const stockDisponible =
                stockByProduct.get(item.id_producto) ?? 0

              const stockInsuficiente =
                !loadingInventory &&
                item.cantidad > stockDisponible

              const cantidadInvalida =
                !Number.isInteger(item.cantidad) ||
                item.cantidad < 1

              return (
                <div
                  key={item.id_producto}
                  style={{
                    width: '100%',
                    marginBottom: '16px',
                  }}
                >
                  {/* Fila del producto */}
                  <div className="sale-item-row">
                    <div className="sale-product-info">
                      <input
                        value={item.nombre}
                        readOnly
                      />

                      <small>
                        Disponibles:{' '}
                        {loadingInventory
                          ? 'Consultando...'
                          : stockDisponible}{' '}
                        unidades
                      </small>
                    </div>

                    {/* Cantidad a vender */}
                    <input
                      type="number"
                      min={1}
                      max={stockDisponible}
                      step={1}
                      aria-label={`Cantidad a vender de ${item.nombre}`}
                      aria-invalid={
                        stockInsuficiente ||
                        cantidadInvalida
                      }
                      value={item.cantidad}
                      onChange={(e) => {
                        const next = Number(e.target.value)

                        setItems((prev) =>
                          prev.map((entry, idx) =>
                            idx === index
                              ? {
                                  ...entry,
                                  cantidad: Number.isNaN(next)
                                    ? 0
                                    : next,
                                }
                              : entry,
                          ),
                        )
                      }}
                    />

                    {/* Precio */}
                    <input
                      type="number"
                      step="0.01"
                      value={item.precio}
                      aria-label={`Precio de ${item.nombre}`}
                      onChange={(e) => {
                        const next = Number(e.target.value)

                        setItems((prev) =>
                          prev.map((entry, idx) =>
                            idx === index
                              ? {
                                  ...entry,
                                  precio: Number.isNaN(next)
                                    ? 0
                                    : next,
                                }
                              : entry,
                          ),
                        )
                      }}
                    />

                    {/* Eliminar producto */}
                    <button
                      type="button"
                      className="icon-button remove-item"
                      aria-label={`Quitar ${item.nombre}`}
                      onClick={() =>
                        setItems((prev) =>
                          prev.filter(
                            (_, idx) => idx !== index,
                          ),
                        )
                      }
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>

                  {/* Nota de stock debajo de la fila */}
                  {stockInsuficiente && (
                    <div
                      role="alert"
                      style={{
                        display: 'block',
                        width: '100%',
                        boxSizing: 'border-box',
                        marginTop: '10px',
                        padding: '12px 14px',
                        borderRadius: '8px',
                        border:
                          '1px solid rgba(239, 68, 68, 0.30)',
                        backgroundColor:
                          'rgba(239, 68, 68, 0.08)',
                        color: '#f87171',
                        fontSize: '13px',
                        lineHeight: '1.6',
                      }}
                    >
                      <strong>⚠️ Nota:</strong>{' '}
                      Solo hay disponibles{' '}
                      <strong>{stockDisponible}</strong>{' '}
                      unidades de{' '}
                      <strong>{item.nombre}</strong>.
                      Reduce la cantidad para continuar.
                    </div>
                  )}

                  {/* Nota para cantidades inválidas */}
                  {!stockInsuficiente &&
                    cantidadInvalida && (
                      <div
                        role="alert"
                        style={{
                          display: 'block',
                          width: '100%',
                          boxSizing: 'border-box',
                          marginTop: '10px',
                          padding: '12px 14px',
                          borderRadius: '8px',
                          backgroundColor:
                            'rgba(239, 68, 68, 0.08)',
                          color: '#f87171',
                          fontSize: '13px',
                        }}
                      >
                        ⚠️ La cantidad debe ser un
                        número entero mayor que cero.
                      </div>
                    )}
                </div>
              )
            })}
          </div>

          {/* Buscar productos */}
          <label>
            Buscar producto

            <span className="search-field">
              <Search size={18} />

              <input
                value={productSearch}
                onChange={(e) =>
                  setProductSearch(e.target.value)
                }
                placeholder="Escribe el nombre del producto"
              />
            </span>
          </label>

          {productSearch && (
            <div
              className="suggestions"
              role="listbox"
            >
              {suggestions.map((product) => {
                const disponibles =
                  stockByProduct.get(product.id_producto) ?? 0

                return (
                  <button
                    type="button"
                    key={product.id_producto}
                    disabled={
                      loadingInventory ||
                      disponibles < 1
                    }
                    onClick={() => {
                      setItems((prev) => [
                        ...prev,
                        {
                          id_producto: product.id_producto,
                          nombre: product.nombre,
                          cantidad: 1,
                          precio: Number(
                            product.precio_venta,
                          ),
                        },
                      ])

                      setProductSearch('')
                      setError('')
                    }}
                  >
                    {product.nombre}

                    <span>
                      {formatCurrency(
                        Number(product.precio_venta),
                      )}{' '}
                      · Stock:{' '}
                      {loadingInventory
                        ? '...'
                        : disponibles}
                    </span>
                  </button>
                )
              })}

              {!suggestions.length && (
                <p>No hay productos coincidentes.</p>
              )}
            </div>
          )}
        </div>

        {/* Resumen de la venta */}
        <aside className="summary-panel">
          <h2>Resumen</h2>

          <div className="summary-row">
            <span>Subtotal</span>
            <strong>
              {formatCurrency(subtotal)}
            </strong>
          </div>

          <div className="summary-row">
            <span>ITBIS</span>
            <strong>
              {formatCurrency(itbis)}
            </strong>
          </div>

          <div className="summary-row total">
            <span>Total</span>
            <strong>
              {formatCurrency(total)}
            </strong>
          </div>

          <label>
            Monto recibido

            <input
              value={montoRecibido}
              onChange={(e) =>
                setMontoRecibido(e.target.value)
              }
            />
          </label>

          <div className="summary-row total">
            <span>Cambio</span>
            <strong>
              {formatCurrency(cambio)}
            </strong>
          </div>

          {error && (
            <p className="error-message">
              {error}
            </p>
          )}

          {success && (
            <p className="success-message">
              {success}
            </p>
          )}

          <button
            type="button"
            disabled={
              saving ||
              loadingInventory ||
              !items.length ||
              !clienteId ||
              invalidQuantity ||
              cambio < 0
            }
            onClick={handleCreateSale}
          >
            {saving
              ? 'Registrando...'
              : 'Registrar venta'}
          </button>
        </aside>
      </section>
    </main>
  )
}
