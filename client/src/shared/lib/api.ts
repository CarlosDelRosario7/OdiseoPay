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
    apiRequest<{ items: ProductSummary[] }>(
      `/api/productos?page=${page}&per_page=${perPage}`,
      'GET',
      { token },
    ),
  getClientes: (token: string) =>
    apiRequest<{ items: ClientSummary[] }>('/api/clientes?page=1&per_page=50', 'GET', {
      token,
    }),
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

export type ClientSummary = {
  id_cliente: number
  nombre: string
  apellido?: string
  telefono?: string
  correo?: string
}
