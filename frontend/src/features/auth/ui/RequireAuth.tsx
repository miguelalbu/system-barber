import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../model/authContext';

export default function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();

  // While /auth/me is in flight we know nothing yet. Rendering the login screen
  // here would flash it at every reload of an authenticated session.
  if (status === 'loading') {
    return <div className="auth-loading">Carregando…</div>;
  }

  if (status === 'anonymous') {
    // `from` lets the login screen send the user back where they were headed.
    return <Navigate to="/entrar" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
