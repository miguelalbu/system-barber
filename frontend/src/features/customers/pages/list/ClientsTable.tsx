import { useState } from 'react';
import type { UseQueryResult } from '@tanstack/react-query';
import { errorMessage } from '@/shared/api/errorMessage';
import { formatPhone } from '@/shared/text/phone';
import { Badge } from '@/shared/ui/Badge';
import DeleteRecordDialog from '@/shared/ui/DeleteRecordDialog';
import TableState from '@/shared/ui/TableState';
import { useDeleteClient, useSetClientActive } from '../../api/customers.queries';
import { formatBirthday, pageCount } from '../../model/customer.rules';
import type { Client, ClientPage } from '../../model/customers.types';

const COLUMNS = ['Cliente', 'Telefone', 'E-mail', 'Aniversário', 'Status', ''];

interface ClientsTableProps {
  query: UseQueryResult<ClientPage>;
  searching: boolean;
  page: number;
  canWrite: boolean;
  /** A barber sees only the clients they served. */
  ownOnly: boolean;
  onEdit: (client: Client) => void;
  onCreate: () => void;
  onPage: (page: number) => void;
}

function emptyMessage(searching: boolean, ownOnly: boolean): string {
  if (searching) return 'Nenhum cliente encontrado para essa busca.';
  if (ownOnly) return 'Seus clientes aparecem aqui depois do primeiro atendimento.';
  return 'Nenhum cliente cadastrado ainda.';
}

export default function ClientsTable({
  query,
  searching,
  page,
  canWrite,
  ownOnly,
  onEdit,
  onCreate,
  onPage,
}: ClientsTableProps) {
  const setActive = useSetClientActive();
  const remove = useDeleteClient();
  const [deleting, setDeleting] = useState<Client | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);
  const pages = pageCount(query.data?.total ?? 0);

  async function toggleActive(client: Client) {
    setRowError(null);
    try {
      await setActive.mutateAsync({ id: client.id, active: !client.active });
    } catch (e) {
      setRowError(errorMessage(e));
    }
  }

  return (
    <>
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
          {query.isPending ? <TableState columns={COLUMNS.length} state="loading" /> : null}
          {query.isError ? (
            <TableState
              columns={COLUMNS.length}
              state="error"
              message={errorMessage(query.error)}
              action={{ label: 'Tentar de novo', onClick: () => void query.refetch() }}
            />
          ) : null}
          {query.isSuccess && query.data.items.length === 0 ? (
            <TableState
              columns={COLUMNS.length}
              state="empty"
              message={emptyMessage(searching, ownOnly)}
              action={
                canWrite && !searching ? { label: 'Cadastrar cliente', onClick: onCreate } : undefined
              }
            />
          ) : null}
          {query.data?.items.map((c) => (
            <tr key={c.id}>
              <td>
                <div className="staff-name">{c.name}</div>
                {c.notes ? <div className="staff-email truncate">{c.notes}</div> : null}
              </td>
              <td className="tnum">{formatPhone(c.phone)}</td>
              <td className="cell-muted">{c.email ?? '—'}</td>
              <td className="cell-muted tnum">{formatBirthday(c.birth_date)}</td>
              <td>
                <Badge kind={c.active ? 'ativo' : 'concluido'}>{c.active ? 'Ativo' : 'Inativo'}</Badge>
              </td>
              <td className="col-right">
                {canWrite ? (
                  <span className="row-actions">
                    <button type="button" className="btn btn-sm" onClick={() => onEdit(c)}>
                      Editar
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm"
                      disabled={setActive.isPending}
                      onClick={() => void toggleActive(c)}
                    >
                      {c.active ? 'Inativar' : 'Reativar'}
                    </button>
                    <button type="button" className="btn btn-sm" onClick={() => setDeleting(c)}>
                      Apagar
                    </button>
                  </span>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {pages > 1 ? (
        <div className="pager">
          <span>
            Página {page} de {pages}
          </span>
          <button type="button" className="btn btn-sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>
            Anterior
          </button>
          <button
            type="button"
            className="btn btn-sm"
            disabled={page >= pages}
            onClick={() => onPage(page + 1)}
          >
            Próxima
          </button>
        </div>
      ) : null}

      {deleting ? (
        <DeleteRecordDialog
          what={`o cliente ${deleting.name}`}
          onDelete={() => remove.mutateAsync(deleting.id)}
          onInactivate={
            deleting.active ? () => setActive.mutateAsync({ id: deleting.id, active: false }) : undefined
          }
          onClose={() => setDeleting(null)}
        />
      ) : null}
    </>
  );
}
