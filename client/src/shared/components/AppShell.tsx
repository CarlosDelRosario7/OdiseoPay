import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className={`app-shell ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <Sidebar onClose={() => setSidebarOpen(false)} />

      <div className="app-main">
        <Topbar onMenuToggle={() => setSidebarOpen((open) => !open)} />
        <main className="content-panel">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
