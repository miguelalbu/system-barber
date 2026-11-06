import { useCallback, useEffect, useState } from 'react';
import { ApiError, NetworkError } from '@/shared/api/http';
import { getTenantSlug, setTenantSlug, tenantComesFromHostname } from '@/shared/session/tenant';
import * as authApi from '../../api/auth.api';
import { ROLE_LABELS } from '../../model/auth.constants';
import { useAuth } from '../../model/authContext';
import type { InviteLookup } from '../../model/auth.types';
import { passwordProblem } from '../../model/invite.rules';

const DEAD_LINK =
  'Este convite é inválido, expirou ou já foi usado. Peça um novo link a quem convidou você.';

function messageFor(error: unknown): string {
  if (error instanceof NetworkError) {
    return 'Não foi possível falar com o servidor. Verifique se a API está no ar.';
  }
  if (error instanceof ApiError) {
    if (error.status === 400) return DEAD_LINK;
    if (error.status === 404) return 'Barbearia não encontrada. Confira o endereço informado.';
    return error.message;
  }
  return 'Não foi possível concluir. Tente de novo.';
}

type Step = 'shop' | 'checking' | 'password' | 'dead';

/**
 * Team invite and owner's first access: check the link, then choose a
 * password and enter. The link is checked **before** asking for the password —
 * finding out it expired after typing it twice is the worst possible order.
 */
export function AcceptInviteForm({ token, onSignedIn }: { token: string; onSignedIn: () => void }) {
  const { signIn } = useAuth();

  // On localhost the shop cannot come from the address, so it is asked for
  // first (the invite link points at <slug>.<domínio> in production).
  const askForTenant = !tenantComesFromHostname();
  const [tenant, setTenant] = useState(() => getTenantSlug() ?? '');
  const [step, setStep] = useState<Step>(askForTenant && !getTenantSlug() ? 'shop' : 'checking');
  const [invite, setInvite] = useState<InviteLookup | null>(null);
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const check = useCallback(async () => {
    setError(null);
    setStep('checking');
    try {
      setInvite(await authApi.lookupInvite(token));
      setStep('password');
    } catch (err) {
      setError(messageFor(err));
      setStep(err instanceof ApiError && err.status === 400 ? 'dead' : askForTenant ? 'shop' : 'dead');
    }
  }, [token, askForTenant]);

  useEffect(() => {
    if (step === 'checking' && !invite) void check();
    // Only on mount: later checks are triggered by the shop step.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function confirmShop(event: React.FormEvent) {
    event.preventDefault();
    if (!tenant.trim()) return;
    setTenantSlug(tenant);
    void check();
  }

  async function accept(event: React.FormEvent) {
    event.preventDefault();
    if (!invite || submitting) return;
    const problem = passwordProblem(password, confirmation);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await authApi.acceptInvite(token, password);
      await signIn(invite.email, password, askForTenant ? tenant.trim() : undefined);
      onSignedIn();
    } catch (err) {
      setError(messageFor(err));
      setSubmitting(false);
    }
  }

  const alert = error ? (
    <div className="login-error" role="alert">
      {error}
    </div>
  ) : null;

  if (step === 'shop') {
    return (
      <form className="login-form" onSubmit={confirmShop} noValidate>
        {alert}
        <label className="field">
          <span className="field-label">Barbearia</span>
          <input
            className="input"
            name="tenant"
            autoComplete="organization"
            placeholder="central"
            autoFocus
            value={tenant}
            onChange={(e) => setTenant(e.target.value)}
            required
          />
          <span className="field-hint">
            O endereço da barbearia que convidou você — em produção vem do próprio link.
          </span>
        </label>
        <button type="submit" className="btn-primary login-submit">
          Continuar
        </button>
      </form>
    );
  }

  if (step === 'checking') {
    return <p className="login-subtitle">Verificando o convite…</p>;
  }

  if (step === 'dead' || !invite) {
    return (
      <div className="login-form">
        {alert ?? (
          <div className="login-error" role="alert">
            {DEAD_LINK}
          </div>
        )}
      </div>
    );
  }

  return (
    <form className="login-form" onSubmit={accept} noValidate>
      {alert}
      <p className="login-subtitle">
        Olá, <strong>{invite.name}</strong>. Você entra como {ROLE_LABELS[invite.role]} com o
        e-mail <strong>{invite.email}</strong>.
      </p>

      <label className="field">
        <span className="field-label">Senha</span>
        <input
          className="input"
          type="password"
          name="new-password"
          autoComplete="new-password"
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={submitting}
          required
        />
        <span className="field-hint">Pelo menos 8 caracteres.</span>
      </label>

      <label className="field">
        <span className="field-label">Repita a senha</span>
        <input
          className="input"
          type="password"
          name="confirm-password"
          autoComplete="new-password"
          value={confirmation}
          onChange={(e) => setConfirmation(e.target.value)}
          disabled={submitting}
          required
        />
      </label>

      <button type="submit" className="btn-primary login-submit" disabled={submitting}>
        {submitting ? 'Entrando…' : 'Definir senha e entrar'}
      </button>
    </form>
  );
}
