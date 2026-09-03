const users = [
  { id: 1, nombre: 'Administrador', usuario: 'admin', rol: 'Admin' },
  { id: 2, nombre: 'Joel La Para', usuario: 'vendedor1', rol: 'Vendedor' },
]

export default function UsersPage() {
  return (
    <section className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Usuarios</p>
          <h1>Administración</h1>
        </div>
        <button type="button">Nuevo usuario</button>
      </header>

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
              <tr key={user.id}>
                <td>{user.nombre}</td>
                <td>{user.usuario}</td>
                <td>{user.rol}</td>
                <td>
                  <button type="button" className="mini-button">Editar</button>
                  <button type="button" className="mini-button danger">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  )
}
