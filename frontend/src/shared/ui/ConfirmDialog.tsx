import { useEffect } from 'react';

interface ConfirmDialogProps {
  title: string;
  children: React.ReactNode;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  /** The action is running: buttons wait. */
  busy?: boolean;
  /** Why the last attempt failed, shown above the buttons. */
  error?: string | null;
  /** Extra action next to the main one (e.g. "Inativar" when deleting is refused). */
  secondary?: { label: string; onClick: () => void };
  danger?: boolean;
}

/** A yes/no question before a destructive or irreversible action. */
export default function ConfirmDialog({
  title,
  children,
  confirmLabel,
  onConfirm,
  onCancel,
  busy = false,
  error = null,
  secondary,
  danger = false,
}: ConfirmDialogProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !busy) onCancel();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [busy, onCancel]);

  return (
    <div className="modal-backdrop" role="presentation" onClick={busy ? undefined : onCancel}>
      <div
        className="modal modal-sm"
        role="alertdialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <span className="modal-title">{title}</span>
        </div>
        <div className="confirm-body">
          {children}
          {error ? (
            <div className="form-alert" role="alert">
              {error}
            </div>
          ) : null}
        </div>
        <div className="modal-foot">
          <div className="modal-foot-actions">
            <button type="button" className="btn" onClick={onCancel} disabled={busy}>
              Cancelar
            </button>
            {secondary ? (
              <button type="button" className="btn" onClick={secondary.onClick} disabled={busy}>
                {secondary.label}
              </button>
            ) : null}
            <button
              type="button"
              className={danger ? 'btn-danger' : 'btn-primary'}
              onClick={onConfirm}
              disabled={busy}
            >
              {busy ? 'Aguarde…' : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
