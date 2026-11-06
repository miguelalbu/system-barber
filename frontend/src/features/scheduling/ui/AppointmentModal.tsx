import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '@/shared/ui/Icon';
import { barbers, serviceOptions } from '../api/scheduling.mock';
import type { AppointmentOrigin } from '../model/scheduling.types';

interface AppointmentModalProps {
  kind: AppointmentOrigin;
  onClose: () => void;
}

export function AppointmentModal({ kind, onClose }: AppointmentModalProps) {
  const navigate = useNavigate();
  const isAi = kind === 'ia';

  const [client, setClient] = useState(isAi ? 'Rafael Lima' : '');
  const [date, setDate] = useState('17/08/2026');
  const [time, setTime] = useState('10:30');
  const [note, setNote] = useState(isAi ? 'Cliente pediu máquina 2 nas laterais' : '');

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={isAi ? 'Agendamento de Rafael Lima' : 'Novo agendamento'}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <div className="modal-title-row">
            <span className="modal-title">
              {isAi ? 'Agendamento · Rafael Lima' : 'Novo agendamento'}
            </span>
            {isAi ? <span className="modal-origin">ORIGEM: IA · WHATSAPP</span> : null}
          </div>
          <button type="button" className="btn-quiet" onClick={onClose} aria-label="Fechar">
            <Icon name="close" />
          </button>
        </div>

        <div className="modal-body">
          <label className="field field-full">
            <span className="field-label">Cliente</span>
            <input
              className="input"
              value={client}
              placeholder={isAi ? undefined : 'Buscar por nome ou telefone'}
              onChange={(e) => setClient(e.target.value)}
            />
            <span className="field-hint">
              {isAi
                ? 'Cliente identificado pelo número +55 11 98812-4417'
                : 'Se não existir, o cadastro é criado ao salvar'}
            </span>
          </label>

          <label className="field">
            <span className="field-label">Serviço</span>
            <select className="select" defaultValue={serviceOptions[0]}>
              {serviceOptions.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field-label">Barbeiro</span>
            <select className="select" defaultValue={barbers[0].name}>
              {barbers.map((b) => (
                <option key={b.id}>{b.name}</option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field-label">Data</span>
            <input className="input" value={date} onChange={(e) => setDate(e.target.value)} />
          </label>

          <label className="field">
            <span className="field-label">Início</span>
            <input className="input" value={time} onChange={(e) => setTime(e.target.value)} />
          </label>

          <label className="field field-full">
            <span className="field-label">Observações</span>
            <input className="input" value={note} onChange={(e) => setNote(e.target.value)} />
          </label>

          {isAi ? (
            <div className="modal-note">
              <div className="modal-note-title">
                Criado automaticamente pelo atendimento no WhatsApp
              </div>
              <div className="modal-note-body">
                Confirmado pelo cliente às 09:41. Nenhuma ação necessária — os campos ficam editáveis
                como em um agendamento manual.
              </div>
              <button
                type="button"
                className="btn btn-sm"
                style={{ marginTop: 8, height: 27, fontWeight: 500 }}
                onClick={() => {
                  onClose();
                  navigate('/app/conversas');
                }}
              >
                Abrir conversa
              </button>
            </div>
          ) : null}
        </div>

        <div className="modal-foot">
          <span className="modal-foot-note">
            {isAi
              ? 'Confirmado pelo cliente às 09:41'
              : 'Um lembrete é enviado por WhatsApp 2h antes'}
          </span>
          <div className="modal-foot-actions">
            <button type="button" className="btn" onClick={onClose}>
              Cancelar
            </button>
            <button type="button" className="btn-primary" onClick={onClose}>
              {isAi ? 'Salvar alterações' : 'Criar agendamento'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
