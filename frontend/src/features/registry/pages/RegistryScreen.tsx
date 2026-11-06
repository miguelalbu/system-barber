import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/features/auth';
import { REGISTRY_TABS, type RegistryTab } from '../model/registry.constants';
import BarbersTab from './barbers/BarbersTab';
import ServicesTab from './services/ServicesTab';

/** "Cadastros": one tab per registry; the active tab lives in the URL (`?aba=`). */
export default function RegistryScreen() {
  const { can } = useAuth();
  const [params, setParams] = useSearchParams();

  const visible = REGISTRY_TABS.filter(
    (t) =>
      (t.key !== 'barbeiros' || can('team:read')) && (t.key !== 'servicos' || can('catalog:read')),
  );
  const requested = params.get('aba') as RegistryTab | null;
  const fallback = visible.find((t) => t.key === 'barbeiros' || t.key === 'servicos') ?? visible[0];
  const tab = visible.find((t) => t.key === requested)?.key ?? fallback?.key;

  function select(key: RegistryTab) {
    setParams({ aba: key });
  }

  return (
    <div className="page-pad">
      <div className="tab-row" role="tablist">
        {visible.map((t) => (
          <button
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            key={t.key}
            className={`pill pill-lg${tab === t.key ? ' is-active' : ''}`}
            onClick={() => select(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'barbeiros' ? <BarbersTab /> : null}
      {tab === 'servicos' ? <ServicesTab /> : null}
      {tab !== 'barbeiros' && tab !== 'servicos' ? (
        <section className="panel">
          <div className="coming-soon">Em breve: este cadastro chega numa próxima etapa.</div>
        </section>
      ) : null}
    </div>
  );
}
