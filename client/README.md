# OdiseoPay Frontend

Aplicación web de punto de venta y gestión comercial para OdiseoPay. Permite administrar productos, categorías, clientes, proveedores, inventario y usuarios, además de registrar compras y ventas.

El frontend está construido con React y TypeScript, y se conecta al backend Flask mediante la API REST del proyecto.

## Stack

- React 19 + TypeScript
- Vite 8
- React Router para navegación
- TanStack React Query
- Zustand para sesión y tema claro/oscuro
- Auth0 React SDK para login social
- Fetch centralizado en `src/shared/lib/api.ts`
- Lucide React para iconos
- Vite PWA para manifest y service worker

## Funcionalidades

### Autenticación

- Inicio de sesión local mediante `POST /api/auth/login`.
- Inicio de sesión con Google y Facebook a través de Auth0 (`POST /api/auth/auth0/login`).
- Vinculación y desvinculación de una cuenta social desde el menú lateral, sin SQL manual.
- Una sola cuenta social por usuario. Para cambiar de Google a Facebook primero se desvincula la actual.
- Persistencia local del token y usuario autenticado.
- Protección de rutas privadas.
- Permisos para `Admin` y `Vendedor`.
- Mostrar u ocultar contraseña.
- Cambio de tema claro/oscuro desde login y aplicación.
- Diseño de login en dos columnas: portada a la izquierda y formulario a la derecha. En móvil la portada pasa arriba y el formulario se solapa ligeramente.

### Módulos

- **Dashboard:** métricas de ventas, productos y clientes.
- **Ventas:** búsqueda con sugerencias, carrito editable, eliminación de productos, cálculo de subtotal, ITBIS, total y cambio.
- **Historial:** ventas con filtros por fecha y recibo imprimible.
- **Productos:** listado, creación, edición, eliminación y stock asociado.
- **Categorías:** listado, creación, edición y eliminación.
- **Clientes:** listado, creación, edición y eliminación.
- **Proveedores:** listado, creación, edición y eliminación.
- **Inventario:** edición de cantidad, stock mínimo y ubicación.
- **Compras:** proveedor, productos, cantidades y precios; el backend actualiza el stock.
- **Usuarios:** listado, creación, edición y eliminación para administradores.

## Rutas

| Ruta | Acceso |
| --- | --- |
| `/login` | Público |
| `/` | Usuario autenticado |
| `/ventas` | `Admin`, `Vendedor` |
| `/ventas/historial` | `Admin`, `Vendedor` |
| `/productos` | `Admin`, `Vendedor` |
| `/categorias` | `Admin`, `Vendedor` |
| `/clientes` | Según permisos del backend |
| `/inventario` | `Admin`, `Vendedor` |
| `/proveedores` | Administrador |
| `/compras` | Administrador |
| `/usuarios` | Administrador |

El backend aplica siempre la autorización definitiva. El frontend oculta opciones y protege rutas para mejorar la experiencia.

## Estructura

```text
src/
├── app/                 # Rutas y providers globales
├── modules/             # Funcionalidades por dominio
│   ├── auth/
│   ├── categories/
│   ├── customers/
│   ├── dashboard/
│   ├── inventory/
│   ├── products/
│   ├── providers/
│   ├── purchases/
│   ├── sales/
│   └── users/
└── shared/
    ├── components/      # Shell, sidebar, topbar y rutas protegidas
    ├── lib/             # Cliente API, configuración Auth0 y tipos
    ├── store/           # Sesión y tema
    └── utils/           # Validaciones y formatos
```

## Configuración

Crear `client/.env` a partir de `client/.env.example`:

```env
VITE_API_BASE_URL=http://127.0.0.1:5000
VITE_APP_NAME=OdiseoPay
VITE_APP_ENV=development
VITE_ENABLE_PWA=true
VITE_DEFAULT_THEME=dark

VITE_AUTH0_DOMAIN=dev-mjgxqjikayj2605h.us.auth0.com
VITE_AUTH0_CLIENT_ID=KTIURFsJfii0Q3EcCfHSa8FL2RN49QWz
VITE_AUTH0_AUDIENCE=https://api.odiseopay.com
```

