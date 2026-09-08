# OdiseoPay API

Backend REST para OdiseoPay construido con Flask, Flask-SQLAlchemy, MariaDB/MySQL, JWT y Flask-Migrate.

## Inicio rápido

Desde la raíz del proyecto (en el caso de ejecutar en linux o WSL), ejecuta:

```bash
./server/iniciar_servidor.sh
```

El script crea `.venv` si no existe, instala las dependencias y arranca la API.

La API queda disponible en `http://127.0.0.1:5000`. También puede iniciarse con `flask --app src.main run --debug`.

El archivo `.env` debe contener las credenciales de la base de datos. Usa `.env.example` como referencia. No publiques `.env` ni sus secretos.

## Base de datos y migraciones

La base inicial se crea ejecutando `migrations/odiseopay.sql`. Los cambios posteriores se gestionan con Flask-Migrate:

```bash
source venv/bin/activate
flask --app src.main db migrate -m "descripcion del cambio"
flask --app src.main db upgrade
```

La migración inicial crea `categorias`, `proveedores`, `clientes`, `usuarios`, `productos`, `inventario`, `compras`, `detalle_compra`, `ventas`, `detalle_venta` y `movimientos_inventario`.

## Convenciones generales

- Todas las rutas de negocio empiezan por `/api`.
- Los cuerpos de creación y actualización son JSON.
- Los identificadores son enteros.
- Las listas devuelven `page`, `per_page`, `total`, `pages` e `items`.
- `per_page` está limitado a 100 y el valor predeterminado es 20.
- Las contraseñas se envían con el campo `contrasena`, pero nunca se devuelven.
- La columna de MariaDB se llama `contraseña`; el frontend debe usar `contrasena` en JSON.

## Autenticación

### Crear el primer administrador

Solo si `usuarios` está vacía:

```http
POST /api/auth/registro
Content-Type: application/json

{
	"nombre": "Administrador",
	"usuario": "admin",
	"contrasena": "admin1234",
	"rol": "Admin"
}
```

El primer usuario debe ser `Admin`. Después, este endpoint queda bloqueado y los usuarios deben crearse mediante `POST /api/usuarios` con un token de `Admin`.

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
	"usuario": "admin",
	"contrasena": "admin1234"
}
```

Respuesta `200`:

```json
{
	"access_token": "<jwt>",
	"usuario": "admin",
	"rol": "Admin"
}
```

Enviar el token en todas las rutas protegidas:

```http
Authorization: Bearer <jwt>
```

## Permisos por rol

| Recurso | Admin | Vendedor |
| --- | --- | --- |
| Categorías | CRUD | listar y consultar |
| Proveedores | CRUD | sin acceso |
| Clientes | CRUD | sin acceso |
| Usuarios | CRUD | sin acceso |
| Productos | CRUD | listar y consultar |
| Inventario | CRUD | listar y consultar |
| Compras | CRUD | sin acceso |
| Detalles de compra | CRUD | sin acceso |
| Ventas | CRUD | listar, consultar y crear |
| Detalles de venta | CRUD | listar, consultar y crear |
| Movimientos de inventario | CRUD | listar y consultar |

Los endpoints de lectura también requieren JWT. Sin token se responde `401`; sin permisos, `403`.

## Endpoints CRUD

Para cada recurso, `<id>` es el identificador entero:

| Método | Endpoint | Uso |
| --- | --- | --- |
| GET | `/api/<recurso>` | Lista paginada |
| GET | `/api/<recurso>/<id>` | Consulta individual |
| POST | `/api/<recurso>` | Crear |
| PATCH | `/api/<recurso>/<id>` | Actualización parcial |
| DELETE | `/api/<recurso>/<id>` | Borrado físico |

Recursos disponibles:

```text
/api/categorias
/api/proveedores
/api/clientes
/api/usuarios
/api/productos
/api/inventario
/api/compras
/api/detalle-compras
/api/ventas
/api/detalle-ventas
/api/movimientos-inventario
```

Ejemplo:

```http
GET /api/productos?page=1&per_page=20
Authorization: Bearer <jwt>
```

Respuesta de lista:

```json
{
	"items": [],
	"page": 1,
	"per_page": 20,
	"total": 0,
	"pages": 0
}
```

## Payloads

### Categoría

```json
{
	"nombre": "Bebidas",
	"descripcion": "Bebidas y refrescos"
}
```

### Proveedor

```json
{
	"nombre": "Proveedor Demo",
	"telefono": "5551234567",
	"correo": "proveedor@example.com",
	"direccion": "Calle Principal 123"
}
```

### Cliente

```json
{
	"nombre": "Cliente",
	"apellido": "Demo",
	"correo": "cliente@example.com",
	"telefono": "5552223333",
	"direccion": "Avenida Central 45"
}
```

### Usuario

```json
{
	"nombre": "Vendedor Demo",
	"usuario": "vendedor1",
	"contrasena": "1234",
	"rol": "Vendedor"
}
```

Los únicos roles válidos son `Admin` y `Vendedor`.

### Producto

```json
{
	"nombre": "Agua 600ml",
	"descripcion": "Agua embotellada",
	"precio_compra": "5.00",
	"precio_venta": "8.50",
	"id_categoria": 1,
	"id_proveedor": 1
}
```

### Inventario

```json
{
	"id_producto": 1,
	"cantidad": 10,
	"stock_minimo": 5,
	"ubicacion": "Estante A1"
}
```

Cada producto puede tener un único registro de inventario.

### Movimiento de inventario

```json
{
	"id_producto": 1,
	"tipo": "AJUSTE",
	"cantidad": 1,
	"motivo": "Conteo fisico",
	"id_usuario": 1
}
```

`tipo` solo puede ser `ENTRADA`, `SALIDA` o `AJUSTE`.

## Compras y ventas

Las operaciones completas deben usar los endpoints de cabecera. Los servicios crean los detalles y actualizan el inventario en una misma transacción.

### Registrar compra

Solo `Admin`:

```http
POST /api/compras
Authorization: Bearer <jwt>
Content-Type: application/json

