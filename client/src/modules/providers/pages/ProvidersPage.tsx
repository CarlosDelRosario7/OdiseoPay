import { useEffect, useState } from 'react'
import { Pencil, Trash2 } from 'lucide-react'

import { api, type ProviderSummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'

const emptyProvider = { nombre: '', telefono: '', correo: '', direccion: '' }

export default function ProvidersPage() {
  const token = useAuthStore((state) => state.token)
  const [providers, setProviders] = useState<ProviderSummary[]>([])
  const [form, setForm] = useState(emptyProvider)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  const load = async () => {
    if (!token) return
    try { setProviders((await api.getProviders(token)).items); setError('') }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudieron cargar los proveedores.') }
  }
  useEffect(() => {
    if (!token) return
    void api.getProviders(token).then((response) => setProviders(response.items)).catch((err) => setError(err instanceof Error ? err.message : 'No se pudieron cargar los proveedores.'))
  }, [token])
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); if (!token) return
    try { if (editingId) await api.updateProvider(token, editingId, form); else await api.createProvider(token, form); setForm(emptyProvider); setEditingId(null); await load() }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudo guardar el proveedor.') }
  }
  const remove = async (id: number) => { if (!token || !window.confirm('¿Eliminar este proveedor?')) return; try { await api.deleteProvider(token, id); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo eliminar.') } }

  return <section className="page-shell"><header className="page-header"><div><p className="eyebrow">Abastecimiento</p><h1>Proveedores</h1></div></header>
    <form className="panel-card form-grid" onSubmit={submit}><h2>{editingId ? 'Editar proveedor' : 'Nuevo proveedor'}</h2><input required placeholder="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} /><input placeholder="Teléfono" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} /><input type="email" placeholder="Correo" value={form.correo} onChange={(e) => setForm({ ...form, correo: e.target.value })} /><input placeholder="Dirección" value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} /><button type="submit">Guardar proveedor</button>{editingId && <button type="button" className="secondary-button" onClick={() => { setEditingId(null); setForm(emptyProvider) }}>Cancelar</button>}</form>
    {error && <p className="error-message">{error}</p>}
    <section className="panel-card table-panel"><table><thead><tr><th>Nombre</th><th>Teléfono</th><th>Correo</th><th>Dirección</th><th>Acciones</th></tr></thead><tbody>{providers.map((provider) => <tr key={provider.id_proveedor}><td>{provider.nombre}</td><td>{provider.telefono || '-'}</td><td>{provider.correo || '-'}</td><td>{provider.direccion || '-'}</td><td><button type="button" className="icon-button" aria-label="Editar proveedor" onClick={() => { setEditingId(provider.id_proveedor); setForm({ nombre: provider.nombre, telefono: provider.telefono ?? '', correo: provider.correo ?? '', direccion: provider.direccion ?? '' }) }}><Pencil size={17} /></button><button type="button" className="icon-button remove-item" aria-label="Eliminar proveedor" onClick={() => void remove(provider.id_proveedor)}><Trash2 size={17} /></button></td></tr>)}</tbody></table></section>
  </section>
}
