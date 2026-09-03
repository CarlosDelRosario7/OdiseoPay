# Plan de frontend para OdiseoPay

## 1. Objetivo

Diseñar el frontend en React + TypeScript, siguiendo el backend real de este proyecto y evitando suposiciones que puedan romper la integración. El sistema será mobile-first, con diseño minimalista, oscuro/claro, responsivo, modular y preparado para escalar, manteniendo la lógica de negocio alineada con los endpoints y roles actuales del backend.

Este plan no incluye implementación aún; es la base para revisión y aprobación antes de comenzar con el código.

---

## 2. Revisión del backend y compatibilidad real

Se revisó el backend y se validó que la estructura actual soporta este flujo de negocio:

- Autenticación:
  - `POST /api/auth/login`
  - `POST /api/auth/registro`
  - El primer usuario registrado debe ser `Admin`.
  - Los roles válidos actuales son `Admin` y `Vendedor`.
  - El token JWT incluye el rol del usuario.

- Usuarios:
  - `GET /api/usuarios`
  - `GET /api/usuarios/:id`
  - `PATCH /api/usuarios/:id`
  - `POST /api/usuarios` sólo para Admin.
  - El usuario tiene: `nombre`, `usuario`, `contrasena`, `rol`.

- Productos:
  - `GET /api/productos`
  - `GET /api/productos/:id`
  - `POST /api/productos`
  - `PATCH /api/productos/:id`
  - `DELETE /api/productos/:id`
  - Se usan `nombre`, `descripcion`, `precio_compra`, `precio_venta`, `id_categoria`, `id_proveedor`.

- Clientes:
  - `GET /api/clientes`
  - `GET /api/clientes/:id`
  - `POST /api/clientes`
  - `PATCH /api/clientes/:id`
  - `DELETE /api/clientes/:id`
  - Se manejan `nombre`, `apellido`, `correo`, `telefono`, `direccion`.

- Categorías y proveedores:
  - `GET /api/categorias`, `POST /api/categorias`, etc.
  - `GET /api/proveedores`, `POST /api/proveedores`, etc.

- Inventario:
  - `POST /api/inventario`
  - `GET /api/inventario`
  - `PATCH /api/inventario/:id`
  - Se controla `id_producto`, `cantidad`, `stock_minimo`, `ubicacion`.

- Compras:
  - `POST /api/compras`
  - Se registra una compra con detalles, aumenta stock y crea movimientos de inventario tipo `ENTRADA`.

- Ventas:
  - `POST /api/ventas`
  - Requiere `id_cliente` y al menos un detalle en `detalles`.
  - Cada detalle requiere `id_producto`, `cantidad` y `precio`.
  - Valida stock suficiente antes de realizar la venta.
  - Descuenta inventario automáticamente y genera movimiento tipo `SALIDA`.

- Reglas de autorización:
  - `Admin` puede gestionar más módulos y crear usuarios.
  - `Vendedor` tiene permisos de venta y lectura general, según la configuración del backend.

### Validación importante

El plan frontend deberá respetar estas condiciones para no crear inconsistencias:

1. El rol de primer usuario es `Admin`.
2. La venta no se puede registrar sin cliente y sin productos.
3. El backend valida stock disponible antes de vender.
4. El sistema no tiene un endpoint de factura/recibo nativo; si se genera un recibo digital, debe construirse desde la venta confirmada y los datos del backend.
5. Las operaciones de borrado pueden devolver 409 cuando hay registros relacionados.

---

## 3. Requisitos funcionales compatibles con el backend

### RF-01: Inicio de sesión

Debe implementarse con `POST /api/auth/login` usando `usuario` y `contrasena`. El frontend debe guardar el token y manejar el rol del usuario para permisos.

### RF-02: Registrar una venta con múltiples productos

Debe ir con `POST /api/ventas`, enviando:

```json
{
  "id_cliente": 1,
  "detalles": [
    { "id_producto": 1, "cantidad": 2, "precio": "8.50" }
  ]
}
```

El frontend debe construir el arreglo de productos con cantidad y precio, calcular el subtotal, ITBIS y total de forma local, y confirmar la venta con el backend.

### RF-03: Cálculo de subtotal, ITBIS y total

El backend no devuelve estos valores por sí solo; el frontend debe calcularlo de acuerdo a la lógica de negocio del negocio. Se recomienda usar una regla consistente (
ITBIS 18% o la tasa vigente del negocio) y mostrarla claramente en la pantalla de venta.

### RF-04: Cambio a devolver

Se calcula en frontend como:

