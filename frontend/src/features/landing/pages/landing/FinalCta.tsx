import { useState } from 'react';
import Reveal from './Reveal';

export default function FinalCta() {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [sent, setSent] = useState(false);

  // TODO(backend): enviar para POST /api/leads.
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !phone.trim()) return;
    setSent(true);
  };

  return (
    <section id="cta-final" className="section">
      <div className="wrap" style={{ paddingTop: 72, paddingBottom: 72 }}>
        <Reveal className="cta-inner">
          <h2 className="cta-title">Veja funcionando com a agenda da sua barbearia</h2>
          <p className="cta-sub">
            Demonstração de 20 minutos, sem compromisso. Teste 14 dias depois, se fizer sentido.
          </p>
          <form className="lead-form" onSubmit={submit}>
            <input
              className="lead-input"
              placeholder="Nome da barbearia"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setSent(false);
              }}
            />
            <input
              className="lead-input is-phone"
              placeholder="WhatsApp"
              value={phone}
              onChange={(e) => {
                setPhone(e.target.value);
                setSent(false);
              }}
            />
            <button type="submit" className="lead-submit">
              Agendar demonstração
            </button>
          </form>
          <p className="lead-status" role="status">
            {sent
              ? 'Recebido. Entramos em contato pelo WhatsApp em até 1 dia útil.'
              : 'A gente responde pelo WhatsApp em até 1 dia útil.'}
          </p>
        </Reveal>
      </div>
    </section>
  );
}
