// Valores públicos de la SPA de Auth0. Un Client ID de SPA no es un secreto.
// Se pueden sobrescribir con client/.env sin tocar el código.
const DEFAULT_AUTH0_DOMAIN = 'dev-mjgxqjikayj2605h.us.auth0.com'
const DEFAULT_AUTH0_CLIENT_ID = 'KTIURFsJfii0Q3EcCfHSa8FL2RN49QWz'
const DEFAULT_AUTH0_AUDIENCE = 'https://api.odiseopay.com'

function readEnv(value: string | undefined, fallback: string) {
  const normalized = value?.trim()
  return normalized ? normalized : fallback
}

export const auth0Config = {
  domain: readEnv(import.meta.env.VITE_AUTH0_DOMAIN, DEFAULT_AUTH0_DOMAIN),
  clientId: readEnv(import.meta.env.VITE_AUTH0_CLIENT_ID, DEFAULT_AUTH0_CLIENT_ID),
  audience: readEnv(import.meta.env.VITE_AUTH0_AUDIENCE, DEFAULT_AUTH0_AUDIENCE),
  redirectUri: `${window.location.origin}/login`,
}

export const isAuth0Configured = Boolean(
  auth0Config.domain && auth0Config.clientId,
)

export const auth0Connections = {
  google: 'google-oauth2',
  facebook: 'facebook',
} as const

// La vinculación usa redirección en la misma pestaña. Estas claves permiten
// recordar la intención y mostrar el resultado al volver a la aplicación.
const LINK_INTENT_KEY = 'odiseopay:auth0-link-intent'
const LINK_RETURN_KEY = 'odiseopay:auth0-link-return'
const LINK_RESULT_KEY = 'odiseopay:auth0-link-result'
const LINK_INTENT_TTL_MS = 30 * 60 * 1000

export type Auth0LinkResult = {
  type: 'success' | 'error'
  message: string
}

export function startLinkIntent(returnTo: string) {
  sessionStorage.setItem(LINK_INTENT_KEY, String(Date.now()))
  sessionStorage.setItem(LINK_RETURN_KEY, returnTo)
  sessionStorage.removeItem(LINK_RESULT_KEY)
}

export function hasLinkIntent() {
  const startedAt = Number(sessionStorage.getItem(LINK_INTENT_KEY))

  if (!Number.isFinite(startedAt) || startedAt <= 0) {
    return false
  }

  if (Date.now() - startedAt > LINK_INTENT_TTL_MS) {
    clearLinkIntent()
    return false
  }

  return true
}

export function consumeLinkReturnTo() {
  const returnTo = sessionStorage.getItem(LINK_RETURN_KEY) || '/'
  sessionStorage.removeItem(LINK_RETURN_KEY)
  return returnTo
}

export function clearLinkIntent() {
  sessionStorage.removeItem(LINK_INTENT_KEY)
  sessionStorage.removeItem(LINK_RETURN_KEY)
}

export function setLinkResult(result: Auth0LinkResult) {
  sessionStorage.setItem(LINK_RESULT_KEY, JSON.stringify(result))
}

export function readLinkResult(): Auth0LinkResult | null {
  const raw = sessionStorage.getItem(LINK_RESULT_KEY)

  if (!raw) {
    return null
  }

  try {
    const result = JSON.parse(raw) as Auth0LinkResult

    if (
      (result.type === 'success' || result.type === 'error') &&
      typeof result.message === 'string'
    ) {
      return result
    }
  } catch {
    // Resultado corrupto: se ignora.
  }

  return null
}

export function clearLinkResult() {
  sessionStorage.removeItem(LINK_RESULT_KEY)
}
