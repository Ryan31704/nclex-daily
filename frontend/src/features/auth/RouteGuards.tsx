import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { LoadingScreen } from '../../components/LoadingScreen'
import { useAuth } from './useAuth'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <LoadingScreen />
  }
  if (!user) {
    return <Navigate replace state={{ from: location }} to="/login" />
  }
  return <Outlet />
}

export function GuestOnlyRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }
  if (user) {
    return <Navigate replace to="/dashboard" />
  }
  return <Outlet />
}
