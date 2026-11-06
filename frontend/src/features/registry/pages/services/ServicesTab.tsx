import { useState } from 'react';
import { useAuth, useMe } from '@/features/auth';
import { errorMessage } from '@/shared/api/errorMessage';
import { formatDuration } from '@/shared/text/duration';
import { formatBRL } from '@/shared/text/money';
import { Badge } from '@/shared/ui/Badge';
import DeleteRecordDialog from '@/shared/ui/DeleteRecordDialog';
import TableState from '@/shared/ui/TableState';
import { useDeleteService, useServices, useSetServiceActive } from '../../api/registry.queries';
import type { Service } from '../../model/registry.types';
import ServiceForm from './ServiceForm';

const COLUMNS = ['Serviço', 'Duração', 'Preço', 'Barbeiros', 'Status', ''];

/** Services list and form. Shop-wide: only who sees every unit may change them. */
export default function ServicesTab() {
  const { can } = useAuth();
  const me = useMe();
  const canWrite = can('catalog:write') !== null && me.all_units;
  const services = useServices();
  const setActive = useSetServiceActive();
  const remove = useDeleteService();

  const [editing, setEditing] = useState<Service | 'new' | null>(null);
  const [deleting, setDeleting] = useState<Service | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  async function toggleActive(service: Service) {
    setRowError(null);
    try {
      await setActive.mutateAsync({ id: service.id, active: !service.active });
    } catch (e) {
      setRowError(errorMessage(e));
    }
  }

  return (
    <>
      <section className="panel">
        <div className="toolbar">
          {can('catalog:write') !== null && !me.all_units ? (
            <span className="field-hint">
              Serviços valem para todas as unidades; só quem administra todas pode alterá-los.
            </span>
          ) : null}
          <div className="toolbar-end">
            {services.data ? <span className="record-count">{services.data.length} registros</span> : null}
            {canWrite ? (
              <button type="button" className="btn-primary" onClick={() => setEditing('new')}>
                Novo serviço
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
            {services.isPending ? <TableState columns={COLUMNS.length} state="loading" /> : null}
            {services.isError ? (
              <TableState
                columns={COLUMNS.length}
                state="error"
                message={errorMessage(services.error)}
                action={{ label: 'Tentar de novo', onClick: () => void services.refetch() }}
              />
            ) : null}
            {services.isSuccess && services.data.length === 0 ? (
              <TableState
                columns={COLUMNS.length}
                state="empty"
                message="Nenhum serviço cadastrado ainda."
                action={canWrite ? { label: 'Cadastrar serviço', onClick: () => setEditing('new') } : undefined}
              />
            ) : null}
            {services.data?.map((s) => (
              <tr key={s.id}>
                <td>
                  <div className="staff-name">{s.name}</div>
                  {s.description ? <div className="staff-email">{s.description}</div> : null}
                </td>
                <td className="cell-muted tnum">{formatDuration(s.duration_minutes)}</td>
                <td className="tnum">{formatBRL(s.price_cents)}</td>
                <td className="cell-muted tnum">{s.barber_ids.length}</td>
                <td>
                  <Badge kind={s.active ? 'ativo' : 'concluido'}>{s.active ? 'Ativo' : 'Inativo'}</Badge>
                </td>
                <td className="col-right">
                  {canWrite ? (
                    <span className="row-actions">
                      <button type="button" className="btn btn-sm" onClick={() => setEditing(s)}>
                        Editar
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm"
                        disabled={setActive.isPending}
                        onClick={() => void toggleActive(s)}
                      >
                        {s.active ? 'Inativar' : 'Reativar'}
                      </button>
                      <button type="button" className="btn btn-sm" onClick={() => setDeleting(s)}>
                        Apagar
                      </button>
                    </span>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {editing ? (
        <ServiceForm
          key={editing === 'new' ? 'new' : editing.id}
          service={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
        />
      ) : null}

      {deleting ? (
        <DeleteRecordDialog
          what={`o serviço ${deleting.name}`}
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
