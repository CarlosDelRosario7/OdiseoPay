import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { useAuthStore } from '../store/authStore'

type ProtectedRouteProps = {
  children: ReactNode
  roles?: Array<'Admin' | 'Vendedor'>
}

export default function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const token = useAuthStore((state) => state.token)
  const role = useAuthStore((state) => state.user?.rol)
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (roles && (!role || !roles.includes(role))) return <Navigate to="/" replace />

  return children
}
