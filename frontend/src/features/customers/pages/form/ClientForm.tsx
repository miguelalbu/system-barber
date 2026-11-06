import { useState } from 'react';
import { errorMessage, statusOf } from '@/shared/api/errorMessage';
import { maskPhone } from '@/shared/text/phone';
import ConfirmDialog from '@/shared/ui/ConfirmDialog';
import { useSaveClient } from '../../api/customers.queries';
import {
  clientInput,
  clientToForm,
  emptyClientForm,
  validateClient,
  type ClientErrors,
  type ClientForm as Form,
} from '../../model/customer.rules';
import type { Client } from '../../model/customers.types';

interface ClientFormProps {
  client: Client | null;
  onClose: () => void;
}

export default function ClientForm({ client, onClose }: ClientFormProps) {
  const [initial] = useState<Form>(() => (client ? clientToForm(client) : emptyClientForm()));
  const [form, setForm] = useState<Form>(initial);
  const [errors, setErrors] = useState<ClientErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmingClose, setConfirmingClose] = useState(false);
  const save = useSaveClient();
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
    const found = validateClient(form);
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length) return;
    try {
      await save.mutateAsync({ id: client?.id ?? null, input: clientInput(form) });
      onClose();
    } catch (err) {
      // A phone already in use belongs next to the phone field.
      if (statusOf(err) === 409) setErrors({ phone: errorMessage(err) });
      else setSubmitError(errorMessage(err));
    }
  }

  const today = new Date().toISOString().slice(0, 10);

  return (
    <form className="panel form-panel" onSubmit={(e) => void submit(e)} noValidate>
      <div className="panel-head">
        <div className="panel-title">{client ? `Editar cliente · ${client.name}` : 'Novo cliente'}</div>
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
            maxLength={120}
            onChange={(e) => set('name', e.target.value)}
            autoFocus
          />
          {errors.name ? <span className="field-error">{errors.name}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Telefone (WhatsApp)</span>
          <input
            className={`input${errors.phone ? ' is-invalid' : ''}`}
            value={form.phone}
            inputMode="tel"
            placeholder="(11) 98765-4321"
            onChange={(e) => set('phone', maskPhone(e.target.value))}
          />
          <span className="field-hint">Estrangeiro: comece com + e o código do país</span>
          {errors.phone ? <span className="field-error">{errors.phone}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">E-mail (opcional)</span>
          <input
            className={`input${errors.email ? ' is-invalid' : ''}`}
            type="email"
            value={form.email}
            maxLength={255}
            onChange={(e) => set('email', e.target.value)}
          />
          {errors.email ? <span className="field-error">{errors.email}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Data de nascimento (opcional)</span>
          <input
            className={`input${errors.birthDate ? ' is-invalid' : ''}`}
            type="date"
            max={today}
            value={form.birthDate}
            onChange={(e) => set('birthDate', e.target.value)}
          />
          {errors.birthDate ? <span className="field-error">{errors.birthDate}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Status</span>
          <span className="check-field">
            <input type="checkbox" checked={form.active} onChange={(e) => set('active', e.target.checked)} />
            Ativo
          </span>
        </label>
        <label className="field field-full">
          <span className="field-label">Observações (opcional)</span>
          <textarea
            className={`input${errors.notes ? ' is-invalid' : ''}`}
            value={form.notes}
            maxLength={1000}
            onChange={(e) => set('notes', e.target.value)}
          />
          {errors.notes ? <span className="field-error">{errors.notes}</span> : null}
        </label>
      </div>

      <div className="panel-foot">
        <button type="button" className="btn" onClick={close} disabled={save.isPending}>
          Cancelar
        </button>
        <button type="submit" className="btn-primary" disabled={save.isPending}>
          {save.isPending ? 'Salvando…' : client ? 'Salvar alterações' : 'Cadastrar cliente'}
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
