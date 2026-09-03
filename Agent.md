En esta rama, quiero que me ayudes con toda la parte frontend [client]{/client} que es un proyecto aparte, pero depende totalmente del backend [server]{/server}. Por tanto, quiero que le des un review al backend. Principalmente al archivo test.http [test.http]{/server/test.http} que es el archivo que contiene todos los endpoints que se van a consumir desde el frontend. Ya los endpoint fueron probados y funcionan correctamente. Busco una interfaz minimalista y simple, pero usa íconos y colores modernos (modo oscuro y claro) y que sea responsivo (como si es principalmente para móviles, pero que también se vea bien en pantallas grandes). Quiero que me ayudes a estructurar el frontend de la mejor manera posible, siguiendo buenas prácticas y patrones de diseño. Que esté lo más modularizado posible, que cada componente tenga su propio archivo y que no haya componentes muy grandes. Que se pueda escalar fácilmente y que sea fácil de mantener. Que tenga una buena estructura de carpetas y que cada carpeta tenga un propósito específico. Que tenga un buen sistema de rutas y que sea fácil de navegar. Que tenga un buen sistema de estado y que sea fácil de manejar. Que tenga un buen sistema de autenticación y autorización. Que tenga un buen sistema de manejo de errores y que sea fácil de depurar. El sistema será en React.js con TypeScript. Y debe tener manejo de errores en los input que entre el usuario (correo, teléfono, contraseña de 8 caracteres, etc.) y que pregunte si está seguro de borrar cualquier cosa porque se hará permanentemente en la base de datos. Según el backend, el primer usuario creado es Admin, y los demás son vendedores; así que se debe tener esto en cuenta.

Requisitos Funcionales
1. RF-01: El sistema debe permitir el inicio de sesión mediante credenciales únicas para cada usuario. 
2. RF-02: El sistema debe permitir registrar una venta seleccionando múltiples productos. 
3. RF-03: El sistema debe calcular automáticamente el subtotal, ITBIS (impuestos) y el total de la venta. 
4. RF-04: El sistema debe calcular el cambio a devolver al cliente basado en el monto recibido. 
5. RF-05: El sistema debe generar un recibo de venta en formato digital o para impresión. 
6. RF-06: El sistema debe descontar automáticamente del inventario la cantidad de productos vendidos. 
7. RF-07: El sistema debe permitir la creación, edición y eliminación de productos en el catálogo. 
8. RF-08: El sistema debe permitir la búsqueda de productos por nombre o código de barras. 
9. RF-09: El sistema debe permitir registrar y gestionar datos básicos de clientes (nombre, teléfono). 
10. RF-10: El sistema debe permitir consultar un historial de ventas realizadas por fecha.

Claro, esto requicitos deben estar de acuerdo con el backend, de lo contrario, no lo agregues porque será un caos luego.

El plan es que se pueda volver PWA (Progressive Web App) y que se pueda convertir a apk con bublewrap (burbuja de plastico) para que el TWA pueda instalarse en dispositivos Android. Y, en el caso de IOS, se pueda instalar como PWA.

Hasta ahora, no quiero que implementes nada. Solo crea un plan.md para ver si está todo correcto y proceder. Guarda el plan en un archivo llamado [plan.md]{/plan.md} para que podamos revisarlo y aprobarlo antes de proceder a la implementación.