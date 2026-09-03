const inventory = [
  { id: 1, producto: 'Agua 600ml', cantidad: 18, ubicacion: 'Estante A1', minimo: 5 },
  { id: 2, producto: 'Galletas Dulces', cantidad: 12, ubicacion: 'Estante B2', minimo: 8 },
]

export default function InventoryPage() {
  return (
    <section className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Inventario</p>
          <h1>Control de stock</h1>
        </div>
      </header>

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
              <tr key={item.id}>
                <td>{item.producto}</td>
                <td>{item.cantidad}</td>
                <td>{item.ubicacion}</td>
                <td>{item.minimo}</td>
                <td>
                  {item.cantidad <= item.minimo ? 'Bajo' : 'Normal'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  )
}
