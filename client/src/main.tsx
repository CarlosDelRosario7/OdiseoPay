import { createRoot } from 'react-dom/client'
import { Auth0Provider } from '@auth0/auth0-react'
import './index.css'
import App from './App.tsx'
import { auth0Config } from './shared/lib/auth0'

createRoot(document.getElementById('root')!).render(
  <Auth0Provider
    domain={auth0Config.domain}
    clientId={auth0Config.clientId}
    cacheLocation="localstorage"
    useRefreshTokens={false}
    authorizationParams={{
      redirect_uri: auth0Config.redirectUri,
      audience: auth0Config.audience,
    }}
  >
    <App />
  </Auth0Provider>,
)
