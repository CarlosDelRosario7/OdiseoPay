import { useEffect, useState } from 'react'

import { api, type InventoryItem } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'

export default function InventoryPage() {
  const token = useAuthStore((state) => state.token)
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [error, setError] = useState('')
  const load = async () => { if (!token) return; try { setInventory((await api.getInventory(token)).items); setError('') } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo cargar el inventario.') } }
  useEffect(() => {
    if (!token) return
    void api.getInventory(token).then((response) => setInventory(response.items)).catch((err) => setError(err instanceof Error ? err.message : 'No se pudo cargar el inventario.'))
  }, [token])
  const update = async (item: InventoryItem, field: 'cantidad' | 'stock_minimo' | 'ubicacion', value: string) => { if (!token) return; try { await api.updateInventory(token, item.id_inventario, { [field]: field === 'ubicacion' ? value : Number(value) }); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo actualizar el inventario.') } }

  return (
    <section className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Inventario</p>
          <h1>Control de stock</h1>
        </div>
      </header>
      {error && <p className="error-message">{error}</p>}

      <section className="panel-card table-panel">
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Cantidad</th>
              <th>Ubicación</th>
              <th>Stock mínimo</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {inventory.map((item) => (
              <tr key={item.id_inventario}>
                <td>Producto #{item.id_producto}</td>
                <td><input type="number" min="0" defaultValue={item.cantidad} onBlur={(e) => void update(item, 'cantidad', e.target.value)} /></td>
                <td><input defaultValue={item.ubicacion ?? ''} onBlur={(e) => void update(item, 'ubicacion', e.target.value)} /></td>
                <td><input type="number" min="0" defaultValue={item.stock_minimo} onBlur={(e) => void update(item, 'stock_minimo', e.target.value)} /></td>
                <td>
                  {item.cantidad <= item.stock_minimo ? 'Bajo' : 'Normal'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  )
}
