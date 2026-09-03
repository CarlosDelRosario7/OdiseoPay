const customers = [
  { id: 1, nombre: 'Argenys', apellido: 'No Bulto', telefono: '8292345678', correo: 'argenys@example.com' },
  { id: 2, nombre: 'Marta', apellido: 'Pérez', telefono: '8091234567', correo: 'marta@example.com' },
]

export default function CustomersPage() {
  return (
    <section className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">CRM</p>
          <h1>Clientes</h1>
        </div>
        <button type="button">Nuevo cliente</button>
      </header>

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
              <tr key={customer.id}>
                <td>{customer.nombre} {customer.apellido}</td>
                <td>{customer.telefono}</td>
                <td>{customer.correo}</td>
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
