import { useState } from 'react';
import { errorMessage } from '@/shared/api/errorMessage';
import ConfirmDialog from '@/shared/ui/ConfirmDialog';
import { useCreateHolidayClosures, useHolidays } from '../../api/units.queries';
import { holidayAlreadyClosed, holidayClosures } from '../../model/unit.rules';

interface HolidaysDialogProps {
  unitId: string;
  year: number;
  today: string;
  onClose: () => void;
}

/**
 * National holidays of a year with checkboxes. Nothing is ticked by default
 * (many shops open on holidays); confirming creates one closure per ticked day.
 */
export default function HolidaysDialog({ unitId, year, today, onClose }: HolidaysDialogProps) {
  const holidays = useHolidays(year, true);
  const create = useCreateHolidayClosures();
  const [picked, setPicked] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setError(null);
    const inputs = holidayClosures(holidays.data ?? [], picked, unitId);
    if (!inputs.length) {
      onClose();
      return;
    }
    try {
      await create.mutateAsync(inputs);
      onClose();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <ConfirmDialog
      title={`Feriados nacionais de ${year}`}
      confirmLabel={picked.length ? `Fechar em ${picked.length} ${picked.length === 1 ? 'dia' : 'dias'}` : 'Fechar'}
      busy={create.isPending}
      error={error ?? (holidays.isError ? errorMessage(holidays.error) : null)}
      onConfirm={() => void confirm()}
      onCancel={onClose}
    >
      <p className="field-hint">
        Marque os feriados em que esta unidade fecha. Feriados estaduais e municipais você cadastra
        em "Nova data".
      </p>
      {holidays.isPending ? <span className="skeleton-bar" /> : null}
      <ul className="holiday-list">
        {holidays.data?.map((h) => {
          const closed = holidayAlreadyClosed(h, unitId);
          const past = h.date < today;
          const [, m, d] = h.date.split('-');
          return (
            <li key={h.date}>
              <label className="check-field">
                <input
                  type="checkbox"
                  checked={closed || picked.includes(h.date)}
                  disabled={closed || past}
                  onChange={(e) =>
                    setPicked((p) => (e.target.checked ? [...p, h.date] : p.filter((x) => x !== h.date)))
                  }
                />
                <span className="tnum">
                  {d}/{m}
                </span>
                <span>{h.name}</span>
                {closed ? <span className="cell-muted">já fechado</span> : null}
                {past && !closed ? <span className="cell-muted">já passou</span> : null}
              </label>
            </li>
          );
        })}
      </ul>
    </ConfirmDialog>
  );
}
