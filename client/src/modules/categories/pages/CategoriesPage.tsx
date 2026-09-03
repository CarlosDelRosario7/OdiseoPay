import { useEffect, useState } from 'react'
import { Pencil, Trash2 } from 'lucide-react'
import { api, type CategorySummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'

export default function CategoriesPage() {
  const token = useAuthStore((state) => state.token)
  const [categories, setCategories] = useState<CategorySummary[]>([])
  const [form, setForm] = useState({ nombre: '', descripcion: '' })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const load = async () => { if (!token) return; try { setCategories((await api.getCategories(token)).items); setError('') } catch (err) { setError(err instanceof Error ? err.message : 'No se pudieron cargar las categorías.') } }
  useEffect(() => { if (!token) return; void api.getCategories(token).then((response) => setCategories(response.items)).catch((err) => setError(err instanceof Error ? err.message : 'No se pudieron cargar las categorías.')) }, [token])
  const submit = async (event: React.FormEvent) => { event.preventDefault(); if (!token) return; try { if (editingId) await api.updateCategory(token, editingId, form); else await api.createCategory(token, form); setForm({ nombre: '', descripcion: '' }); setEditingId(null); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo guardar la categoría.') } }
  const remove = async (id: number) => { if (!token || !window.confirm('¿Eliminar esta categoría?')) return; try { await api.deleteCategory(token, id); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo eliminar.') } }
  return <section className="page-shell"><header className="page-header"><div><p className="eyebrow">Catálogo</p><h1>Categorías</h1></div></header><form className="panel-card form-grid" onSubmit={submit}><h2>{editingId ? 'Editar categoría' : 'Nueva categoría'}</h2><input required placeholder="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} /><input placeholder="Descripción" value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} /><button type="submit">Guardar categoría</button>{editingId && <button type="button" className="secondary-button" onClick={() => { setEditingId(null); setForm({ nombre: '', descripcion: '' }) }}>Cancelar</button>}</form>{error && <p className="error-message">{error}</p>}<section className="panel-card table-panel"><table><thead><tr><th>Nombre</th><th>Descripción</th><th>Acciones</th></tr></thead><tbody>{categories.map((category) => <tr key={category.id_categoria}><td>{category.nombre}</td><td>{category.descripcion || '-'}</td><td><button type="button" className="icon-button" aria-label="Editar categoría" onClick={() => { setEditingId(category.id_categoria); setForm({ nombre: category.nombre, descripcion: category.descripcion ?? '' }) }}><Pencil size={17} /></button><button type="button" className="icon-button remove-item" aria-label="Eliminar categoría" onClick={() => void remove(category.id_categoria)}><Trash2 size={17} /></button></td></tr>)}</tbody></table></section></section>
}