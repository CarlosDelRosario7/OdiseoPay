const products = [
  { id: 1, nombre: 'Agua 600ml', categoria: 'Bebidas', precio: 8.5, stock: 18 },
  { id: 2, nombre: 'Galletas Dulces', categoria: 'Snacks', precio: 35, stock: 12 },
  { id: 3, nombre: 'Arroz 5kg', categoria: 'Abarrotes', precio: 240, stock: 9 },
]

export default function ProductsPage() {
  return (
    <section className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Catálogo</p>
          <h1>Productos</h1>
        </div>
        <button type="button">Nuevo producto</button>
      </header>

      <div className="card-list">
        <div className="panel-card">
          <strong>Productos activos</strong>
          <span>3</span>
        </div>
        <div className="panel-card">
          <strong>Stock bajo</strong>
          <span>1</span>
        </div>
        <div className="panel-card">
          <strong>Precio promedio</strong>
          <span>RD$ 94.50</span>
        </div>
      </div>

      <section className="panel-card table-panel">
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Categoría</th>
              <th>Precio</th>
              <th>Stock</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td>{product.nombre}</td>
                <td>{product.categoria}</td>
                <td>RD$ {product.precio.toFixed(2)}</td>
                <td>{product.stock}</td>
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
