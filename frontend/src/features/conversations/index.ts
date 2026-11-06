/** Public API of the conversations feature — the only entry point other code may import. */
export { default as InboxScreen } from './pages/InboxScreen';
export { ThreadTagLabel } from './ui/ThreadTagLabel';
export type { Thread, ThreadTag } from './model/conversations.types';
// Demo data, shown on the dashboard too until the conversations API exists.
export { threads as conversationThreads } from './api/conversations.mock';
