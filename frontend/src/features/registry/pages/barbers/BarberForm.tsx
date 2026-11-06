import { useState } from 'react';
import { useAuth } from '@/features/auth';
import { errorMessage } from '@/shared/api/errorMessage';
import ConfirmDialog from '@/shared/ui/ConfirmDialog';
import { useMembers, useSaveBarber } from '../../api/registry.queries';
import {
  barberInput,
  barberToForm,
  emptyBarberForm,
  linkableMembers,
  suggestedInitials,
  validateBarber,
  type BarberErrors,
  type BarberForm as Form,
} from '../../model/barber.rules';
import type { Barber, Service, Unit } from '../../model/registry.types';

interface BarberFormProps {
  barber: Barber | null;
  units: Unit[];
  services: Service[];
  onClose: () => void;
}

/** Create or edit a barber, with the services they perform and an optional panel login. */
export default function BarberForm({ barber, units, services, onClose }: BarberFormProps) {
  const { can } = useAuth();
  const [initial] = useState<Form>(() =>
    barber ? barberToForm(barber, services) : emptyBarberForm(units[0]?.id ?? ''),
  );
  const [form, setForm] = useState<Form>(initial);
  const [errors, setErrors] = useState<BarberErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmingClose, setConfirmingClose] = useState(false);

  const members = useMembers(can('team:read') !== null);
  const save = useSaveBarber();
  const dirty = JSON.stringify(form) !== JSON.stringify(initial);
  const linked = members.data?.find((m) => m.id === barber?.user_id);
  // A `barber` login always needs its barber: the API refuses to unlink it.
  const linkLocked = linked?.role === 'barber';

  function set<K extends keyof Form>(key: K, value: Form[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function toggleService(id: string) {
    set(
      'serviceIds',
      form.serviceIds.includes(id) ? form.serviceIds.filter((s) => s !== id) : [...form.serviceIds, id],
    );
  }

  function close() {
    if (dirty && !save.isPending) setConfirmingClose(true);
    else onClose();
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const found = validateBarber(form);
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length) return;
    try {
      await save.mutateAsync({ id: barber?.id ?? null, input: barberInput(form), serviceIds: form.serviceIds });
      onClose();
    } catch (err) {
      setSubmitError(errorMessage(err));
    }
  }

  return (
    <form className="panel form-panel" onSubmit={(e) => void submit(e)} noValidate>
      <div className="panel-head">
        <div className="panel-title">{barber ? `Editar barbeiro · ${barber.name}` : 'Novo barbeiro'}</div>
        <button type="button" className="btn-quiet" onClick={close}>
          Fechar
        </button>
      </div>

      {submitError ? (
        <div className="form-alert" role="alert">
          {submitError}
        </div>
      ) : null}

      <div className="form-grid">
        <label className="field">
          <span className="field-label">Nome completo</span>
          <input
            className={`input${errors.name ? ' is-invalid' : ''}`}
            value={form.name}
            maxLength={120}
            onChange={(e) => set('name', e.target.value)}
            autoFocus
          />
          {errors.name ? <span className="field-error">{errors.name}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Iniciais</span>
          <input
            className={`input${errors.initials ? ' is-invalid' : ''}`}
            value={form.initials}
            placeholder={suggestedInitials(form.name)}
            maxLength={4}
            onChange={(e) => set('initials', e.target.value.toUpperCase())}
          />
          <span className="field-hint">Vazio: usa as iniciais do nome</span>
          {errors.initials ? <span className="field-error">{errors.initials}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Unidade</span>
          <select
            className={`select${errors.unitId ? ' is-invalid' : ''}`}
            value={form.unitId}
            onChange={(e) => set('unitId', e.target.value)}
          >
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
          {errors.unitId ? <span className="field-error">{errors.unitId}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Comissão padrão (%)</span>
          <input
            className={`input${errors.commission ? ' is-invalid' : ''}`}
            value={form.commission}
            inputMode="decimal"
            onChange={(e) => set('commission', e.target.value)}
          />
          {errors.commission ? <span className="field-error">{errors.commission}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Acesso ao painel</span>
          <select
            className="select"
            value={form.userId}
            disabled={linkLocked || members.isPending}
            onChange={(e) => set('userId', e.target.value)}
          >
            <option value="">Sem acesso</option>
            {linkableMembers(members.data ?? [], barber).map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} · {m.email}
              </option>
            ))}
          </select>
          <span className="field-hint">
            {linkLocked
              ? 'Login com cargo de barbeiro: o vínculo é fixo'
              : 'Liga a um usuário que já existe. Novos acessos: convite em Equipe'}
          </span>
        </label>
        <label className="field">
          <span className="field-label">Status</span>
          <span className="check-field">
            <input type="checkbox" checked={form.active} onChange={(e) => set('active', e.target.checked)} />
            Ativo
          </span>
        </label>

        <div className="field-full">
          <div className="field-label" style={{ marginBottom: 7 }}>
            Serviços habilitados
          </div>
          {services.length ? (
            <div className="chip-row">
              {services.map((s) => (
                <button
                  type="button"
                  key={s.id}
                  aria-pressed={form.serviceIds.includes(s.id)}
                  className={`chip${form.serviceIds.includes(s.id) ? ' is-on' : ''}`}
                  onClick={() => toggleService(s.id)}
                >
                  {s.name}
                  {s.active ? '' : ' (inativo)'}
                </button>
              ))}
            </div>
          ) : (
            <span className="field-hint">Nenhum serviço cadastrado. Cadastre na aba Serviços.</span>
          )}
        </div>
      </div>

      <div className="panel-foot">
        <button type="button" className="btn" onClick={close} disabled={save.isPending}>
          Cancelar
        </button>
        <button type="submit" className="btn-primary" disabled={save.isPending}>
          {save.isPending ? 'Salvando…' : barber ? 'Salvar alterações' : 'Cadastrar barbeiro'}
        </button>
      </div>

      {confirmingClose ? (
        <ConfirmDialog
          title="Descartar alterações?"
          confirmLabel="Descartar"
          onConfirm={onClose}
          onCancel={() => setConfirmingClose(false)}
        >
          <p>As alterações deste formulário ainda não foram salvas.</p>
        </ConfirmDialog>
      ) : null}
    </form>
  );
}
