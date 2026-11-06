import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/features/auth';
import { errorMessage } from '@/shared/api/errorMessage';
import { Badge } from '@/shared/ui/Badge';
import DeleteRecordDialog from '@/shared/ui/DeleteRecordDialog';
import TableState from '@/shared/ui/TableState';
import {
  useBarbers,
  useDeleteBarber,
  useServices,
  useSetBarberActive,
  useUnits,
} from '../../api/registry.queries';
import { formatCommission, servicesOf } from '../../model/barber.rules';
import type { Barber } from '../../model/registry.types';
import BarberForm from './BarberForm';

const COLUMNS = ['Barbeiro', 'Unidade', 'Serviços habilitados', 'Comissão', 'Acesso ao painel', 'Status', ''];

type StatusFilter = 'ativos' | 'inativos' | 'todos';

/** Barbers list with filters in the URL (`busca`, `unidade`, `status`) and the edit form. */
export default function BarbersTab() {
  const { can } = useAuth();
  const canWrite = can('team:manage') !== null;
  const [params, setParams] = useSearchParams();
  const search = params.get('busca') ?? '';
  const unitFilter = params.get('unidade') ?? '';
  const status = (params.get('status') as StatusFilter | null) ?? 'ativos';

  const barbers = useBarbers();
  const services = useServices();
  const units = useUnits();
  const setActive = useSetBarberActive();
  const remove = useDeleteBarber();

  const [editing, setEditing] = useState<Barber | 'new' | null>(null);
  const [deleting, setDeleting] = useState<Barber | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  }

  const unitName = new Map((units.data ?? []).map((u) => [u.id, u.name]));
  const term = search.trim().toLowerCase();
  const rows = (barbers.data ?? []).filter(
    (b) =>
      (!term || b.name.toLowerCase().includes(term)) &&
      (!unitFilter || b.unit_id === unitFilter) &&
      (status === 'todos' || b.active === (status === 'ativos')),
  );

  async function toggleActive(barber: Barber) {
    setRowError(null);
    try {
      await setActive.mutateAsync({ id: barber.id, active: !barber.active });
    } catch (e) {
      setRowError(errorMessage(e));
    }
  }

  return (
    <>
      <section className="panel">
        <div className="toolbar">
          <input
            className="input search-input"
            type="search"
            placeholder="Buscar barbeiro"
            aria-label="Buscar barbeiro"
            value={search}
            onChange={(e) => setFilter('busca', e.target.value)}
          />
          {(units.data?.length ?? 0) > 1 ? (
            <select
              className="select select-sm"
              aria-label="Unidade"
              value={unitFilter}
              onChange={(e) => setFilter('unidade', e.target.value)}
            >
              <option value="">Unidade: todas</option>
              {units.data?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          ) : null}
          <select
            className="select select-sm"
            aria-label="Status"
            value={status}
            onChange={(e) => setFilter('status', e.target.value === 'ativos' ? '' : e.target.value)}
          >
            <option value="ativos">Status: ativos</option>
            <option value="inativos">Status: inativos</option>
            <option value="todos">Status: todos</option>
          </select>
          <div className="toolbar-end">
            {barbers.data ? <span className="record-count">{rows.length} registros</span> : null}
            {canWrite ? (
              <button type="button" className="btn-primary" onClick={() => setEditing('new')}>
                Novo barbeiro
              </button>
            ) : null}
          </div>
        </div>

        {rowError ? (
          <div className="form-alert" role="alert">
            {rowError}
          </div>
        ) : null}

        <table className="table">
          <thead>
            <tr>
              {COLUMNS.map((c, i) => (
                <th key={c || 'actions'} className={i === COLUMNS.length - 1 ? 'col-right' : undefined}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {barbers.isPending ? <TableState columns={COLUMNS.length} state="loading" /> : null}
            {barbers.isError ? (
              <TableState
                columns={COLUMNS.length}
                state="error"
                message={errorMessage(barbers.error)}
                action={{ label: 'Tentar de novo', onClick: () => void barbers.refetch() }}
              />
            ) : null}
            {barbers.isSuccess && rows.length === 0 ? (
              <TableState
                columns={COLUMNS.length}
                state="empty"
                message={
                  barbers.data.length === 0
                    ? 'Nenhum barbeiro cadastrado ainda.'
                    : 'Nenhum barbeiro com esses filtros.'
                }
                action={
                  canWrite && barbers.data.length === 0
                    ? { label: 'Cadastrar barbeiro', onClick: () => setEditing('new') }
                    : undefined
                }
              />
            ) : null}
            {rows.map((b) => (
              <tr key={b.id}>
                <td>
                  <div className="staff-cell">
                    <div className="avatar avatar-sm">{b.initials}</div>
                    <div className="staff-name">{b.name}</div>
                  </div>
                </td>
                <td className="cell-muted">{unitName.get(b.unit_id) ?? '—'}</td>
                <td className="cell-muted">{servicesOf(b.id, services.data ?? [])}</td>
                <td className="tnum">{formatCommission(b.default_commission)}</td>
                <td className="cell-muted">{b.email ?? 'Sem acesso'}</td>
                <td>
                  <Badge kind={b.active ? 'ativo' : 'concluido'}>{b.active ? 'Ativo' : 'Inativo'}</Badge>
                </td>
                <td className="col-right">
                  {canWrite ? (
                    <span className="row-actions">
                      <button type="button" className="btn btn-sm" onClick={() => setEditing(b)}>
                        Editar
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm"
                        disabled={setActive.isPending}
                        onClick={() => void toggleActive(b)}
                      >
                        {b.active ? 'Inativar' : 'Reativar'}
                      </button>
                      {/* A barber with a login cannot be deleted (the API refuses): inactivate. */}
                      {b.user_id === null ? (
                        <button type="button" className="btn btn-sm" onClick={() => setDeleting(b)}>
                          Apagar
                        </button>
                      ) : null}
                    </span>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {editing ? (
        <BarberForm
          key={editing === 'new' ? 'new' : editing.id}
          barber={editing === 'new' ? null : editing}
          units={units.data ?? []}
          services={services.data ?? []}
          onClose={() => setEditing(null)}
        />
      ) : null}

      {deleting ? (
        <DeleteRecordDialog
          what={`o barbeiro ${deleting.name}`}
          onDelete={() => remove.mutateAsync(deleting.id)}
          onInactivate={
            deleting.active
              ? () => setActive.mutateAsync({ id: deleting.id, active: false })
              : undefined
          }
          onClose={() => setDeleting(null)}
        />
      ) : null}
    </>
  );
}
