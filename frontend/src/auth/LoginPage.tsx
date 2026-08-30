import { useEffect, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ApiError, NetworkError } from '@/api/http';
import { useAuth } from './AuthContext';
import { getTenantSlug, tenantComesFromHostname } from './tenant';
// Same stylesheet the panel uses, so the screen inherits the exact same tokens,
// controls and spacing instead of a look-alike copy.
import '@/app/app.css';

const DEFAULT_DESTINATION = '/app/agenda';

function messageFor(error: unknown): string {
  if (error instanceof NetworkError) {
    return 'Não foi possível falar com o servidor. Verifique se a API está no ar.';
  }
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return 'Barbearia não encontrada. Confira o endereço informado.';
    }
    // 401 and 403 already carry a message written for the end user.
    return error.message;
  }
  return 'Não foi possível entrar. Tente de novo.';
}

export default function LoginPage() {
  const { status, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // On localhost there is no subdomain to read the shop from, so it is asked
  // for. On <slug>.navalha.app the field never appears.
  const askForTenant = !tenantComesFromHostname();

  const [tenant, setTenant] = useState(() => getTenantSlug() ?? '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    document.title = 'Entrar · Navalha';
  }, []);

  if (status === 'authenticated') {
    return <Navigate to={DEFAULT_DESTINATION} replace />;
  }

  const destination =
    (location.state as { from?: { pathname: string } } | null)?.from?.pathname ??
    DEFAULT_DESTINATION;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (submitting) return;

    setError(null);
    setSubmitting(true);
    try {
      await signIn(email.trim(), password, askForTenant ? tenant.trim() : undefined);
      navigate(destination, { replace: true });
    } catch (err) {
      setError(messageFor(err));
      setSubmitting(false);
    }
  }

  return (
    <div className="login-screen">
      <main className="login-card">
        <div className="login-brand">
          <div className="sidebar-brand-mark" />
          <span className="sidebar-brand-name">Navalha</span>
        </div>

        <h1 className="login-title">Entrar</h1>
        <p className="login-subtitle">Acesse o painel da sua barbearia.</p>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          {error ? (
            <div className="login-error" role="alert">
              {error}
            </div>
          ) : null}

          {askForTenant ? (
            <label className="field">
              <span className="field-label">Barbearia</span>
              <input
                className="input"
                name="tenant"
                autoComplete="organization"
                placeholder="central"
                value={tenant}
                onChange={(e) => setTenant(e.target.value)}
                disabled={submitting}
                required
              />
              <span className="field-hint">
                O endereço da sua barbearia — em produção vem do próprio domínio.
              </span>
            </label>
          ) : null}

          <label className="field">
            <span className="field-label">E-mail</span>
            <input
              className="input"
              type="email"
              name="email"
              autoComplete="username"
              // eslint-disable-next-line jsx-a11y/no-autofocus
              autoFocus={!askForTenant}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={submitting}
              required
            />
          </label>

          <label className="field">
            <span className="field-label">Senha</span>
            <input
              className="input"
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              required
            />
          </label>

          <button type="submit" className="btn-primary login-submit" disabled={submitting}>
            {submitting ? 'Entrando…' : 'Entrar'}
          </button>
        </form>

        <p className="login-foot">
          Esqueceu a senha? Fale com o dono da barbearia para receber um novo convite.
        </p>
      </main>
    </div>
  );
}
