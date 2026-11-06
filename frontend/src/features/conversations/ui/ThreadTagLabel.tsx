import { Tag, type TagVariant } from '@/shared/ui/Badge';
import type { ThreadTag } from '../model/conversations.types';

const VARIANT: Record<ThreadTag, TagVariant> = {
  'Aguardando humano': 'waiting',
  'IA conduzindo': 'ai',
  Resolvida: 'done',
};

/** Who is handling the conversation, as a colored tag. */
export function ThreadTagLabel({ tag, label }: { tag: ThreadTag; label?: string }) {
  return <Tag variant={VARIANT[tag]}>{label ?? tag}</Tag>;
}
