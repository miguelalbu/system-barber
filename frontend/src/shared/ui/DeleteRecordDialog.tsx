import { useState } from 'react';
import { errorMessage, statusOf } from '@/shared/api/errorMessage';
import ConfirmDialog from './ConfirmDialog';

interface DeleteRecordDialogProps {
  /** What is being deleted, as the person reads it: "o serviço Corte". */
  what: string;
  onDelete: () => Promise<unknown>;
  /** Offered when the API refuses (409: the record has history or is in use). */
  onInactivate?: () => Promise<unknown>;
  onClose: () => void;
}

/**
 * Delete with confirmation. Deleting is final; when the API refuses because the
 * record has history (409), its message is shown and inactivating is offered.
 */
export default function DeleteRecordDialog({
  what,
  onDelete,
  onInactivate,
  onClose,
}: DeleteRecordDialogProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refused, setRefused] = useState(false);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
      setRefused(statusOf(e) === 409);
      setBusy(false);
    }
  }

  return (
    <ConfirmDialog
      title="Apagar cadastro"
      confirmLabel="Apagar"
      danger
      busy={busy}
      error={error}
      onCancel={onClose}
      onConfirm={() => void run(onDelete)}
      secondary={
        refused && onInactivate ? { label: 'Inativar', onClick: () => void run(onInactivate) } : undefined
      }
    >
      <p>
        Apagar {what}? Esta ação não pode ser desfeita. Se quiser só tirar de uso, prefira inativar.
      </p>
    </ConfirmDialog>
  );
}
