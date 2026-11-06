import { useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { tokenFromPath } from '../model/invite.rules';
import { AcceptInviteForm } from './accept-invite/AcceptInviteForm';
import '@/shared/styles/panel.css';

/**
 * Route `/convite/:token` — the link every invite carries, including the
 * owner's first access to a newly provisioned shop.
 */
export default function AcceptInviteScreen() {
  const { token } = useParams();
  const navigate = useNavigate();
  const value = tokenFromPath(token);

  useEffect(() => {
    document.title = 'Primeiro acesso · Navalha';
  }, []);

  return (
    <div className="login-screen">
      <main className="login-card">
        <div className="login-brand">
          <div className="sidebar-brand-mark" />
          <span className="sidebar-brand-name">Navalha</span>
        </div>

        <h1 className="login-title">Primeiro acesso</h1>
        <p className="login-subtitle">Defina sua senha para entrar no painel da barbearia.</p>

        {value ? (
          <AcceptInviteForm
            token={value}
            onSignedIn={() => navigate('/app/agenda', { replace: true })}
          />
        ) : (
          <div className="login-error" role="alert">
            Link de convite incompleto.
          </div>
        )}

        <p className="login-foot">
          Já tem acesso? <Link to="/entrar">Entrar</Link>
        </p>
      </main>
    </div>
  );
}
