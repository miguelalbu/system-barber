import { Navigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/features/auth';
import { errorMessage } from '@/shared/api/errorMessage';
import { useShopSettings } from '../api/settings.queries';
import { SECTIONS, sectionOf } from '../model/settings.rules';
import BookingPoliciesSection from './booking-policies/BookingPoliciesSection';
import ShopSection from './shop/ShopSection';

/** `/app/configuracoes`: one section at a time (`?secao=`), each saving on its own. */
export default function SettingsScreen() {
  const { can } = useAuth();
  const [params, setParams] = useSearchParams();
  const section = sectionOf(params.get('secao'));
  const settings = useShopSettings();

  // Settings are the owner's (tenant:configure); others go back to the agenda.
  if (can('tenant:configure') === null) return <Navigate to="/app/agenda" replace />;

  return (
    <div className="page-pad settings-layout">
      <nav className="settings-nav" aria-label="Seções das configurações">
        {SECTIONS.map((s) => (
          <button
            type="button"
            key={s.key}
            className={`settings-nav-item${s.key === section ? ' is-active' : ''}`}
            aria-current={s.key === section ? 'page' : undefined}
            onClick={() => setParams({ secao: s.key }, { replace: true })}
          >
            {s.label}
          </button>
        ))}
      </nav>

      <div className="settings-body">
        {settings.isPending ? (
          <section className="panel">
            <div className="panel-body">
              <span className="skeleton-bar" />
            </div>
          </section>
        ) : null}
        {settings.isError ? (
          <section className="panel">
            <div className="form-alert" role="alert">
              {errorMessage(settings.error)}{' '}
              <button type="button" className="btn btn-sm" onClick={() => void settings.refetch()}>
                Tentar de novo
              </button>
            </div>
          </section>
        ) : null}
        {settings.data && section === 'barbearia' ? (
          <ShopSection settings={settings.data} />
        ) : null}
        {settings.data && section === 'agendamento' ? (
          <BookingPoliciesSection settings={settings.data} />
        ) : null}
      </div>
    </div>
  );
}
