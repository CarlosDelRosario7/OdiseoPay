import { useEffect, useState } from 'react'
import { api, type ProductSummary, type ProviderSummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'
import { formatCurrency } from '../../../shared/utils/validation'
import { Plus, Trash2 } from 'lucide-react'

type PurchaseRow = { id_producto: number; nombre: string; cantidad: number; precio: number }

export default function PurchasesPage() {
  const token = useAuthStore((state) => state.token)
  const [providers, setProviders] = useState<ProviderSummary[]>([])
  const [products, setProducts] = useState<ProductSummary[]>([])
  const [providerId, setProviderId] = useState('')
  const [rows, setRows] = useState<PurchaseRow[]>([])
  const [productSearch, setProductSearch] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    void Promise.all([api.getProviders(token), api.getProducts(token, 1, 100)]).then(([providerResponse, productResponse]) => { setProviders(providerResponse.items); setProducts(productResponse.items) }).catch((err) => setError(err instanceof Error ? err.message : 'No se pudieron cargar los datos de compra.'))
  }, [token])
  const suggestions = products.filter((product) => product.nombre.toLowerCase().includes(productSearch.toLowerCase()) && !rows.some((row) => row.id_producto === product.id_producto)).slice(0, 6)
  const submit = async (event: React.FormEvent) => { event.preventDefault(); if (!token) return; try { await api.createPurchase(token, { id_proveedor: Number(providerId), detalles: rows.map((row) => ({ id_producto: row.id_producto, cantidad: row.cantidad, precio: row.precio.toFixed(2) })) }); setRows([]); setProviderId(''); setMessage('Compra registrada y stock actualizado.'); setError('') } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo registrar la compra.') } }
  return <section className="page-shell"><header className="page-header"><div><p className="eyebrow">Abastecimiento</p><h1>Nueva compra</h1></div></header><form className="panel-card purchase-form" onSubmit={submit}><label>Proveedor<select required value={providerId} onChange={(e) => setProviderId(e.target.value)}><option value="">Selecciona un proveedor</option>{providers.map((provider) => <option key={provider.id_proveedor} value={provider.id_proveedor}>{provider.nombre}</option>)}</select></label><label>Buscar producto<span className="search-field"><input value={productSearch} onChange={(e) => setProductSearch(e.target.value)} placeholder="Escribe para buscar" /></span></label>{productSearch && <div className="suggestions">{suggestions.map((product) => <button type="button" key={product.id_producto} onClick={() => { setRows([...rows, { id_producto: product.id_producto, nombre: product.nombre, cantidad: 1, precio: Number(product.precio_compra ?? 0) }]); setProductSearch('') }}>{product.nombre}<Plus size={16} /></button>)}</div>}<div className="purchase-rows">{rows.map((row, index) => <div className="purchase-row" key={row.id_producto}><strong>{row.nombre}</strong><input type="number" min="1" value={row.cantidad} onChange={(e) => setRows(rows.map((item, itemIndex) => itemIndex === index ? { ...item, cantidad: Number(e.target.value) } : item))} /><input type="number" min="0" step="0.01" value={row.precio} onChange={(e) => setRows(rows.map((item, itemIndex) => itemIndex === index ? { ...item, precio: Number(e.target.value) } : item))} /><button type="button" className="icon-button remove-item" aria-label={`Quitar ${row.nombre}`} onClick={() => setRows(rows.filter((_, itemIndex) => itemIndex !== index))}><Trash2 size={18} /></button></div>)}</div><button type="submit" disabled={!rows.length}>Registrar compra</button></form>{message && <p className="success-message">{message}</p>}{error && <p className="error-message">{error}</p>}<p className="purchase-total">Total estimado: {formatCurrency(rows.reduce((sum, row) => sum + row.cantidad * row.precio, 0))}</p></section>
}
