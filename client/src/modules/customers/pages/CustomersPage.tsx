import { useEffect, useState } from 'react'

import { api, type ClientSummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'

export default function CustomersPage() {
  const token = useAuthStore((state) => state.token)
  const [customers, setCustomers] = useState<ClientSummary[]>([])
  const [form, setForm] = useState({ nombre: '', apellido: '', telefono: '', correo: '' })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const load = async () => { if (!token) return; try { setCustomers((await api.getClientes(token)).items); setError('') } catch (err) { setError(err instanceof Error ? err.message : 'No se pudieron cargar los clientes.') } }
  useEffect(() => {
    if (!token) return
    void api.getClientes(token).then((response) => setCustomers(response.items)).catch((err) => setError(err instanceof Error ? err.message : 'No se pudieron cargar los clientes.'))
  }, [token])
  const submit = async (event: React.FormEvent) => { event.preventDefault(); if (!token) return; try { if (editingId) await api.updateClient(token, editingId, form); else await api.createClient(token, form); setForm({ nombre: '', apellido: '', telefono: '', correo: '' }); setEditingId(null); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo guardar el cliente.') } }
  const remove = async (id: number) => { if (!token || !window.confirm('¿Eliminar este cliente?')) return; try { await api.deleteClient(token, id); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo eliminar.') } }

  return (
    <section className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">CRM</p>
          <h1>Clientes</h1>
        </div>
      </header>

      <form className="panel-card form-grid" onSubmit={submit}>
        <h2>{editingId ? 'Editar cliente' : 'Nuevo cliente'}</h2>
        <input required placeholder="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
        <input required placeholder="Apellido" value={form.apellido} onChange={(e) => setForm({ ...form, apellido: e.target.value })} />
        <input placeholder="Teléfono" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
        <input type="email" placeholder="Correo" value={form.correo} onChange={(e) => setForm({ ...form, correo: e.target.value })} />
        <button type="submit">Guardar cliente</button>{editingId && <button type="button" className="secondary-button" onClick={() => { setEditingId(null); setForm({ nombre: '', apellido: '', telefono: '', correo: '' }) }}>Cancelar</button>}
      </form>
      {error && <p className="error-message">{error}</p>}

      <section className="panel-card table-panel">
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Teléfono</th>
              <th>Correo</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((customer) => (
              <tr key={customer.id_cliente}>
                <td>{customer.nombre} {customer.apellido}</td>
                <td>{customer.telefono}</td>
                <td>{customer.correo}</td>
                <td>
                  <button type="button" className="mini-button" onClick={() => { setEditingId(customer.id_cliente); setForm({ nombre: customer.nombre, apellido: customer.apellido ?? '', telefono: customer.telefono ?? '', correo: customer.correo ?? '' }) }}>Editar</button><button type="button" className="mini-button danger" onClick={() => void remove(customer.id_cliente)}>Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  )
}
