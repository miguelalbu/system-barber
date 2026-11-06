/**
 * Status pill and conversation tag. Purely visual: each variant is a CSS class
 * in `shared/styles/panel.css`; features map their own statuses onto them.
 */

export type BadgeVariant = 'confirmado' | 'pendente' | 'concluido' | 'cancelado' | 'ativo';

export function Badge({ kind, children }: { kind: BadgeVariant; children: React.ReactNode }) {
  return <span className={`badge badge-${kind}`}>{children}</span>;
}

export type TagVariant = 'waiting' | 'ai' | 'done';

export function Tag({ variant, children }: { variant: TagVariant; children: React.ReactNode }) {
  return <span className={`tag tag-${variant}`}>{children}</span>;
}
