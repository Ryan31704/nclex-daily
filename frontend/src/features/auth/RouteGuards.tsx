import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { LoadingScreen } from '../../components/LoadingScreen'
import { useAuth } from './useAuth'

export function ProtectedRoute() {
  const { user, loading, passwordSetupRequired } = useAuth()
  const location = useLocation()

  if (loading) {
    return <LoadingScreen />
  }
  if (!user) {
    return <Navigate replace state={{ from: location }} to="/login" />
  }
  if (passwordSetupRequired && location.pathname !== '/set-password') {
    return <Navigate replace to="/set-password" />
  }
  return <Outlet />
}

export function GuestOnlyRoute() {
  const { user, loading, passwordSetupRequired } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }
  if (user) {
    return <Navigate replace to={passwordSetupRequired ? '/set-password' : '/dashboard'} />
  }
  return <Outlet />
}

export function LandingRoute() {
  const { user, loading, passwordSetupRequired } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }
  if (user && passwordSetupRequired) {
    return <Navigate replace to="/set-password" />
  }
  return <Outlet />
}

export function PasswordSetupRoute() {
  const { user, loading, passwordSetupRequired } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }
  if (user && !passwordSetupRequired) {
    return <Navigate replace to="/dashboard" />
  }
  return <Outlet />
}
