import { useState } from 'react';
import { useMe } from '@/features/auth';
import { errorMessage } from '@/shared/api/errorMessage';
import { maskPhone } from '@/shared/text/phone';
import { useRenameShop, useSaveShopSettings } from '../../api/settings.queries';
import {
  ABOUT_MAX,
  changedFields,
  shopSettingsInput,
  shopToForm,
  validateShop,
  type ShopErrors,
  type ShopForm,
} from '../../model/settings.rules';
import type { ShopSettings } from '../../model/settings.types';

/** "Barbearia": name, public contact, the "about" text and the barber's view of contacts. */
export default function ShopSection({ settings }: { settings: ShopSettings }) {
  const me = useMe();
  const [initial, setInitial] = useState<ShopForm>(() => shopToForm(me.tenant.name, settings));
  const [form, setForm] = useState<ShopForm>(initial);
  const [errors, setErrors] = useState<ShopErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const rename = useRenameShop();
  const save = useSaveShopSettings();
  const dirty = JSON.stringify(form) !== JSON.stringify(initial);
  const busy = rename.isPending || save.isPending;

  function set<K extends keyof ShopForm>(key: K, value: ShopForm[K]) {
    setForm((f) => ({ ...f, [key]: value }));
    setSavedAt(null);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const found = validateShop(form);
    setErrors(found);
    setSubmitError(null);
    if (Object.keys(found).length) return;
    try {
      if (form.name.trim() !== initial.name) await rename.mutateAsync(form.name.trim());
      const changes = changedFields(shopSettingsInput(initial), shopSettingsInput(form));
      const saved = Object.keys(changes).length ? await save.mutateAsync(changes) : settings;
      const next = shopToForm(form.name.trim(), saved);
      setInitial(next);
      setForm(next);
      setSavedAt(Date.now());
    } catch (err) {
      setSubmitError(errorMessage(err));
    }
  }

  return (
    <form className="panel" onSubmit={(e) => void submit(e)} noValidate>
      <div className="panel-head">
        <div className="panel-title">Barbearia</div>
        {savedAt ? <span className="cell-muted" role="status">Salvo</span> : null}
      </div>
      {submitError ? (
        <div className="form-alert" role="alert">
          {submitError}
        </div>
      ) : null}
      <div className="form-grid">
        <label className="field">
          <span className="field-label">Nome da barbearia</span>
          <input
            className={`input${errors.name ? ' is-invalid' : ''}`}
            value={form.name}
            maxLength={120}
            onChange={(e) => set('name', e.target.value)}
          />
          {errors.name ? <span className="field-error">{errors.name}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Telefone de contato</span>
          <input
            className={`input${errors.contactPhone ? ' is-invalid' : ''}`}
            value={form.contactPhone}
            inputMode="tel"
            placeholder="(11) 98765-4321"
            onChange={(e) => set('contactPhone', maskPhone(e.target.value))}
          />
          {errors.contactPhone ? <span className="field-error">{errors.contactPhone}</span> : null}
        </label>
        <label className="field">
          <span className="field-label">Instagram</span>
          <input
            className={`input${errors.instagram ? ' is-invalid' : ''}`}
            value={form.instagram}
            placeholder="@suabarbearia"
            onChange={(e) => set('instagram', e.target.value)}
          />
          <span className="field-hint">Pode colar o @ ou o link do perfil.</span>
          {errors.instagram ? <span className="field-error">{errors.instagram}</span> : null}
        </label>
        <label className="field field-full">
          <span className="field-label">Sobre a barbearia</span>
          <textarea
            className={`input textarea${errors.about ? ' is-invalid' : ''}`}
            value={form.about}
            rows={4}
            maxLength={ABOUT_MAX}
            onChange={(e) => set('about', e.target.value)}
          />
          <span className="field-hint">
            Aparece na página de agendamento e o atendimento automático usa para responder clientes.
            {' '}
            {form.about.length}/{ABOUT_MAX}
          </span>
          {errors.about ? <span className="field-error">{errors.about}</span> : null}
        </label>
        <label className="field field-full">
          <span className="check-field">
            <input
              type="checkbox"
              checked={form.barberSeesClientContact}
              onChange={(e) => set('barberSeesClientContact', e.target.checked)}
            />
            Barbeiro vê telefone e e-mail do cliente
          </span>
          <span className="field-hint">
            Desligado, o barbeiro vê nome e histórico, mas o contato aparece mascarado.
          </span>
        </label>
      </div>
      <div className="panel-foot">
        <button type="button" className="btn" disabled={!dirty || busy} onClick={() => setForm(initial)}>
          Desfazer
        </button>
        <button type="submit" className="btn-primary" disabled={!dirty || busy}>
          {busy ? 'Salvando…' : 'Salvar'}
        </button>
      </div>
    </form>
  );
}
