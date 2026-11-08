import { useState } from 'react';
import { errorMessage, statusOf } from '@/shared/api/errorMessage';
import { maskPhone } from '@/shared/text/phone';
import ConfirmDialog from '@/shared/ui/ConfirmDialog';
import { useSaveUnit } from '../../api/units.queries';
import {
  BR_TIMEZONES,
  emptyUnitForm,
  unitInput,
  unitToForm,
  validateUnit,
  type UnitErrors,
  type UnitForm as Form,
} from '../../model/unit.rules';
import type { UnitRecord } from '../../model/unit.types';

interface UnitFormProps {
  unit: UnitRecord | null;
  /** `tenant:configure`; without it the form is read-only. */
  canWrite: boolean;
  onClose: () => void;
  onCreated: (unit: UnitRecord) => void;
}

const OTHER = '__other__';

/** Create or edit a unit's data (name, address, phone, timezone, online booking). */
export default function UnitForm({ unit, canWrite, onClose, onCreated }: UnitFormProps) {
  const [initial] = useState<Form>(() => (unit ? unitToForm(unit) : emptyUnitForm()));
  const [form, setForm] = useState<Form>(initial);
  const [errors, setErrors] = useState<UnitErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [planLimit, setPlanLimit] = useState(false);
  const [confirmingTimezone, setConfirmingTimezone] = useState(false);
  const [confirmingClose, setConfirmingClose] = useState(false);
  const [otherZone, setOtherZone] = useState(() => !BR_TIMEZONES.some((z) => z.value === initial.timezone));
  const save = useSaveUnit();
  const dirty = JSON.stringify(form) !== JSON.stringify(initial);

  function set<K extends keyof Form>(key: K, value: Form[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function close() {
    if (dirty && !save.isPending && canWrite) setConfirmingClose(true);
    else onClose();
  }

  async function persist() {
    setConfirmingTimezone(false);
    setSubmitError(null);
    setPlanLimit(false);
    try {
      const saved = await save.mutateAsync({ id: unit?.id ?? null, input: unitInput(form) });
      if (unit) onClose();
      else onCreated(saved);
    } catch (err) {
      setPlanLimit(statusOf(err) === 402);
      setSubmitError(errorMessage(err));
    }
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const found = validateUnit(form);
    setErrors(found);
    if (Object.keys(found).length) return;
    // Moving a unit to another timezone shifts the local time of what is booked.
    if (unit && form.timezone.trim() !== unit.timezone) setConfirmingTimezone(true);
    else void persist();
  }

  return (
    <form className="panel form-panel" onSubmit={submit} noValidate>
      <div className="panel-head">
        <div className="panel-title">{unit ? `Unidade · ${unit.name}` : 'Nova unidade'}</div>
        <button type="button" className="btn-quiet" onClick={close}>
          Fechar
        </button>
      </div>

      {submitError ? (
        <div className="form-alert" role="alert">
          {submitError}
          {planLimit ? ' Fale com o suporte do Navalha para mudar de plano.' : null}
        </div>
      ) : null}

      <fieldset className="form-grid plain-fieldset" disabled={!canWrite}>
        <label className="field">
          <span className="field-label">Nome</span>
          <input
            className={`input${errors.name ? ' is-invalid' : ''}`}
            value={form.name}
            maxLength={120}
            autoFocus={!unit}
            onChange={(e) => set('name', e.target.value)}
          />
          {errors.name ? <span className="field-error">{errors.name}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Telefone (opcional)</span>
          <input
            className={`input${errors.phone ? ' is-invalid' : ''}`}
            value={form.phone}
            inputMode="tel"
            placeholder="(11) 3333-4444"
            onChange={(e) => set('phone', maskPhone(e.target.value))}
          />
          {errors.phone ? <span className="field-error">{errors.phone}</span> : null}
        </label>
        <label className="field field-full">
          <span className="field-label">Endereço (opcional)</span>
          <input
            className={`input${errors.address ? ' is-invalid' : ''}`}
            value={form.address}
            maxLength={300}
            onChange={(e) => set('address', e.target.value)}
          />
          {errors.address ? <span className="field-error">{errors.address}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Fuso horário</span>
          <select
            className="select"
            value={otherZone ? OTHER : form.timezone}
            onChange={(e) => {
              const value = e.target.value;
              setOtherZone(value === OTHER);
              if (value !== OTHER) set('timezone', value);
            }}
          >
            {BR_TIMEZONES.map((z) => (
              <option key={z.value} value={z.value}>
                {z.label}
              </option>
            ))}
            <option value={OTHER}>Outro…</option>
          </select>
        </label>
        {otherZone ? (
          <label className="field">
            <span className="field-label">Fuso (padrão IANA)</span>
            <input
              className={`input${errors.timezone ? ' is-invalid' : ''}`}
              value={form.timezone}
              placeholder="America/Sao_Paulo"
              onChange={(e) => set('timezone', e.target.value)}
            />
            {errors.timezone ? <span className="field-error">{errors.timezone}</span> : null}
          </label>
        ) : null}
        <label className="field">
          <span className="field-label">Agendamento online</span>
          <span className="check-field">
            <input
              type="checkbox"
              checked={form.onlineBooking}
              onChange={(e) => set('onlineBooking', e.target.checked)}
            />
            Aceita agendamento pela IA e pelo link
          </span>
        </label>
        <label className="field">
          <span className="field-label">Status</span>
          <span className="check-field">
            <input type="checkbox" checked={form.active} onChange={(e) => set('active', e.target.checked)} />
            Ativa
          </span>
        </label>
      </fieldset>

      {canWrite ? (
        <div className="panel-foot">
          <button type="button" className="btn" onClick={close} disabled={save.isPending}>
            Cancelar
          </button>
          <button type="submit" className="btn-primary" disabled={save.isPending || (unit !== null && !dirty)}>
            {save.isPending ? 'Salvando…' : unit ? 'Salvar alterações' : 'Cadastrar unidade'}
          </button>
        </div>
      ) : null}

      {confirmingTimezone ? (
        <ConfirmDialog
          title="Mudar o fuso horário?"
          confirmLabel="Mudar fuso"
          onConfirm={() => void persist()}
          onCancel={() => setConfirmingTimezone(false)}
        >
          <p>Os horários locais dos agendamentos futuros desta unidade vão mudar.</p>
        </ConfirmDialog>
      ) : null}
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
