interface TableStateProps {
  columns: number;
  state: 'loading' | 'empty' | 'error';
  /** Empty: what to say. Error: the message. */
  message?: string;
  /** Empty: create button; error: retry button. */
  action?: { label: string; onClick: () => void };
}

/** The non-data states of a list, as rows inside its own table. */
export default function TableState({ columns, state, message, action }: TableStateProps) {
  if (state === 'loading') {
    return (
      <>
        {[0, 1, 2].map((row) => (
          <tr key={row} aria-hidden="true">
            {Array.from({ length: columns }, (_, col) => (
              <td key={col}>
                <span className="skeleton-bar" />
              </td>
            ))}
          </tr>
        ))}
      </>
    );
  }

  return (
    <tr>
      <td colSpan={columns}>
        <div className={`table-state${state === 'error' ? ' is-error' : ''}`} role={state === 'error' ? 'alert' : undefined}>
          <span>{message}</span>
          {action ? (
            <button type="button" className="btn btn-sm" onClick={action.onClick}>
              {action.label}
            </button>
          ) : null}
        </div>
      </td>
    </tr>
  );
}