```
cambio = monto_recibido - total_venta
```

### RF-05: Recibo de venta

Se puede generar un recibo digital (PDF, impresión o vista previa) a partir de la respuesta de la venta y los datos agregados en frontend. No debe asumirse un endpoint exclusivo de recibos.

### RF-06: Descuento automático del inventario

El backend ya hace este descuento al crear la venta. El frontend sólo debe validar stock previo y mostrar mensajes claros si el producto no tiene suficiente cantidad.

### RF-07: Crear, editar y eliminar productos

Compatibles con `POST /api/productos`, `PATCH /api/productos/:id` y `DELETE /api/productos/:id`.

### RF-08: Buscar productos por nombre

El backend no expone un endpoint de búsqueda por código de barras. La búsqueda debe seguir lo que ofrece la API actual: filtros por nombre y relaciones (`id_categoria`, `id_proveedor`) en `GET /api/productos`. El frontend implementará la búsqueda local y/o por query params según sea necesario, sin inventar soporte de código de barras que no exista en el backend.

### RF-09: Registrar y gestionar clientes

Compatible con `POST /api/clientes` y `PATCH /api/clientes/:id`.

### RF-10: Historial de ventas por fecha

El backend expone `GET /api/ventas` con paginación. Para historial por fechas, el frontend debe hacer el filtrado localmente o consultar el endpoint general y ordenar/filtrar en cliente.

---

## 4. Requisitos no incluidos o no forzados

Estos no se agregan al plan porque no están respaldados por la API actual. Se documentarán como futuras actualizaciones pendientes del backend o del producto:

- Roles distintos a `Admin` y `Vendedor`.
- Permisos tipo “supervisor” o “cajero” sin backend.
- Endpoints de factura, reporte contable o cierre de caja que no existan.
- Registro masivo de ventas con cálculo fiscal complejo fuera del flujo actual.
- Autenticación externa o OAuth si el backend no la expone.
- Funcionalidades avanzadas de inventario, auditoría o BI no contempladas todavía por la API.

### Futuras actualizaciones sugeridas

- Módulo de reportes financieros y cierre de caja.
- Exportación de ventas a PDF/Excel.
- Integración con códigos de barras físicos cuando el backend lo soporte.
- Mejoras de auditoría y trazabilidad de movimientos por usuario.
- Extensión de roles y permisos si el backend evoluciona.

---

## 5. Recursos visuales y configuración del proyecto

### Icono SVG

Se deberá usar el icono SVG existente del proyecto, con estilo moderno y minimalista, compatible con navegador, PWA y accesible en modo oscuro y claro. El archivo base es:

```txt
client/
  icono.svg
```

No se usará `Portada.jpg` a menos que el diseño final lo requiera como elemento visual opcional de marketing o splash; por el momento no es necesaria para la funcionalidad ni el plan base del proyecto.

### Variables de entorno

Se deben crear dos archivos de entorno en la raíz del frontend `client/`:

- `.env`
- `.env.example`

Ejemplo de variables sugeridas:

```env
VITE_API_BASE_URL=http://127.0.0.1:5000
VITE_APP_NAME=OdiseoPay
VITE_APP_ENV=development
VITE_ENABLE_PWA=true
VITE_DEFAULT_THEME=dark
```

Estos archivos deben usarse para centralizar la URL del backend y otros valores configurables, evitando hardcode dentro del código fuente.

---

## 6. Arquitectura recomendada del frontend

### Stack sugerido

- React 18+
- TypeScript
- Vite
- React Router
- React Query o TanStack Query
- Zustand para estado global
- Axios o Fetch centralizado
- Tailwind CSS o CSS Modules para UI
- PWA support con Vite PWA plugin y manifest

### Objetivo arquitectónico

- Que cada módulo funcione de forma independiente.
- Reducir componentes gigantes.
- Separar la capa de UI, datos, validaciones y servicios.
- Mantener bajo acoplamiento entre módulos.

---

## 6. Estructura de carpetas recomendada

