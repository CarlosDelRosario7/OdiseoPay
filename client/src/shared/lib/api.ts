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
    // El backend devuelve mensajes concretos (cuenta no vinculada, conflicto
    // de vinculación, etc.). Priorizarlos evita ocultarlos tras un 401/403
    // genérico.
    if (typeof payload?.error === 'string' && payload.error.trim()) {
      throw new Error(payload.error)
    }
    if (typeof payload?.message === 'string' && payload.message.trim()) {
      throw new Error(payload.message)
    }
    if (response.status === 401) {
      throw new Error('Tu sesión expiró. Inicia sesión nuevamente.')
    }
    if (response.status === 403) {
      throw new Error('No tienes permisos para realizar esta acción.')
    }
    throw new Error('Ocurrió un error inesperado.')
  }

  return payload as T
}

export type AuthResponse = {
  access_token: string
  id_usuario: number
  nombre: string
  usuario: string
  rol: string
  auth0_sub?: string | null
  auth0_provider?: string | null
}

export type LinkAuth0Response = {
  auth0_sub: string
  auth0_provider: string | null
  message: string
}

export const api = {
  auth0Login: (auth0Token: string) =>
    apiRequest<AuthResponse>(
      '/api/auth/auth0/login',
      'POST',
      { token: auth0Token },
    ),
  linkAuth0: (token: string, auth0Token: string) =>
    apiRequest<LinkAuth0Response>(
      '/api/auth/auth0/vincular',
      'POST',
      { token, body: JSON.stringify({ auth0_token: auth0Token }) },
    ),
  unlinkAuth0: (token: string) =>
    apiRequest<void>(
      '/api/auth/auth0/vincular',
      'DELETE',
      { token },
    ),
  login: (data: { usuario: string; contrasena: string }) =>
    apiRequest<AuthResponse>(
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
  getProviders: (token: string) =>
    apiRequest<ListResponse<ProviderSummary>>('/api/proveedores?page=1&per_page=100', 'GET', { token }),
  createProvider: (token: string, data: ProviderInput) =>
    apiRequest<ProviderSummary>('/api/proveedores', 'POST', { token, body: JSON.stringify(data) }),
  updateProvider: (token: string, id: number, data: Partial<ProviderInput>) =>
    apiRequest<ProviderSummary>(`/api/proveedores/${id}`, 'PATCH', { token, body: JSON.stringify(data) }),
  deleteProvider: (token: string, id: number) =>
    apiRequest<void>(`/api/proveedores/${id}`, 'DELETE', { token }),
  getCategories: (token: string) =>
    apiRequest<ListResponse<CategorySummary>>('/api/categorias?page=1&per_page=100', 'GET', { token }),
  createCategory: (token: string, data: CategoryInput) =>
    apiRequest<CategorySummary>('/api/categorias', 'POST', { token, body: JSON.stringify(data) }),
  updateCategory: (token: string, id: number, data: Partial<CategoryInput>) =>
    apiRequest<CategorySummary>(`/api/categorias/${id}`, 'PATCH', { token, body: JSON.stringify(data) }),
  deleteCategory: (token: string, id: number) =>
    apiRequest<void>(`/api/categorias/${id}`, 'DELETE', { token }),
  createPurchase: (token: string, payload: PurchaseInput) =>
    apiRequest<PurchaseSummary>('/api/compras', 'POST', { token, body: JSON.stringify(payload) }),
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
export type ProviderSummary = { id_proveedor: number; nombre: string; telefono?: string; correo?: string; direccion?: string }
export type ProviderInput = Omit<ProviderSummary, 'id_proveedor'>
export type CategorySummary = { id_categoria: number; nombre: string; descripcion?: string }
export type CategoryInput = Omit<CategorySummary, 'id_categoria'>
export type PurchaseDetailInput = { id_producto: number; cantidad: number; precio: string }
export type PurchaseInput = { id_proveedor: number; detalles: PurchaseDetailInput[] }
export type PurchaseSummary = { id_compra: number; fecha?: string; id_proveedor: number; id_usuario: number }
