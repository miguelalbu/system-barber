import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/features/auth';
import { useClients } from '../api/customers.queries';
import { pageFrom } from '../model/customer.rules';
import type { Client } from '../model/customers.types';
import ClientForm from './form/ClientForm';
import ClientsTable from './list/ClientsTable';

const SEARCH_DELAY_MS = 300;

/** "Clientes": paged search (`?q=`, `?pagina=` in the URL) and the client form. */
export default function CustomersScreen() {
  const { can } = useAuth();
  const canWrite = can('client:write') !== null;
  const [params, setParams] = useSearchParams();
  const q = params.get('q') ?? '';
  const page = pageFrom(params.get('pagina'));
  const [typed, setTyped] = useState(q);
  const [editing, setEditing] = useState<Client | 'new' | null>(null);

  // The URL follows the search box after a pause, so each keystroke is not a request.
  useEffect(() => {
    if (typed.trim() === q) return;
    const timer = window.setTimeout(() => {
      const next = new URLSearchParams(params);
      if (typed.trim()) next.set('q', typed.trim());
      else next.delete('q');
      next.delete('pagina');
      setParams(next, { replace: true });
    }, SEARCH_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [typed, q, params, setParams]);

  function goTo(nextPage: number) {
    const next = new URLSearchParams(params);
    if (nextPage > 1) next.set('pagina', String(nextPage));
    else next.delete('pagina');
    setParams(next);
  }

  const clients = useClients({ q, page });

  return (
    <div className="page-pad">
      <section className="panel">
        <div className="toolbar">
          <input
            className="input search-input"
            type="search"
            placeholder="Buscar por nome ou telefone"
            aria-label="Buscar cliente"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
          />
          <div className="toolbar-end">
            {clients.data ? <span className="record-count">{clients.data.total} registros</span> : null}
            {canWrite ? (
              <button type="button" className="btn-primary" onClick={() => setEditing('new')}>
                Novo cliente
              </button>
            ) : null}
          </div>
        </div>

        <ClientsTable
          query={clients}
          searching={Boolean(q)}
          page={page}
          canWrite={canWrite}
          ownOnly={can('client:read') === 'own'}
          onEdit={setEditing}
          onCreate={() => setEditing('new')}
          onPage={goTo}
        />
      </section>

      {editing ? (
        <ClientForm
          key={editing === 'new' ? 'new' : editing.id}
          client={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
        />
      ) : null}
    </div>
  );
}
