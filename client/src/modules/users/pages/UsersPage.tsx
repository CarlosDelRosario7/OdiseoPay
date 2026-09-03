import { useEffect, useState } from 'react'
import { api, type UserSummary } from '../../../shared/lib/api'
import { useAuthStore } from '../../../shared/store/authStore'

export default function UsersPage() {
  const token = useAuthStore((state) => state.token)
  const [users, setUsers] = useState<UserSummary[]>([])
  const [form, setForm] = useState({ nombre: '', usuario: '', contrasena: '', rol: 'Vendedor' as 'Admin' | 'Vendedor' })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const load = async () => { if (!token) return; try { setUsers((await api.getUsers(token)).items) } catch (err) { setError(err instanceof Error ? err.message : 'No se pudieron cargar los usuarios.') } }
  useEffect(() => {
    if (!token) return
    void api.getUsers(token).then((response) => setUsers(response.items)).catch((err) => setError(err instanceof Error ? err.message : 'No se pudieron cargar los usuarios.'))
  }, [token])
  const submit = async (event: React.FormEvent) => { event.preventDefault(); if (!token) return; try { if (editingId) await api.updateUser(token, editingId, { ...form, contrasena: form.contrasena || undefined }); else await api.createUser(token, form); setForm({ nombre: '', usuario: '', contrasena: '', rol: 'Vendedor' }); setEditingId(null); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo guardar el usuario.') } }
  const remove = async (id: number) => { if (!token || !window.confirm('¿Eliminar este usuario?')) return; try { await api.deleteUser(token, id); await load() } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo eliminar.') } }
  return (
    <section className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Usuarios</p>
          <h1>Administración</h1>
        </div>
      </header>
      <form className="panel-card form-grid" onSubmit={submit}><h2>{editingId ? 'Editar usuario' : 'Nuevo usuario'}</h2><input required placeholder="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} /><input required placeholder="Usuario" value={form.usuario} onChange={(e) => setForm({ ...form, usuario: e.target.value })} />{!editingId && <input required type="password" placeholder="Contraseña" value={form.contrasena} onChange={(e) => setForm({ ...form, contrasena: e.target.value })} />}<select value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value as 'Admin' | 'Vendedor' })}><option>Vendedor</option><option>Admin</option></select><button type="submit">Guardar usuario</button>{editingId && <button type="button" className="secondary-button" onClick={() => { setEditingId(null); setForm({ nombre: '', usuario: '', contrasena: '', rol: 'Vendedor' }) }}>Cancelar</button>}</form>
      {error && <p className="error-message">{error}</p>}

      <section className="panel-card table-panel">
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Usuario</th>
              <th>Rol</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id_usuario}>
                <td>{user.nombre}</td>
                <td>{user.usuario}</td>
                <td>{user.rol}</td>
                <td>
                  <button type="button" className="mini-button" onClick={() => { setEditingId(user.id_usuario); setForm({ nombre: user.nombre, usuario: user.usuario, contrasena: '', rol: user.rol as 'Admin' | 'Vendedor' }) }}>Editar</button><button type="button" className="mini-button danger" onClick={() => void remove(user.id_usuario)}>Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  )
}
