import type { BadgeKind, ThreadTag } from '@/types';

export function Badge({ kind, children }: { kind: BadgeKind; children: React.ReactNode }) {
  return <span className={`badge badge-${kind}`}>{children}</span>;
}

const TAG_CLASS: Record<ThreadTag, string> = {
  'Aguardando humano': 'tag-waiting',
  'IA conduzindo': 'tag-ai',
  Resolvida: 'tag-done',
};

export function Tag({ tag, label }: { tag: ThreadTag; label?: string }) {
  return <span className={`tag ${TAG_CLASS[tag]}`}>{label ?? tag}</span>;
}
