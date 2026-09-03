const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:5000'

type ApiMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE'

type RequestOptions = RequestInit & {
  token?: string
}

async function apiRequest<T>(
  path: string,
  method: ApiMethod,
  options: RequestOptions = {},
): Promise<T> {
  const { token, headers: customHeaders, body, ...rest } = options

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    ...rest,
    body,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(customHeaders ?? {}),
    },
  })

  if (response.status === 204) {
    return undefined as T
  }

  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Tu sesión expiró. Inicia sesión nuevamente.')
    }
    if (response.status === 403) {
      throw new Error('No tienes permisos para realizar esta acción.')
    }
    const message =
      payload?.error ?? payload?.message ?? 'Ocurrió un error inesperado.'
    throw new Error(message)
  }

  return payload as T
}

export const api = {
  login: (data: { usuario: string; contrasena: string }) =>
    apiRequest<{ access_token: string; usuario: string; rol: string }>(
      '/api/auth/login',
      'POST',
      { body: JSON.stringify(data) },
    ),
  getProducts: (token: string, page = 1, perPage = 20) =>
    apiRequest<ListResponse<ProductSummary>>(
      `/api/productos?page=${page}&per_page=${perPage}`,
      'GET',
      { token },
    ),
  getClientes: (token: string) =>
    apiRequest<ListResponse<ClientSummary>>('/api/clientes?page=1&per_page=50', 'GET', {
      token,
    }),
  createProduct: (token: string, data: ProductInput) =>
    apiRequest<ProductSummary>('/api/productos', 'POST', { token, body: JSON.stringify(data) }),
  updateProduct: (token: string, id: number, data: Partial<ProductInput>) =>
    apiRequest<ProductSummary>(`/api/productos/${id}`, 'PATCH', { token, body: JSON.stringify(data) }),
  deleteProduct: (token: string, id: number) =>
    apiRequest<void>(`/api/productos/${id}`, 'DELETE', { token }),
  getInventory: (token: string) =>
    apiRequest<ListResponse<InventoryItem>>('/api/inventario?page=1&per_page=100', 'GET', { token }),
  getSales: (token: string) =>
    apiRequest<ListResponse<SaleSummary>>('/api/ventas?page=1&per_page=100', 'GET', { token }),
  updateInventory: (token: string, id: number, data: Partial<InventoryInput>) =>
    apiRequest<InventoryItem>(`/api/inventario/${id}`, 'PATCH', { token, body: JSON.stringify(data) }),
  createClient: (token: string, data: ClientInput) =>
    apiRequest<ClientSummary>('/api/clientes', 'POST', { token, body: JSON.stringify(data) }),
  updateClient: (token: string, id: number, data: Partial<ClientInput>) =>
    apiRequest<ClientSummary>(`/api/clientes/${id}`, 'PATCH', { token, body: JSON.stringify(data) }),
  deleteClient: (token: string, id: number) =>
    apiRequest<void>(`/api/clientes/${id}`, 'DELETE', { token }),
  getUsers: (token: string) =>
    apiRequest<ListResponse<UserSummary>>('/api/usuarios?page=1&per_page=100', 'GET', { token }),
  createUser: (token: string, data: UserInput) =>
    apiRequest<{ id_usuario: number }>('/api/usuarios', 'POST', { token, body: JSON.stringify(data) }),
  updateUser: (token: string, id: number, data: Partial<UserInput>) =>
    apiRequest<UserSummary>(`/api/usuarios/${id}`, 'PATCH', { token, body: JSON.stringify(data) }),
  deleteUser: (token: string, id: number) =>
    apiRequest<void>(`/api/usuarios/${id}`, 'DELETE', { token }),
  createSale: (token: string, payload: Record<string, unknown>) =>
    apiRequest<Record<string, unknown>>('/api/ventas', 'POST', {
      token,
      body: JSON.stringify(payload),
    }),
}

export type ProductSummary = {
  id_producto: number
  nombre: string
  descripcion?: string
  precio_venta: string | number
  precio_compra?: string | number
  id_categoria?: number
  id_proveedor?: number
}

export type ListResponse<T> = { items: T[]; total: number; page: number; pages: number }

export type ProductInput = Omit<ProductSummary, 'id_producto'>

export type InventoryItem = {
  id_inventario: number
  id_producto: number
  cantidad: number
  stock_minimo: number
  ubicacion?: string
}

export type InventoryInput = Omit<InventoryItem, 'id_inventario'>

export type ClientSummary = {
  id_cliente: number
  nombre: string
  apellido?: string
  telefono?: string
  correo?: string
}

export type ClientInput = Omit<ClientSummary, 'id_cliente'> & { direccion?: string }

export type UserSummary = { id_usuario: number; nombre: string; usuario: string; rol: string }
export type UserInput = { nombre: string; usuario: string; contrasena?: string; rol: 'Admin' | 'Vendedor' }
export type SaleSummary = { id_venta: number; fecha?: string; id_cliente: number; id_usuario: number }
