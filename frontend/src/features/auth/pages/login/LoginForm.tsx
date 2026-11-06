import { useState } from 'react';
import { ApiError, NetworkError } from '@/shared/api/http';
import { getTenantSlug, tenantComesFromHostname } from '@/shared/session/tenant';
import { useAuth } from '../../model/authContext';

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

/** E-mail, password and — on localhost only — the shop. Calls `onSignedIn` on success. */
export function LoginForm({ onSignedIn }: { onSignedIn: () => void }) {
  const { signIn } = useAuth();

  // On localhost there is no subdomain to read the shop from, so it is asked
  // for. On <slug>.navalha.app the field never appears.
  const askForTenant = !tenantComesFromHostname();

  const [tenant, setTenant] = useState(() => getTenantSlug() ?? '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (submitting) return;

    setError(null);
    setSubmitting(true);
    try {
      await signIn(email.trim(), password, askForTenant ? tenant.trim() : undefined);
      onSignedIn();
    } catch (err) {
      setError(messageFor(err));
      setSubmitting(false);
    }
  }

  return (
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
  );
}