```txt
client/
  src/
    app/
      App.tsx
      routes.tsx
      providers/
        AuthProvider.tsx
        QueryProvider.tsx
        ThemeProvider.tsx

    modules/
      auth/
        components/
          LoginForm.tsx
          RegisterAdminForm.tsx
        hooks/
          useLogin.ts
        pages/
          LoginPage.tsx
        services/
          auth.api.ts
        types/
          auth.types.ts

      dashboard/
        pages/
          DashboardPage.tsx
        components/
          SummaryCard.tsx
          RecentSalesList.tsx

      sales/
        components/
          ProductCartItem.tsx
          SaleSummary.tsx
          PaymentPanel.tsx
          SaleReceipt.tsx
          CustomerSelector.tsx
        hooks/
          useCreateSale.ts
        pages/
          NewSalePage.tsx
          SalesHistoryPage.tsx
        services/
          sales.api.ts

      products/
        components/
          ProductTable.tsx
          ProductForm.tsx
          ProductSearchBar.tsx
        pages/
          ProductsPage.tsx
          ProductFormPage.tsx
        services/
          products.api.ts

      customers/
        components/
          CustomerForm.tsx
          CustomerTable.tsx
        pages/
          CustomersPage.tsx
        services/
          customers.api.ts

      inventory/
        components/
          InventoryTable.tsx
          StockAlertCard.tsx
        pages/
          InventoryPage.tsx
        services/
          inventory.api.ts

      users/
        components/
          UserTable.tsx
          UserForm.tsx
        pages/
          UsersPage.tsx
        services/
          users.api.ts

      reports/
        components/
          DateRangeFilter.tsx
        pages/
          ReportsPage.tsx

    shared/
      components/
        AppShell.tsx
        Sidebar.tsx
        Topbar.tsx
        ModalConfirm.tsx
        EmptyState.tsx
        Badge.tsx
        InputField.tsx
        SelectField.tsx
        Button.tsx
        ThemeToggle.tsx

      hooks/
        useAuth.ts
        useDebounce.ts
        useDialog.ts
        useResponsive.ts

      lib/
        api.ts
        storage.ts
        utils.ts
        constants.ts

      schemas/
        auth.schema.ts
        product.schema.ts
        customer.schema.ts
        sale.schema.ts

      stores/
        authStore.ts
        uiStore.ts

      services/
        apiClient.ts
        errorHandler.ts

      utils/
        validation.ts
        formatters.ts
        permissions.ts

      types/
        api.ts
        common.ts

    styles/
      globals.css
      theme.css
      tokens.css

    pwa/
      manifest.ts
      service-worker.ts
```

### Principios de organización

- Cada módulo debe tener su propia carpeta con propósito claro.
- Cada componente debe vivir en un archivo propio.
- Las páginas deben ser delgadas y delegar lógica a hooks/services.
- Los servicios del backend deben centralizarse para evitar lógica repetida.

---

## 7. Sistema de rutas sugerido

```txt
/
  /login
  /dashboard
  /ventas/nueva
  /ventas/historial
  /productos
  /productos/nuevo
  /productos/:id/editar
  /clientes
  /clientes/nuevo
  /inventario
  /usuarios
  /usuarios/nuevo
  /reportes
  /perfil
```

### Reglas de navegación

- Rutas públicas: `/login`.
- Rutas protegidas: todas las demás.
- Acceso admin-only: usuarios, creación de usuarios, administración general.
- Acceso vendedor: ventas, productos, clientes, inventario y reportes básicos.

### Protección de rutas

- `ProtectedRoute` para validar token y rol.
- `AdminOnlyRoute` para controlar accesos sensibles.
- Redirección a `/login` si no hay sesión activa.

---

## 8. Sistema de autenticación y autorización

### Recomendación

- Guardar token JWT en almacenamiento seguro: `localStorage` o `sessionStorage`.
- Decodificar el payload del token para obtener el rol.
- Crear un store de autenticación con estado:
  - `user`
  - `token`
  - `role`
  - `isAuthenticated`
  - `login()`
  - `logout()`

### Permisos sugeridos

- Admin:
  - Usuarios
  - Productos
  - Clientes
  - Inventario
  - Compras
  - Reportes generales
  - Configuración de sistema

- Vendedor:
  - Ventas
  - Productos y clientes
  - Inventario consultivo
  - Historial de ventas

---

## 9. Sistema de estado recomendado

### Estado de servidor

Usar React Query/TanStack Query para:

- `usuarios`
- `productos`
- `clientes`
- `inventario`
- `ventas`
- `categorias`
- `proveedores`

Esto evita lógica manual de carga, reintentos y sincronización.

### Estado local

Usar Zustand para:

- autenticación
- tema oscuro/claro
- carrito de venta
- filtros activos en tablas
- modal de confirmación
- estado de UI global

### Beneficio

Separar claramente lo que viene del backend y lo que pertenece a la experiencia del usuario.

---

## 10. Validación de inputs y manejo de errores

El frontend debe validarlo antes de enviar al backend, con mensajes claros y amigables.

### Validaciones recomendadas