{
	"id_proveedor": 1,
	"detalles": [
		{
			"id_producto": 1,
			"cantidad": 20,
			"precio": "5.00"
		}
	]
}
```

La compra incrementa el stock y registra un movimiento `ENTRADA` por cada detalle.

### Registrar venta

Disponible para `Admin` y `Vendedor`:

```http
POST /api/ventas
Authorization: Bearer <jwt>
Content-Type: application/json

{
	"id_cliente": 1,
	"detalles": [
		{
			"id_producto": 1,
			"cantidad": 2,
			"precio": "9.00"
		}
	]
}
```

La venta decrementa el stock y registra un movimiento `SALIDA`. Si no hay stock suficiente, responde `422` y no completa la operación.

Los detalles también tienen CRUD directo mediante `/api/detalle-compras` y `/api/detalle-ventas`, pero no deben usarse para reemplazar las operaciones completas si se necesita actualizar inventario automáticamente.

## Respuestas y errores

| Código | Significado |
| --- | --- |
| 200 | Consulta o actualización exitosa |
| 201 | Recurso creado |
| 204 | Recurso eliminado |
| 401 | Falta autenticación o credenciales inválidas |
| 403 | Rol sin permiso |
| 404 | Recurso no encontrado |
| 409 | Conflicto con registros relacionados |
| 422 | JSON o datos inválidos |
| 500 | Error inesperado |

Respuesta de error:

```json
{
	"error": "Descripción del problema"
}
```

Un `PATCH` es parcial: envía únicamente los campos que quieras cambiar. No envíes campos obligatorios con valor `null`, por ejemplo `"id_producto": null`.

## Borrados físicos

Los `DELETE` son permanentes. El frontend debe pedir confirmación antes de ejecutarlos.

Un producto, proveedor o categoría no puede borrarse si tiene registros relacionados. La API responde `409`; el frontend debe mostrar el mensaje y no repetir automáticamente la solicitud. No se recomienda borrar el historial de ventas o movimientos solo para eliminar un producto.

## REST Client

El archivo `test.http` contiene ejemplos ejecutables. Ejecuta primero health, registro inicial si corresponde, login y después las solicitudes en orden. Los IDs deben coincidir con los registros reales de la base de datos.

## Limitaciones actuales

La versión actual no incluye filtros por query para productos, endpoint de bajo stock, documentación OpenAPI ni refresco de tokens. El frontend debe usar los endpoints descritos arriba hasta que esas funciones se implementen.
