import { Navigate, useParams } from 'react-router-dom';
import { useAuth } from '@/features/auth';
import { REGISTRY_PATH, registryPage } from '../model/registry.constants';
import BarbersTab from './barbers/BarbersTab';
import ServicesTab from './services/ServicesTab';
import UnitsPage from './units/UnitsPage';

/** One registry (`/app/cadastros/:registry`), opened from the sidebar dropdown. */
export default function RegistryPageScreen() {
  const { can } = useAuth();
  const page = registryPage(useParams().registry);

  // Unknown key (e.g. the old `planos`) or one the caller cannot read.
  if (!page || (page.permission !== null && !can(page.permission))) {
    return <Navigate to={REGISTRY_PATH} replace />;
  }

  return (
    <div className="page-pad">
      {page.key === 'unidades' ? <UnitsPage /> : null}
      {page.key === 'barbeiros' ? <BarbersTab /> : null}
      {page.key === 'servicos' ? <ServicesTab /> : null}
      {page.ready ? null : (
        <section className="panel">
          <div className="coming-soon">Em breve: este cadastro chega numa próxima etapa.</div>
        </section>
      )}
    </div>
  );
}
