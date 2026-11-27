import { useCallback, useEffect, useState } from 'react'

import { api, type CancellationInfo, type PurchaseSummary, type SaleSummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'

type Kind = 'ventas' | 'compras'
type Transaction = SaleSummary | PurchaseSummary

function transactionId(item: Transaction): number {
  return 'id_venta' in item ? item.id_venta : item.id_compra
}

function localTime(utc: string): string {
  return new Intl.DateTimeFormat('es-DO', {
    dateStyle: 'short', timeStyle: 'medium', timeZone: 'America/Santo_Domingo',
  }).format(new Date(utc))
}

function CancellationDetails({ info }: { info: CancellationInfo }) {
  return (
    <div>
      Anulada por {info.usuario} (#{info.id_usuario}) el {localTime(info.fecha_utc)} (Santo Domingo).
      {' '}Motivo: {info.motivo}
    </div>
  )
}

function printSale(item: SaleSummary) {
  const popup = window.open('', '_blank', 'width=420,height=600')
  if (!popup) return
  popup.document.title = `Recibo #${item.id_venta}`
  const heading = popup.document.createElement('h1')
  heading.textContent = `OdiseoPay — Recibo #${item.id_venta}`
  popup.document.body.append(heading)
  for (const text of [
    `Fecha: ${item.fecha ?? 'N/D'}`,
    `Cliente: #${item.id_cliente}`,
    `Usuario: #${item.id_usuario}`,
    `Estado: ${item.estado ?? 'ACTIVA'}`,
  ]) {
    const line = popup.document.createElement('p')
    line.textContent = text
    popup.document.body.append(line)
  }
  popup.print()
}

export default function TransactionsHistoryPage({ kind }: { kind: Kind }) {
  const token = useAuthStore((state) => state.token)
  const role = useAuthStore((state) => state.user?.rol)
  const [items, setItems] = useState<Transaction[]>([])
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [busyId, setBusyId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const load = useCallback(async () => {
    if (!token) return
    const response = kind === 'ventas'
      ? await api.getSales(token, page)
      : await api.getPurchases(token, page)
    setItems(response.items)
    setPages(response.pages)
  }, [kind, page, token])

  useEffect(() => {
    let active = true
    if (!token) return
    const request = kind === 'ventas' ? api.getSales(token, page) : api.getPurchases(token, page)
    void request.then((response) => {
      if (active) { setItems(response.items); setPages(response.pages) }
    }).catch((err) => {
      if (active) setError(err instanceof Error ? err.message : 'No se pudo cargar el historial.')
    })
    return () => { active = false }
  }, [kind, page, token])

  const cancel = async (item: Transaction) => {
    if (!token || busyId !== null) return
    const motivo = window.prompt(`Indique el motivo de anulación de ${kind === 'ventas' ? 'la venta' : 'la compra'} #${transactionId(item)}:`)
    if (motivo === null) return
    if (!motivo.trim() || motivo.trim().length > 255) {
      setError('El motivo es obligatorio y no puede exceder 255 caracteres.')
      return
    }
    if (!window.confirm('¿Confirmar la anulación y la reversión del inventario?')) return
    setBusyId(transactionId(item))
    setError('')
    setMessage('')
    try {
      if (kind === 'ventas') await api.cancelSale(token, transactionId(item), motivo)
      else await api.cancelPurchase(token, transactionId(item), motivo)
      setMessage('Operación anulada. Se registró la auditoría y el movimiento de inventario.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo anular la operación.')
    } finally {
      setBusyId(null)
    }
  }

  const filtered = items.filter((item) => {
    const date = item.fecha?.slice(0, 10) ?? ''
    return (!from || date >= from) && (!to || date <= to)
  })

  return (
    <section className="page-shell">
      <header className="page-header"><div><p className="eyebrow">{kind === 'ventas' ? 'Ventas' : 'Compras'}</p><h1>Historial de {kind}</h1></div></header>
      <section className="panel-card filters">
        <label>Desde<input type="date" value={from} onChange={(event) => setFrom(event.target.value)} /></label>
        <label>Hasta<input type="date" value={to} onChange={(event) => setTo(event.target.value)} /></label>
      </section>
      <p className="muted-text">El filtro de fecha se aplica a la página mostrada.</p>
      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}
      <section className="panel-card table-panel">
        <table>
          <thead><tr><th>Operación</th><th>Fecha</th><th>{kind === 'ventas' ? 'Cliente' : 'Proveedor'}</th><th>Usuario</th><th>Estado y auditoría</th><th>Acciones</th></tr></thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={transactionId(item)}>
                <td>#{transactionId(item)}</td>
                <td>{item.fecha ? new Date(item.fecha).toLocaleString('es-DO') : '—'}</td>
                <td>#{'id_cliente' in item ? item.id_cliente : item.id_proveedor}</td>
                <td>#{item.id_usuario}</td>
                <td>{item.anulacion ? <CancellationDetails info={item.anulacion} /> : 'Activa'}</td>
                <td>
                  {'id_venta' in item && <button type="button" onClick={() => printSale(item)}>Recibo</button>}
                  {role === 'Admin' && !item.anulacion && (
                    <button type="button" disabled={busyId !== null} onClick={() => void cancel(item)}>
                      {busyId === transactionId(item) ? 'Anulando...' : 'Anular'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="muted-text">Página {page} de {Math.max(pages, 1)}. Los recibos no incluyen totales porque el backend no los devuelve en el historial.</p>
      <div>
        <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Anterior</button>
        <button type="button" disabled={page >= pages} onClick={() => setPage((value) => value + 1)}>Siguiente</button>
      </div>
    </section>
  )
}
