import { useState } from 'react';
import { errorMessage } from '@/shared/api/errorMessage';
import { useSaveShopSettings } from '../../api/settings.queries';
import {
  MIN_ADVANCE_OPTIONS,
  POLICY_RANGES,
  changedFields,
  policiesOf,
  validatePolicies,
  type PolicyForm,
} from '../../model/settings.rules';
import type { ShopSettings } from '../../model/settings.types';

type NumericKey = keyof typeof POLICY_RANGES;

const NUMERIC_FIELDS: { key: NumericKey; label: string; unit: string; help: (v: number) => string }[] = [
  {
    key: 'max_advance_days',
    label: 'Agendar até',
    unit: 'dias à frente',
    help: (v) => `O cliente vê horários dos próximos ${v} dias.`,
  },
  {
    key: 'confirmation_deadline_hours',
    label: 'Prazo para confirmar',
    unit: 'horas antes',
    help: (v) =>
      `Se o cliente não confirmar até ${v} h antes, o horário fica marcado como "não confirmado" para a recepção decidir. Nada é cancelado sozinho.`,
  },
  {
    key: 'client_change_min_hours',
    label: 'Cliente cancela ou remarca sozinho até',
    unit: 'horas antes',
    help: (v) =>
      v === 0
        ? 'O cliente pode cancelar ou remarcar até a hora do atendimento.'
        : `Depois disso, o pedido vai para a recepção. Com ${v} h, quem marcou às 15:00 muda sozinho até as ${String(15 - Math.min(v, 15)).padStart(2, '0')}:00.`,
  },
  {
    key: 'late_tolerance_minutes',
    label: 'Tolerância de atraso',
    unit: 'minutos',
    help: (v) => `A falta só pode ser marcada ${v} min depois do horário.`,
  },
  {
    key: 'max_future_appointments_per_client',
    label: 'Agendamentos futuros por cliente',
    unit: 'no máximo',
    help: (v) => `Pelo WhatsApp e pelo link, cada cliente tem até ${v} horários marcados. A recepção no painel não tem esse limite.`,
  },
];

/** "Agendamento": the booking policies of the client channels (AI and link). */
export default function BookingPoliciesSection({ settings }: { settings: ShopSettings }) {
  const [initial, setInitial] = useState<PolicyForm>(() => policiesOf(settings));
  const [form, setForm] = useState<PolicyForm>(initial);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const save = useSaveShopSettings();
  const errors = validatePolicies(form);
  const dirty = JSON.stringify(form) !== JSON.stringify(initial);

  function set(key: keyof PolicyForm, value: number) {
    setForm((f) => ({ ...f, [key]: value }));
    setSavedAt(null);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    if (Object.keys(errors).length) return;
    try {
      const saved = await save.mutateAsync(changedFields(initial, form));
      setInitial(policiesOf(saved));
      setForm(policiesOf(saved));
      setSavedAt(Date.now());
    } catch (err) {
      setSubmitError(errorMessage(err));
    }
  }

  return (
    <form className="panel" onSubmit={(e) => void submit(e)} noValidate>
      <div className="panel-head">
        <div className="panel-title">Agendamento</div>
        {savedAt ? <span className="cell-muted" role="status">Salvo</span> : null}
      </div>
      {submitError ? (
        <div className="form-alert" role="alert">
          {submitError}
        </div>
      ) : null}
      <p className="field-hint section-intro">
        Valem para o atendimento automático no WhatsApp e para o link de agendamento. A equipe no
        painel não tem esses limites. Os horários são oferecidos de 15 em 15 minutos.
      </p>
      <div className="form-grid">
        <label className="field">
          <span className="field-label">Antecedência mínima</span>
          <select
            className="select"
            value={form.min_advance_minutes}
            onChange={(e) => set('min_advance_minutes', Number(e.target.value))}
          >
            {MIN_ADVANCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <span className="field-hint">O cliente não marca para daqui a menos que isso.</span>
        </label>
        {NUMERIC_FIELDS.map(({ key, label, unit, help }) => {
          const [min, max] = POLICY_RANGES[key];
          return (
            <label className="field" key={key}>
              <span className="field-label">{label}</span>
              <span className="input-with-unit">
                <input
                  type="number"
                  className={`input${errors[key] ? ' is-invalid' : ''}`}
                  min={min}
                  max={max}
                  value={Number.isNaN(form[key]) ? '' : form[key]}
                  onChange={(e) => set(key, e.target.value === '' ? Number.NaN : Number(e.target.value))}
                />
                <span className="cell-muted">{unit}</span>
              </span>
              {errors[key] ? (
                <span className="field-error">{errors[key]}</span>
              ) : (
                <span className="field-hint">{help(form[key])}</span>
              )}
            </label>
          );
        })}
      </div>
      <div className="panel-foot">
        <button type="button" className="btn" disabled={!dirty || save.isPending} onClick={() => setForm(initial)}>
          Desfazer
        </button>
        <button type="submit" className="btn-primary" disabled={!dirty || save.isPending || Object.keys(errors).length > 0}>
          {save.isPending ? 'Salvando…' : 'Salvar'}
        </button>
      </div>
    </form>
  );
}
