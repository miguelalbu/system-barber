import { useSearchParams } from 'react-router-dom';
import { useState } from 'react';
import { useAuth, useMe } from '@/features/auth';
import { errorMessage } from '@/shared/api/errorMessage';
import { formatPhone } from '@/shared/text/phone';
import { Badge } from '@/shared/ui/Badge';
import DeleteRecordDialog from '@/shared/ui/DeleteRecordDialog';
import TableState from '@/shared/ui/TableState';
import { useDeleteUnit, useSaveUnit, useUnitRecords } from '../../api/units.queries';
import { configurableUnitIds, showTimezoneColumn } from '../../model/unit.rules';
import type { UnitRecord } from '../../model/unit.types';
import UnitExceptionsSection from './UnitExceptionsSection';
import UnitForm from './UnitForm';
import UnitHoursSection from './UnitHoursSection';

/**
 * Units of the shop. Opening one (`?unidade=<id>`, or `novo`) shows its form
 * and, for an existing unit, its opening hours and special dates.
 */
export default function UnitsPage() {
  const { can } = useAuth();
  const me = useMe();
  const canWrite = can('tenant:configure') !== null;
  const [params, setParams] = useSearchParams();
  const openId = params.get('unidade');

  const units = useUnitRecords();
  const save = useSaveUnit();
  const remove = useDeleteUnit();
  const [deleting, setDeleting] = useState<UnitRecord | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  const list = units.data ?? [];
  const configurable = configurableUnitIds(list, can('unit:configure'), me);
  const withTimezone = showTimezoneColumn(list);
  const columns = ['Unidade', 'Endereço', 'Telefone', ...(withTimezone ? ['Fuso'] : []), 'Agendamento online', 'Status', ''];
  const opened = openId && openId !== 'novo' ? list.find((u) => u.id === openId) ?? null : null;

  function openUnit(id: string | null) {
    const next = new URLSearchParams(params);
    if (id) next.set('unidade', id);
    else next.delete('unidade');
    setParams(next, { replace: true });
  }

  async function toggleActive(unit: UnitRecord) {
    setRowError(null);
    try {
      await save.mutateAsync({ id: unit.id, input: { active: !unit.active } });
    } catch (e) {
      setRowError(errorMessage(e));
    }
  }

  return (
    <>
      <section className="panel">
        <div className="toolbar">
          <div className="panel-title">Unidades</div>
          <div className="toolbar-end">
            {units.data ? <span className="record-count">{list.length} registros</span> : null}
            {canWrite ? (
              <button type="button" className="btn-primary" onClick={() => openUnit('novo')}>
                Nova unidade
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
              {columns.map((c, i) => (
                <th key={c || 'actions'} className={i === columns.length - 1 ? 'col-right' : undefined}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {units.isPending ? <TableState columns={columns.length} state="loading" /> : null}
            {units.isError ? (
              <TableState
                columns={columns.length}
                state="error"
                message={errorMessage(units.error)}
                action={{ label: 'Tentar de novo', onClick: () => void units.refetch() }}
              />
            ) : null}
            {units.isSuccess && list.length === 0 ? (
              <TableState columns={columns.length} state="empty" message="Nenhuma unidade visível para você." />
            ) : null}
            {list.map((u) => (
              <tr key={u.id} className={u.id === openId ? 'is-selected' : undefined}>
                <td className="staff-name">{u.name}</td>
                <td className="cell-muted">{u.address ?? '—'}</td>
                <td className="cell-muted tnum">{u.phone ? formatPhone(u.phone) : '—'}</td>
                {withTimezone ? <td className="cell-muted">{u.timezone}</td> : null}
                <td className="cell-muted">{u.online_booking ? 'Sim' : 'Não'}</td>
                <td>
                  <Badge kind={u.active ? 'ativo' : 'concluido'}>{u.active ? 'Ativa' : 'Inativa'}</Badge>
                </td>
                <td className="col-right">
                  <span className="row-actions">
                    <button type="button" className="btn btn-sm" onClick={() => openUnit(u.id)}>
                      {canWrite || configurable.includes(u.id) ? 'Editar' : 'Ver'}
                    </button>
                    {canWrite ? (
                      <>
                        <button
                          type="button"
                          className="btn btn-sm"
                          disabled={save.isPending}
                          onClick={() => void toggleActive(u)}
                        >
                          {u.active ? 'Inativar' : 'Reativar'}
                        </button>
                        <button type="button" className="btn btn-sm" onClick={() => setDeleting(u)}>
                          Apagar
                        </button>
                      </>
                    ) : null}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {openId === 'novo' && canWrite ? (
        <UnitForm
          key="novo"
          unit={null}
          canWrite
          onClose={() => openUnit(null)}
          onCreated={(created) => openUnit(created.id)}
        />
      ) : null}
      {opened ? (
        <>
          <UnitForm
            key={opened.id}
            unit={opened}
            canWrite={canWrite}
            onClose={() => openUnit(null)}
            onCreated={() => undefined}
          />
          <UnitHoursSection key={`h-${opened.id}`} unitId={opened.id} canEdit={configurable.includes(opened.id)} />
          <UnitExceptionsSection
            key={`x-${opened.id}`}
            unit={opened}
            otherConfigurable={list.filter((u) => u.id !== opened.id && u.active && configurable.includes(u.id))}
            canEdit={configurable.includes(opened.id)}
          />
        </>
      ) : null}

      {deleting ? (
        <DeleteRecordDialog
          what={`a unidade ${deleting.name}`}
          onDelete={async () => {
            await remove.mutateAsync(deleting.id);
            if (openId === deleting.id) openUnit(null);
          }}
          onInactivate={
            deleting.active
              ? () => save.mutateAsync({ id: deleting.id, input: { active: false } })
              : undefined
          }
          onClose={() => setDeleting(null)}
        />
      ) : null}
    </>
  );
}
