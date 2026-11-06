import { useEffect } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../model/authContext';
import { LoginForm } from './login/LoginForm';
// Same stylesheet the panel uses, so the screen inherits the exact same tokens,
// controls and spacing instead of a look-alike copy.
import '@/shared/styles/panel.css';

const DEFAULT_DESTINATION = '/app/agenda';

/** Route `/entrar`. Sends an existing session straight in; otherwise shows the form. */
export default function LoginScreen() {
  const { status } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    document.title = 'Entrar · Navalha';
  }, []);

  if (status === 'authenticated') {
    return <Navigate to={DEFAULT_DESTINATION} replace />;
  }

  const destination =
    (location.state as { from?: { pathname: string } } | null)?.from?.pathname ??
    DEFAULT_DESTINATION;

  return (
    <div className="login-screen">
      <main className="login-card">
        <div className="login-brand">
          <div className="sidebar-brand-mark" />
          <span className="sidebar-brand-name">Navalha</span>
        </div>

        <h1 className="login-title">Entrar</h1>
        <p className="login-subtitle">Acesse o painel da sua barbearia.</p>

        <LoginForm onSignedIn={() => navigate(destination, { replace: true })} />

        <p className="login-foot">
          Esqueceu a senha? Fale com o dono da barbearia para receber um novo convite.
        </p>
      </main>
    </div>
  );
}