- Email válido.
- Teléfono válido (solo números, longitud real del negocio).
- Contraseña mínimo 8 caracteres.
- Nombre y apellido requeridos.
- Producto: nombre, precio de compra, precio de venta y categoría obligatorios.
- Cliente: nombre y teléfono mínimos obligatorios.
- Venta: producto válido, cantidad > 0, stock suficiente.

### Manejo de errores

- Centralizar en `apiClient` o `errorHandler`.
- Mostrar errores del backend con mensajes claros.
- Mostrar errores de validación del cliente en el formulario.
- Manejar `409` cuando se intenta eliminar un recurso relacionado.
- Manejar `401` y `403` con redirección o cierre de sesión.

### Confirmaciones de borrado

Todo delete debe pedir confirmación con un modal tipo:

> “¿Está seguro que desea eliminar este registro? Esta acción será permanente y puede afectar información relacionada.”

Esto es importante para productos, clientes, inventario y usuarios.

---

## 11. Diseño visual recomendado

### Estilo general

- Minimalista y limpio.
- Mobile-first, con layouts optimizados para pantallas pequeñas.
- Dark mode y light mode con tokens de color claros.
- Modo oscuro moderno con contraste equilibrado.
- Íconos sencillos y consistentes.

### Reglas de UI

- Botones con jerarquía visual clara.
- Campos con estados de error y éxito.
- Tarjetas de resumen con datos clave.
- Tablas compactas en móvil y expansibles en desktop.
- En venta: lista de productos, monto, ITBIS y cambio en un solo vistazo.

### Tema sugerido

- Fondo principal oscuro: gris muy oscuro / negro azulado.
- Accent: azul, verde o naranja moderno.
- Textos claros y de alto contraste.
- Spacing consistente y componentes pequeños.

---

## 12. PWA / TWA / Android / iPhone

### PWA

El proyecto debe prepararse para convertirse en PWA con:

- `manifest.json`
- iconos adaptados
- `service-worker`
- soporte offline básico
- instalación desde navegador móvil

### Android

Se puede convertir en TWA usando Bubblewrap para:

- empaquetar la PWA como app Android
- habilitar instalación desde Play Store o instalable localmente
- asegurar navegación completa y comportamiento nativo

### iPhone / iOS

La PWA debe poder instalarse desde Safari como aplicación web, siguiendo el patrón estándar de iOS.

### Recomendación técnica

- Mantener la app responsiva y sin dependencias nativas innecesarias.
- Asegurar que las rutas funcionen bien en fallback estático.
- Separar la capa web de la capa de instalación para evitar acoplamientos.

---

## 13. Gestion de errores y depuración

### Recomendaciones

- Registrar errores de red y validación con un logger central.
- Mostrar mensajes de error consistentes en UI.
- Mantener una traza clara del flujo:
  - login
  - carga de datos
  - guardado de venta
  - actualización de inventario
  - respuesta del backend

### Validación de flujos críticos

- Login inválido.
- Registro de usuario con rol incorrecto.
- Venta sin stock suficiente.
- Intento de borrar elemento con dependencias.
- Formulario con campos incompletos.

---

## 14. Recomendaciones de implementación concreta

1. Crear el proyecto React + TypeScript con Vite.
2. Definir estructura base de módulos y rutas.
3. Implementar sistema de autenticación, token y protección de rutas.
4. Crear entorno de consumo de API centralizado.
5. Diseñar flow de ventas primero, porque es el caso más crítico del negocio.
6. Implementar CRUD de productos, clientes e inventario.
7. Agregar reportes básicos por fecha y ventas.
8. Integrar validación visual y modales de confirmación.
9. Añadir tema dark/light y responsividad mobile-first.
10. Preparar PWA y TWA para instalación en Android.

---

## 15. Criterios de aprobación antes de implementación

Se considerará listo para pasar a la fase de codificación cuando:

- La arquitectura de rutas y módulos quede aprobada.
- El sistema de autenticación y roles coincida con el backend.
- La estructura de carpetas se entienda claramente para escalar.
- La validación de inputs y mensajes de error queden aceptados por negocio.
- El plan de PWA/TWA quede revisado con la intención de instalación móvil.

---

## 16. Conclusión

El backend ya define la base real de negocio y seguridad del sistema. El frontend debe reflejar esa estructura sin inventar módulos o permisos que no existen. La mejor apuesta es un diseño modular, mobile-first, con autenticación basada en JWT, rutas protegidas por rol, flujo de ventas fuerte, validaciones de input claras y preparación para PWA/TWA.

Este plan está preparado para revisión y aprobación antes de empezar la implementación real.
