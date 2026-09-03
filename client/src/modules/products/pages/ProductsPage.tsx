import { useEffect, useState } from 'react'

import { api, type ProductSummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'
import { formatCurrency } from '../../../shared/utils/validation'

const emptyProduct = { nombre: '', descripcion: '', precio_compra: '', precio_venta: '', id_categoria: '', id_proveedor: '' }

export default function ProductsPage() {
  const token = useAuthStore((state) => state.token)
  const role = useAuthStore((state) => state.user?.rol)
  const [products, setProducts] = useState<ProductSummary[]>([])
  const [form, setForm] = useState(emptyProduct)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  const load = async () => {
    if (!token) return
    try { setProducts((await api.getProducts(token, 1, 100)).items); setError('') }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudieron cargar los productos.') }
  }
  useEffect(() => {
    if (!token) return
    void api.getProducts(token, 1, 100).then((response) => setProducts(response.items)).catch((err) => setError(err instanceof Error ? err.message : 'No se pudieron cargar los productos.'))
  }, [token])
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); if (!token) return
    const data = { ...form, precio_compra: form.precio_compra, precio_venta: form.precio_venta, id_categoria: Number(form.id_categoria), id_proveedor: Number(form.id_proveedor) }
    try { if (editingId) await api.updateProduct(token, editingId, data); else await api.createProduct(token, data as never); setForm(emptyProduct); setEditingId(null); await load() }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudo guardar el producto.') }
  }
  const remove = async (id: number) => { if (!token || !window.confirm('¿Eliminar este producto?')) return; try { await api.deleteProduct(token, id); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo eliminar.') } }

  return (
    <section className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Catálogo</p>
          <h1>Productos</h1>
        </div>
      </header>

      {role === 'Admin' && <form className="panel-card form-grid" onSubmit={submit}>
        <h2>{editingId ? 'Editar producto' : 'Nuevo producto'}</h2>
        <input required placeholder="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
        <input placeholder="Descripción" value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
        <input required type="number" step="0.01" placeholder="Precio de compra" value={form.precio_compra} onChange={(e) => setForm({ ...form, precio_compra: e.target.value })} />
        <input required type="number" step="0.01" placeholder="Precio de venta" value={form.precio_venta} onChange={(e) => setForm({ ...form, precio_venta: e.target.value })} />
        <input required type="number" placeholder="ID categoría" value={form.id_categoria} onChange={(e) => setForm({ ...form, id_categoria: e.target.value })} />
        <input required type="number" placeholder="ID proveedor" value={form.id_proveedor} onChange={(e) => setForm({ ...form, id_proveedor: e.target.value })} />
        <button type="submit">Guardar</button>{editingId && <button type="button" className="secondary-button" onClick={() => { setEditingId(null); setForm(emptyProduct) }}>Cancelar</button>}
      </form>}
      {error && <p className="error-message">{error}</p>}

      <div className="card-list">
        <div className="panel-card">
          <strong>Productos activos</strong>
          <span>{products.length}</span>
        </div>
        <div className="panel-card">
          <strong>Stock bajo</strong>
          <span>{products.filter((product) => Number(product.precio_venta) <= 0).length}</span>
        </div>
        <div className="panel-card">
          <strong>Precio promedio</strong>
          <span>{formatCurrency(products.length ? products.reduce((sum, product) => sum + Number(product.precio_venta), 0) / products.length : 0)}</span>
        </div>
      </div>

      <section className="panel-card table-panel">
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Categoría</th>
              <th>Precio</th>
              <th>Stock</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id_producto}>
                <td>{product.nombre}</td>
                <td>{product.id_categoria}</td>
                <td>{formatCurrency(Number(product.precio_venta))}</td>
                <td>
                  {role === 'Admin' && <><button type="button" className="mini-button" onClick={() => { setEditingId(product.id_producto); setForm({ nombre: product.nombre, descripcion: product.descripcion ?? '', precio_compra: String(product.precio_compra ?? ''), precio_venta: String(product.precio_venta), id_categoria: String(product.id_categoria ?? ''), id_proveedor: String(product.id_proveedor ?? '') }) }}>Editar</button>
                  <button type="button" className="mini-button danger" onClick={() => void remove(product.id_producto)}>Eliminar</button></>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  )
}
