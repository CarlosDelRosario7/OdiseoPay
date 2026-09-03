import { useEffect, useState } from 'react'
import { Printer } from 'lucide-react'
import { api, type SaleSummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'
import { formatCurrency } from '../../../shared/utils/validation'

export default function SalesHistoryPage() {
  const token = useAuthStore((state) => state.token)
  const [sales, setSales] = useState<SaleSummary[]>([])
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [error, setError] = useState('')
  useEffect(() => { if (!token) return; void api.getSales(token).then((response) => setSales(response.items)).catch((err) => setError(err instanceof Error ? err.message : 'No se pudo cargar el historial.')) }, [token])
  const filtered = sales.filter((sale) => { const date = sale.fecha?.slice(0, 10) ?? ''; return (!from || date >= from) && (!to || date <= to) })
  const printReceipt = (sale: SaleSummary) => { const receipt = window.open('', '_blank', 'width=420,height=600'); if (!receipt) return; receipt.document.write(`<html lang="es"><head><title>Recibo #${sale.id_venta}</title><style>body{font-family:Arial;padding:24px}h1{font-size:20px}p{display:flex;justify-content:space-between;border-bottom:1px solid #ddd;padding:8px 0}</style></head><body><h1>OdiseoPay</h1><p><span>Recibo</span><strong>#${sale.id_venta}</strong></p><p><span>Fecha</span><span>${sale.fecha ?? 'N/D'}</span></p><p><span>Cliente</span><span>#${sale.id_cliente}</span></p><p><span>Usuario</span><span>#${sale.id_usuario}</span></p><script>window.print()</script></body></html>`); receipt.document.close() }
  return <section className="page-shell"><header className="page-header"><div><p className="eyebrow">Ventas</p><h1>Historial de ventas</h1></div></header><section className="panel-card filters"><label>Desde<input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></label><label>Hasta<input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></label></section>{error && <p className="error-message">{error}</p>}<section className="panel-card table-panel"><table><thead><tr><th>Venta</th><th>Fecha</th><th>Cliente</th><th>Usuario</th><th>Recibo</th></tr></thead><tbody>{filtered.map((sale) => <tr key={sale.id_venta}><td>#{sale.id_venta}</td><td>{sale.fecha ? new Date(sale.fecha).toLocaleString('es-DO') : '-'}</td><td>#{sale.id_cliente}</td><td>#{sale.id_usuario}</td><td><button type="button" className="icon-button" aria-label="Imprimir recibo" onClick={() => printReceipt(sale)}><Printer size={18} /></button></td></tr>)}</tbody></table></section><p className="muted-text">{filtered.length} ventas encontradas. {formatCurrency(0)} no incluye totales porque el backend no los devuelve en el historial.</p></section>
}
