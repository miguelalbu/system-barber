import { faq, features, stats, steps, testimonials } from '../model/landing.content';
import FeatureIcon from './landing/FeatureIcon';
import FinalCta from './landing/FinalCta';
import Footer from './landing/Footer';
import Header from './landing/Header';
import Hero from './landing/Hero';
import Pricing from './landing/Pricing';
import Reveal from './landing/Reveal';
import WhatsAppSection from './landing/WhatsAppSection';
import './landing/landing.css';

export default function LandingScreen() {
  return (
    <div className="site">
      <Header />
      <Hero />

      <section className="section">
        <div className="wrap" style={{ paddingTop: 44, paddingBottom: 44 }}>
          <Reveal className="stats-grid">
            {stats.map((s) => (
              <div key={s.figure}>
                <div className="stat-figure">{s.figure}</div>
                <p className="stat-body">{s.body}</p>
              </div>
            ))}
          </Reveal>
          <p className="footnote mono" style={{ marginTop: 26 }}>
            Substituir por fonte real antes de publicar (ex.: pesquisa interna, base de clientes,
            Sebrae).
          </p>
        </div>
      </section>

      <section id="funcionalidades" className="section">
        <div className="wrap section-pad">
          <Reveal className="measure">
            <div className="eyebrow-site">Funcionalidades</div>
            <h2 className="h2">Tudo que você já espera de um sistema de gestão</h2>
            <p className="lede">Sem módulo extra, sem cobrança por barbeiro adicional no plano Pro.</p>
          </Reveal>
          <Reveal className="feature-grid">
            {features.map((f) => (
              <div className="feature" key={f.title}>
                <FeatureIcon name={f.icon} />
                <h3>{f.title}</h3>
                <p>{f.body}</p>
              </div>
            ))}
          </Reveal>
        </div>
      </section>

      <WhatsAppSection />

      <section id="como-funciona" className="section">
        <div className="wrap section-pad">
          <Reveal className="measure">
            <div className="eyebrow-site">Como funciona</div>
            <h2 className="h2">Funcionando em três passos, no mesmo dia</h2>
          </Reveal>
          <Reveal className="steps-grid">
            {steps.map((s) => (
              <div className="step" key={s.n}>
                <div className="step-n mono">{s.n}</div>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </Reveal>
        </div>
      </section>

      <section className="section section-white">
        <div className="wrap section-pad">
          <Reveal className="measure">
            <div className="eyebrow-site">Quem usa</div>
            <h2 className="h2">Barbearias que trocaram a recepção pelo chat</h2>
          </Reveal>
          <Reveal className="testimonial-grid">
            {testimonials.map((t) => (
              <div className="testimonial" key={t.name}>
                <div className="testimonial-headline">{t.headline}</div>
                <p className="testimonial-quote">{t.quote}</p>
                <div className="testimonial-author">
                  <span className="testimonial-avatar">{t.initials}</span>
                  <div>
                    <div className="testimonial-name">{t.name}</div>
                    <div className="testimonial-org">{t.org}</div>
                  </div>
                </div>
              </div>
            ))}
          </Reveal>
          <p className="footnote mono" style={{ marginTop: 22 }}>
            Trocar por depoimentos e fotos reais com autorização antes de publicar.
          </p>
        </div>
      </section>

      <Pricing />

      <section id="faq" className="section section-white">
        <div className="wrap section-pad">
          <Reveal className="faq-split split">
            <div>
              <div className="eyebrow-site">FAQ</div>
              <h2 className="h2">Perguntas que todo dono faz na primeira conversa</h2>
              <p className="faq-intro">
                Não achou a sua? <a href="#cta-final">Fale com a gente</a> antes de assinar.
              </p>
            </div>
            <div className="faq-list">
              {faq.map((item) => (
                <div className="faq-item" key={item.q}>
                  <h3>{item.q}</h3>
                  <p>{item.a}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <FinalCta />
      <Footer />
    </div>
  );
}
