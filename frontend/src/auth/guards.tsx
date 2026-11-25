import { Navigate, Outlet } from 'react-router'
import { useAppSelector } from '../hooks'

function Loading() {
  // role="status" makes screen readers announce the wait politely.
  return <p role="status">Carregando…</p>
}

// Layout route for private pages: only a confirmed session gets through.
export function RequireAuth() {
  const status = useAppSelector((state) => state.auth.status)

  if (status === 'checking') return <Loading />
  if (status === 'anonymous') return <Navigate to="/login" replace />
  return <Outlet />
}

// Layout route for login/register: a signed-in visitor has no business here.
export function PublicOnly() {
  const status = useAppSelector((state) => state.auth.status)

  if (status === 'checking') return <Loading />
  if (status === 'authenticated') return <Navigate to="/" replace />
  return <Outlet />
}
