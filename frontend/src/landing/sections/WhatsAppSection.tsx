import Reveal from './Reveal';
import { aiCapabilities, darkChat } from '@/data/landing';

export default function WhatsAppSection() {
  return (
    <section id="whatsapp" className="dark-section">
      <div className="wrap">
        <Reveal className="split">
          <div>
            <div className="dark-eyebrow">O diferencial</div>
            <h2 className="dark-h2">
              Atendimento automatizado no seu próprio número de WhatsApp
            </h2>
            <p className="dark-lede">
              Roda sobre a API oficial do WhatsApp Business, homologada pela Meta. Não é bot de
              celular espelhado, não cai por bloqueio e mantém seu número verificado.
            </p>
            <ul className="capability-list">
              {aiCapabilities.map((c) => (
                <li className="capability" key={c.title}>
                  <span className="capability-dot" />
                  <div>
                    <strong>{c.title}</strong>
                    <span>{c.body}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="dark-device">
            <div className="dark-device-head">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="dark-avatar">MR</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>Marcos Ribeiro</div>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--site-muted-4)' }}>
                    cliente desde 2022 · 18 visitas
                  </div>
                </div>
              </div>
              <span className="mono" style={{ fontSize: 11, color: 'var(--site-muted-4)' }}>
                21:47
              </span>
            </div>
            <div className="dark-chat">
              <div className="dark-chat-note mono">fora do horário de funcionamento</div>
              {darkChat.map((m, i) => (
                <div key={i} className={`dark-bubble from-${m.from}`}>
                  {m.text}
                </div>
              ))}
              <div className="dark-system mono">
                <span className="dot" />
                conversa transferida para Rafael (dono)
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
