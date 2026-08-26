import { Link } from 'react-router-dom';
import { navLinks } from '@/data/landing';

export default function Header() {
  return (
    <header className="site-header">
      <div className="wrap site-header-inner">
        <a href="#topo" className="brand">
          <span className="brand-mark">N</span>
          <span className="brand-name">
            Navalha<span>.app</span>
          </span>
        </a>

        <nav className="site-nav">
          {navLinks.map((l) => (
            <a key={l.href} href={l.href}>
              {l.label}
            </a>
          ))}
        </nav>

        <div className="header-actions">
          {/* Entra direto no painel — o login real chega com o backend. */}
          <Link to="/app/agenda" className="header-login">
            Entrar
          </Link>
          <a href="#cta-final" className="btn-solid">
            Agendar demonstração
          </a>
        </div>
      </div>
    </header>
  );
}
