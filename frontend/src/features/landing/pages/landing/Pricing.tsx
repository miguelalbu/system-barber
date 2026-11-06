import { useState } from 'react';
import Reveal from './Reveal';
import { plans } from '../../model/landing.content';

export default function Pricing() {
  const [yearly, setYearly] = useState(false);

  /** On the yearly cycle the customer pays 10 months; we show the monthly equivalent. */
  const price = (monthly: number) => (yearly ? Math.round((monthly * 10) / 12) : monthly);

  return (
    <section id="planos" className="section">
      <div className="wrap section-pad">
        <Reveal className="pricing-head">
          <div className="measure">
            <div className="eyebrow-site">Planos</div>
            <h2 className="h2">Preço por barbearia, não por barbeiro</h2>
          </div>
          <div className="cycle-toggle">
            <button
              type="button"
              className={!yearly ? 'is-active' : ''}
              onClick={() => setYearly(false)}
            >
              Mensal
            </button>
            <button
              type="button"
              className={yearly ? 'is-active' : ''}
              onClick={() => setYearly(true)}
            >
              Anual · 2 meses grátis
            </button>
          </div>
        </Reveal>

        <Reveal className="plan-grid">
          {plans.map((plan) => (
            <div className={`plan${plan.featured ? ' is-featured' : ''}`} key={plan.name}>
              <div className="plan-head">
                <h3>{plan.name}</h3>
                {plan.badge ? <span className="plan-badge mono">{plan.badge}</span> : null}
              </div>
              <p className="plan-tagline">{plan.tagline}</p>
              <div className="plan-price">
                <strong>R$ {price(plan.monthly)}</strong>
                <span>{plan.unit}</span>
              </div>
              <ul className="plan-items">
                {plan.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <a
                href="#cta-final"
                className={`plan-cta${plan.featured ? ' is-solid' : ''}`}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </Reveal>

        <p className="pricing-note">
          O custo das conversas cobradas pela Meta é repassado sem margem e aparece detalhado na sua
          fatura.
        </p>
      </div>
    </section>
  );
}
