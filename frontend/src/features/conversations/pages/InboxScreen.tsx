import { useState } from 'react';
import {
  clientFacts,
  clientHistory,
  messages,
  quickReplies,
  threads,
} from '../api/conversations.mock';
import { ThreadTagLabel } from '../ui/ThreadTagLabel';

const TABS = ['Todas', 'Aguardando', 'Minhas'];

export default function InboxScreen() {
  const [tab, setTab] = useState(0);
  const [activeId, setActiveId] = useState(threads[0].id);

  const visible = threads.filter((t) => {
    if (tab === 1) return t.tag === 'Aguardando humano';
    if (tab === 2) return Boolean(t.note);
    return true;
  });

  return (
    <div className="inbox">
      <div className="inbox-list">
        <div className="inbox-tabs">
          {TABS.map((label, i) => (
            <button
              type="button"
              key={label}
              className={`pill${tab === i ? ' is-active' : ''}`}
              onClick={() => setTab(i)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="inbox-threads">
          {visible.map((t) => (
            <button
              type="button"
              key={t.id}
              className={`thread${activeId === t.id ? ' is-active' : ''}`}
              onClick={() => setActiveId(t.id)}
            >
              <div className="thread-head">
                <span className="thread-name">{t.name}</span>
                <span className="thread-time">{t.time}</span>
              </div>
              <div className="thread-last">{t.last}</div>
              <div className="thread-tags">
                <ThreadTagLabel tag={t.tag} />
                {t.note ? <span className="tag-note">{t.note}</span> : null}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="conversation">
        <div className="conversation-head">
          <div className="avatar avatar-md">RL</div>
          <div>
            <div className="conversation-name">Rafael Lima</div>
            <div className="conversation-meta">+55 11 98812-4417 · WhatsApp</div>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="chip-outline">Conduzida pela IA</span>
            <button type="button" className="btn">
              Ver ficha
            </button>
            <button type="button" className="btn-primary">
              Assumir conversa
            </button>
          </div>
        </div>

        <div className="messages">
          {messages.map((m) => {
            const mine = m.author !== 'cliente';
            return (
              <div className={`message-row${mine ? ' is-mine' : ''}`} key={m.id}>
                <div className="bubble">
                  <div>{m.text}</div>
                  <div className="bubble-meta">{m.meta}</div>
                </div>
              </div>
            );
          })}
          <div className="divider-note">
            <span>Agendamento criado pela IA · 17/08 10:30 · Diego Martins</span>
          </div>
        </div>

        <div className="composer">
          <div className="composer-locked">
            A IA está respondendo. Assuma a conversa para digitar.
          </div>
          <div className="composer-quick">
            <span className="composer-quick-label">Respostas rápidas:</span>
            {quickReplies.map((q) => (
              <button type="button" className="btn btn-sm" key={q}>
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      <aside className="client-panel">
        <div className="eyebrow">Cliente</div>
        <div className="client-name">Rafael Lima</div>
        <div className="client-sub">Cliente recorrente · desde mar/2024</div>
        <div className="hr" />
        {clientFacts.map((f) => (
          <div className="fact-row" key={f.label}>
            <span className="fact-key">{f.label}</span>
            <span className="fact-value">{f.value}</span>
          </div>
        ))}
        <div className="hr" />
        <div className="eyebrow" style={{ marginBottom: 8 }}>
          Últimos atendimentos
        </div>
        {clientHistory.map((h) => (
          <div className="visit-row" key={`${h.service}-${h.meta}`}>
            <div className="visit-service">{h.service}</div>
            <div className="visit-meta">{h.meta}</div>
          </div>
        ))}
      </aside>
    </div>
  );
}
