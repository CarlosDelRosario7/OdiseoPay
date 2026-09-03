import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icono.svg'],
      manifest: {
        name: 'OdiseoPay',
        short_name: 'OdiseoPay',
        description: 'Sistema de ventas e inventario',
        theme_color: '#0b1220',
        background_color: '#0b1220',
        display: 'standalone',
        start_url: '/',
        lang: 'es',
        icons: [{ src: '/icono.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'any maskable' }],
      },
    }),
  ],
})
