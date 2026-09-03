import { Navigate, Route, Routes } from 'react-router-dom'

import LoginPage from '../modules/auth/pages/LoginPage'
import DashboardPage from '../modules/dashboard/pages/DashboardPage'
import CustomersPage from '../modules/customers/pages/CustomersPage'
import InventoryPage from '../modules/inventory/pages/InventoryPage'
import ProductsPage from '../modules/products/pages/ProductsPage'
import SalesPage from '../modules/sales/pages/SalesPage'
import UsersPage from '../modules/users/pages/UsersPage'
import ProvidersPage from '../modules/providers/pages/ProvidersPage'
import CategoriesPage from '../modules/categories/pages/CategoriesPage'
import PurchasesPage from '../modules/purchases/pages/PurchasesPage'
import SalesHistoryPage from '../modules/sales/pages/SalesHistoryPage'
import AppShell from '../shared/components/AppShell'
import ProtectedRoute from '../shared/components/ProtectedRoute'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="/ventas" element={<SalesPage />} />
        <Route path="/ventas/historial" element={<SalesHistoryPage />} />
        <Route path="/productos" element={<ProductsPage />} />
        <Route path="/clientes" element={<CustomersPage />} />
        <Route path="/inventario" element={<InventoryPage />} />
        <Route path="/usuarios" element={<ProtectedRoute roles={['Admin']}><UsersPage /></ProtectedRoute>} />
        <Route path="/proveedores" element={<ProtectedRoute roles={['Admin']}><ProvidersPage /></ProtectedRoute>} />
        <Route path="/categorias" element={<CategoriesPage />} />
        <Route path="/compras" element={<ProtectedRoute roles={['Admin']}><PurchasesPage /></ProtectedRoute>} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
