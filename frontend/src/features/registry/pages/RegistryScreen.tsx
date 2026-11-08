import { Navigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/features/auth';
import { REGISTRY_PATH, registryPage, visibleRegistries } from '../model/registry.constants';

/**
 * `/app/cadastros` has no page of its own: the registries live in the sidebar
 * dropdown, so the bare path opens the first one the user may read.
 */
export default function RegistryScreen() {
  const { can } = useAuth();
  const [params] = useSearchParams();

  // Links from the tabbed version (`?aba=barbeiros`) still land on the right page.
  const target = registryPage(params.get('aba') ?? undefined) ?? visibleRegistries(can)[0];
  if (!target) return <Navigate to="/app/agenda" replace />;
  return <Navigate to={`${REGISTRY_PATH}/${target.key}`} replace />;
}
