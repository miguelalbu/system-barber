import { useState } from 'react';
import { errorMessage, statusOf } from '@/shared/api/errorMessage';
import { DURATION_OPTIONS, formatDuration } from '@/shared/text/duration';
import ConfirmDialog from '@/shared/ui/ConfirmDialog';
import { useSaveService } from '../../api/registry.queries';
import type { Service } from '../../model/registry.types';
import {
  emptyServiceForm,
  serviceInput,
  serviceToForm,
  validateService,
  type ServiceErrors,
  type ServiceForm as Form,
} from '../../model/service.rules';

interface ServiceFormProps {
  service: Service | null;
  onClose: () => void;
}

export default function ServiceForm({ service, onClose }: ServiceFormProps) {
  const [initial] = useState<Form>(() => (service ? serviceToForm(service) : emptyServiceForm()));
  const [form, setForm] = useState<Form>(initial);
  const [errors, setErrors] = useState<ServiceErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmingClose, setConfirmingClose] = useState(false);
  const save = useSaveService();
  const dirty = JSON.stringify(form) !== JSON.stringify(initial);

  function set<K extends keyof Form>(key: K, value: Form[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function close() {
    if (dirty && !save.isPending) setConfirmingClose(true);
    else onClose();
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const found = validateService(form);
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length) return;
    try {
      await save.mutateAsync({ id: service?.id ?? null, input: serviceInput(form) });
      onClose();
    } catch (err) {
      // A repeated name belongs next to the name field.
      if (statusOf(err) === 409) setErrors({ name: errorMessage(err) });
      else setSubmitError(errorMessage(err));
    }
  }

  return (
    <form className="panel form-panel" onSubmit={(e) => void submit(e)} noValidate>
      <div className="panel-head">
        <div className="panel-title">{service ? `Editar serviço · ${service.name}` : 'Novo serviço'}</div>
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
          <span className="field-label">Nome</span>
          <input
            className={`input${errors.name ? ' is-invalid' : ''}`}
            value={form.name}
            maxLength={80}
            onChange={(e) => set('name', e.target.value)}
            autoFocus
          />
          {errors.name ? <span className="field-error">{errors.name}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Duração</span>
          <select
            className="select"
            value={form.duration}
            onChange={(e) => set('duration', Number(e.target.value))}
          >
            {DURATION_OPTIONS.map((m) => (
              <option key={m} value={m}>
                {formatDuration(m)}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Preço (R$)</span>
          <input
            className={`input${errors.price ? ' is-invalid' : ''}`}
            value={form.price}
            inputMode="decimal"
            placeholder="45,00"
            onChange={(e) => set('price', e.target.value)}
          />
          {errors.price ? <span className="field-error">{errors.price}</span> : null}
        </label>
        <label className="field field-full">
          <span className="field-label">Descrição (opcional)</span>
          <textarea
            className={`input${errors.description ? ' is-invalid' : ''}`}
            value={form.description}
            maxLength={500}
            onChange={(e) => set('description', e.target.value)}
          />
          {errors.description ? <span className="field-error">{errors.description}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Status</span>
          <span className="check-field">
            <input type="checkbox" checked={form.active} onChange={(e) => set('active', e.target.checked)} />
            Ativo
          </span>
        </label>
      </div>

      <div className="panel-foot">
        <button type="button" className="btn" onClick={close} disabled={save.isPending}>
          Cancelar
        </button>
        <button type="submit" className="btn-primary" disabled={save.isPending}>
          {save.isPending ? 'Salvando…' : service ? 'Salvar alterações' : 'Cadastrar serviço'}
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