El backend debe estar ejecutándose y permitir el origen de Vite, normalmente `http://localhost:5173`.

`VITE_AUTH0_CLIENT_ID` debe ser el Client ID de una aplicación **Single Page Application**, no el de una Regular Web App ni el de Machine-to-Machine. El Client ID de una SPA es público; no agregues Client Secret al frontend.

`src/shared/lib/auth0.ts` incluye los valores públicos del tenant como respaldo para que la aplicación no navegue a `https://undefined`. Si `client/.env` define las variables, esas tienen prioridad.

### Configuración de Auth0

En el dashboard de Auth0, la SPA debe tener:

- **Allowed Callback URLs:** `http://localhost:5173/login`
- **Allowed Logout URLs:** `http://localhost:5173/login`
- **Allowed Web Origins:** `http://localhost:5173`
- La API con identifier `https://api.odiseopay.com` autorizada para la SPA.
- Las conexiones **Google** y **Facebook** habilitadas para esa SPA.

El identifier de la API es lógico: no necesita ser un dominio real ni resolver en DNS. El backend local sigue en `http://127.0.0.1:5000`.

### Vincular Google o Facebook

1. Inicia sesión con usuario y contraseña local.
2. Abre el menú lateral y pulsa **Vincular cuenta social**.
3. Auth0 abre la pantalla de inicio de sesión en la misma pestaña.
4. Elige Google o Facebook y completa el flujo.
5. Al volver a OdiseoPay, el backend guarda el `sub` en `usuarios.auth0_sub` y verás el resultado en el menú lateral.

Después de vincular, los botones **Google** y **Facebook** del login permiten entrar directamente con el rol local del usuario.

Cada usuario puede tener una sola cuenta social. Si ya vinculó Google y quiere usar Facebook, primero debe pulsar **Desvincular**. El backend también rechaza con `409` un intento de vincular una segunda cuenta o un `sub` que ya pertenece a otro usuario.

### Problemas frecuentes de Auth0

| Síntoma | Solución |
| --- | --- |
| `Servidor no encontrado: undefined` | Faltan las variables `VITE_AUTH0_*`; revisa `client/.env` y reinicia Vite |
| `Callback URL mismatch` | Agrega `http://localhost:5173/login` en Allowed Callback URLs |
| `Client ... is not authorized to access resource server` | Abre APIs → OdiseoPay API → Applications y autoriza la SPA |
| La cuenta social no inicia sesión | Primero vincula la cuenta desde el menú lateral con tu usuario local |
| La vinculación no vuelve a la app | Revisa que `http://localhost:5173/login` esté en Allowed Callback URLs y que Auth0 tenga la API autorizada |
| Error al vincular una segunda cuenta | Desvincula la cuenta actual antes de vincular la otra |

## Instalación y ejecución

Desde la carpeta `client`:

```bash
npm install
npm run dev
```

La aplicación estará disponible normalmente en `http://localhost:5173`.

## Validación

```bash
npm run build
npm run lint
```

El build genera también `manifest.webmanifest`, `sw.js` y `registerSW.js` para la PWA.

## Diseño responsive

- Login en dos columnas en escritorio y apilado en móvil, con la portada arriba y la tarjeta del formulario solapada.
- La portada se sirve como `public/portada.webp`; `Portada.jpg` se conserva como fuente original.
- Menú lateral desplegable desde la izquierda en pantallas pequeñas.
- Scroll independiente para el menú y el contenido principal.
- Scroll horizontal en tablas pequeñas.
- Transiciones de navegación y loader con el icono de OdiseoPay.
- Soporte para `prefers-reduced-motion`.

## Consideraciones del backend

- Las ventas y compras se envían como operaciones compuestas para actualizar inventario y registrar movimientos.
- El historial devuelve datos básicos; el recibo imprimible usa únicamente la información disponible en la API.
- La búsqueda de productos se realiza localmente sobre los productos cargados.
- El frontend no sustituye las validaciones de autenticación, permisos, stock ni integridad del backend.
