const COLUMNS = [
  {
    heading: 'Produto',
    links: [
      { href: '#funcionalidades', label: 'Funcionalidades' },
      { href: '#whatsapp', label: 'WhatsApp com IA' },
      { href: '#planos', label: 'Planos' },
    ],
  },
  {
    heading: 'Empresa',
    links: [
      { href: '#faq', label: 'Perguntas frequentes' },
      { href: '#privacidade', label: 'Privacidade e LGPD' },
      { href: '#termos', label: 'Termos de uso' },
    ],
  },
  {
    heading: 'Contato',
    links: [
      { href: '#contato', label: '(19) 99000-0000' },
      { href: '#contato', label: 'contato@navalha.app' },
      { href: '#instagram', label: 'Instagram' },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="wrap footer-grid">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="footer-brand-mark">N</span>
            <span style={{ fontSize: 14.5, fontWeight: 600 }}>Navalha.app</span>
          </div>
          <p className="footer-blurb">Gestão e atendimento automatizado para barbearias.</p>
        </div>

        {COLUMNS.map((col) => (
          <div key={col.heading}>
            <div className="footer-heading">{col.heading}</div>
            <ul className="footer-links">
              {col.links.map((l) => (
                <li key={l.label}>
                  <a href={l.href}>{l.label}</a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="wrap footer-legal-wrap">
        <div className="footer-legal">
          © 2026 Navalha Tecnologia LTDA · CNPJ 00.000.000/0001-00
        </div>
      </div>
    </footer>
  );
}
