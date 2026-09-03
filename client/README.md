# OdiseoPay Frontend

Aplicación web de punto de venta y gestión comercial para OdiseoPay. Permite administrar productos, categorías, clientes, proveedores, inventario y usuarios, además de registrar compras y ventas.

El frontend está construido con React y TypeScript, y se conecta al backend Flask mediante la API REST del proyecto.

## Stack

- React 19 + TypeScript
- Vite 8
- React Router para navegación
- TanStack React Query
- Zustand para sesión y tema claro/oscuro
- Fetch centralizado en `src/shared/lib/api.ts`
- Lucide React para iconos
- Vite PWA para manifest y service worker

## Funcionalidades

### Autenticación

- Inicio de sesión mediante `POST /api/auth/login`.
- Persistencia local del token y usuario autenticado.
- Protección de rutas privadas.
- Permisos para `Admin` y `Vendedor`.
- Mostrar u ocultar contraseña.
- Cambio de tema claro/oscuro desde login y aplicación.

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
    ├── lib/             # Cliente API y tipos compartidos
    ├── store/            # Sesión y tema
    └── utils/            # Validaciones y formatos
```

## Configuración

Crear `client/.env` a partir de `client/.env.example`:

```env
VITE_API_BASE_URL=http://127.0.0.1:5000
```

El backend debe estar ejecutándose y permitir el origen de Vite, normalmente `http://localhost:5173`.

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
