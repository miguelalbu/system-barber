import { useState } from 'react';
import Reveal from './Reveal';
import { heroAgenda, heroAgendaBarbers, heroChat } from '@/data/landing';

type Visual = 'whatsapp' | 'agenda';

export default function Hero() {
  const [visual, setVisual] = useState<Visual>('whatsapp');

  return (
    <section id="topo" className="hero">
      <div className="wrap hero-grid" style={{ maxWidth: 1160 }}>
        <Reveal className="hero-copy">
          <div className="hero-badge">
            <span className="dot" />
            WhatsApp Business API oficial (Meta)
          </div>
          <h1 className="hero-title">Sua barbearia respondendo no WhatsApp sozinha.</h1>
          <p className="hero-sub">
            Agenda por barbeiro, financeiro, planos de assinatura e um atendimento que agenda,
            remarca e lembra o cliente no WhatsApp — sem ninguém da recepção digitando.
          </p>
          <div className="hero-actions">
            <a href="#cta-final" className="btn-solid btn-solid-lg">
              Agendar demonstração
            </a>
            <a href="#whatsapp" className="btn-outline">
              Ver demonstração
            </a>
          </div>
          <p className="hero-fineprint">
            Teste 14 dias. Sem cartão, sem fidelidade, migração da agenda inclusa.
          </p>
        </Reveal>

        <Reveal className="hero-visual">
          <div className="visual-tabs">
            <button
              type="button"
              className={`visual-tab${visual === 'whatsapp' ? ' is-active' : ''}`}
              onClick={() => setVisual('whatsapp')}
            >
              Conversa no WhatsApp
            </button>
            <button
              type="button"
              className={`visual-tab${visual === 'agenda' ? ' is-active' : ''}`}
              onClick={() => setVisual('agenda')}
            >
              Agenda do dia
            </button>
          </div>

          {visual === 'whatsapp' ? <ChatPreview /> : <AgendaPreview />}
        </Reveal>
      </div>
    </section>
  );
}

function ChatPreview() {
  return (
    <div className="device">
      <div className="device-head">
        <span className="chat-avatar">BC</span>
        <div style={{ flex: 1 }}>
          <div className="device-title">Barbearia Central</div>
          <div className="device-meta mono">conta comercial verificada</div>
        </div>
        <span className="device-time mono">14:02</span>
      </div>
      <div className="chat-body">
        {heroChat.map((m, i) => (
          <div key={i} className={`chat-bubble from-${m.from}`}>
            {m.text}
          </div>
        ))}
        <div className="chat-system mono">
          <span className="dot" />
          agendamento criado na agenda do Rafael
        </div>
      </div>
    </div>
  );
}

function AgendaPreview() {
  return (
    <div className="device">
      <div className="device-head" style={{ justifyContent: 'space-between' }}>
        <div className="device-title">Quarta, 18 de setembro</div>
        <div className="device-meta mono">3 barbeiros · 21 horários</div>
      </div>
      <div className="mini-agenda">
        <div className="mini-agenda-corner" />
        {heroAgendaBarbers.map((b) => (
          <div className="mini-agenda-head" key={b}>
            {b}
          </div>
        ))}

        {heroAgenda.map((row) => (
          <Row key={row.time} row={row} />
        ))}
      </div>
    </div>
  );
}

function Row({ row }: { row: (typeof heroAgenda)[number] }) {
  return (
    <>
      <div className="mini-agenda-time mono">{row.time}</div>
      {row.cells.map((cell, i) => (
        <div className="mini-agenda-cell" key={i}>
          {cell ? (
            <div className={`mini-agenda-event${cell.sub ? ' is-ai' : ''}`}>
              {cell.label}
              {cell.sub ? <div className="mini-agenda-event-sub mono">{cell.sub}</div> : null}
            </div>
          ) : null}
        </div>
      ))}
    </>
  );
}
