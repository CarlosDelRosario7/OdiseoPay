# OdiseoPay API

Backend REST para OdiseoPay construido con Flask, Flask-SQLAlchemy, MariaDB/MySQL, JWT y Flask-Migrate.

## Inicio rápido

Desde la raíz del proyecto (en el caso de ejecutar en linux o WSL), ejecuta:

```bash
./server/iniciar_servidor.sh
```

El script crea `.venv` si no existe, instala las dependencias, aplica las migraciones pendientes con Alembic y arranca la API.

La API queda disponible en `http://127.0.0.1:5000`. También puede iniciarse con `flask --app src.main run --debug`.

El archivo `.env` debe contener las credenciales de la base de datos. Usa `.env.example` como referencia. No publiques `.env` ni sus secretos.

## Base de datos y migraciones

La base inicial se crea ejecutando `migrations/odiseopay.sql`. Los cambios posteriores se gestionan con Flask-Migrate/Alembic. El repositorio guarda el entorno de migraciones en `server/migrations/alembic/` y la configuración en `server/alembic.ini`.

Desde `server/`:

```bash
../.venv/bin/python -m flask --app src.main db upgrade
../.venv/bin/python -m flask --app src.main db current
```

Para crear una migración después de cambiar un modelo:

```bash
../.venv/bin/python -m flask --app src.main db migrate -m "descripcion del cambio"
../.venv/bin/python -m flask --app src.main db upgrade
```

También puedes usar Alembic directamente:

```bash
../.venv/bin/python -m alembic -c alembic.ini upgrade head
../.venv/bin/python -m alembic -c alembic.ini current
```

`iniciar_servidor.sh` aplica automáticamente `alembic upgrade head` antes de arrancar. Para omitir ese paso:

```bash
ODISEOPAY_SKIP_MIGRATIONS=1 ./server/iniciar_servidor.sh
```

La migración inicial crea `categorias`, `proveedores`, `clientes`, `usuarios`, `productos`, `inventario`, `compras`, `detalle_compra`, `ventas`, `detalle_venta` y `movimientos_inventario`. La migración `c4f89f958055` agrega `usuarios.auth0_sub` y su restricción única.

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
	"id_usuario": 3,
	"nombre": "Administrador",
	"usuario": "admin",
	"rol": "Admin",
	"auth0_sub": null,
	"auth0_provider": null
}
```

`auth0_sub` indica la cuenta social vinculada (`google-oauth2|...` o `facebook|...`). Es `null` cuando el usuario solo tiene contraseña local.

Enviar el token en todas las rutas protegidas:

```http
Authorization: Bearer <jwt>
```

### Login social con Auth0

El frontend usa una aplicación de Auth0 de tipo **Single Page Application**. El flujo es:

1. El usuario pulsa **Google** o **Facebook** en `/login`.
2. Auth0 redirige de vuelta a `http://localhost:5173/login`.
3. El frontend obtiene el access token y llama a `POST /api/auth/auth0/login`.
4. El backend valida el token contra el JWKS del tenant, busca `usuarios.auth0_sub` y devuelve el JWT local con el rol de OdiseoPay.

Si la cuenta social todavía no está vinculada, el backend responde `403` con un mensaje que indica iniciar sesión localmente y vincularla desde el menú lateral.

Variables necesarias en `server/.env`:

```env
AUTH0_DOMAIN=dev-mjgxqjikayj2605h.us.auth0.com
AUTH0_AUDIENCE=https://api.odiseopay.com
```

`AUTH0_AUDIENCE` es el **identifier** de la API creada en Auth0. No tiene que ser un dominio real ni resolver en DNS; es un identificador lógico. La API del proyecto sigue corriendo en `http://127.0.0.1:5000`.

En el dashboard de Auth0, la SPA debe tener configurado:

- Allowed Callback URLs: `http://localhost:5173/login`
- Allowed Logout URLs: `http://localhost:5173/login`
- Allowed Web Origins: `http://localhost:5173`
- La API `https://api.odiseopay.com` autorizada para la SPA.
- Las conexiones sociales Google y Facebook habilitadas para esa SPA.

#### Vincular una cuenta social

La vinculación se hace dentro de la aplicación, sin SQL manual:

```http
POST /api/auth/auth0/vincular
Authorization: Bearer <jwt-local>
Content-Type: application/json

{
	"auth0_token": "<access_token de Auth0>"
}
```

Respuesta `200`:

```json
{
	"auth0_sub": "google-oauth2|1234567890",
	"auth0_provider": "Google",
	"message": "Cuenta social vinculada correctamente."
}
```

Reglas:

- Cada usuario local puede tener **una** cuenta social vinculada.
- Si el usuario ya tiene Google y envía un token de Facebook, el backend responde `409` y pide desvincular primero.
- Si el `sub` ya pertenece a otro usuario, responde `409`.
- Vincular la misma cuenta dos veces es idempotente (`200`).

#### Desvincular una cuenta social

```http
DELETE /api/auth/auth0/vincular
Authorization: Bearer <jwt-local>
```

Responde `204` si se eliminó el vínculo, o `200` con un mensaje si el usuario no tenía cuenta social.

### Solución de problemas de Auth0

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `Firefox no puede conectarse al servidor undefined` | Faltan `VITE_AUTH0_DOMAIN` o `VITE_AUTH0_CLIENT_ID` | Crea `client/.env` desde `client/.env.example` y reinicia Vite |
| `La cuenta de Auth0 no está vinculada` | El `sub` no existe en `usuarios.auth0_sub` | Inicia sesión local y usa **Vincular cuenta social** |
| `Auth0 no está configurado en el servidor` | Faltan variables en `server/.env` | Agrega `AUTH0_DOMAIN` y `AUTH0_AUDIENCE` y reinicia Flask |
| `Unknown column 'usuarios.auth0_sub'` | Falta aplicar la migración | Ejecuta `flask --app src.main db upgrade` |
| `No se pudo validar la cuenta de Auth0` | Token vencido, audience incorrecta o problema de red con el JWKS | Revisa la configuración de la API y vuelve a iniciar sesión |
| `Client ... is not authorized to access resource server` | La SPA no está autorizada para la API en Auth0 | En APIs → OdiseoPay API → Applications, autoriza la SPA |
| `Callback URL mismatch` | La URL de callback no está autorizada | Agrega `http://localhost:5173/login` en la SPA |

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
