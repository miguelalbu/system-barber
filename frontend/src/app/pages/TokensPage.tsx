/** Documentação viva do design system — espelha src/styles/tokens.css. */

const PALETTE = [
  { name: 'canvas', hex: '#F4F5F6', use: 'fundo da aplicação' },
  { name: 'surface', hex: '#FFFFFF', use: 'painéis, tabelas' },
  { name: 'border', hex: '#E3E6E8', use: 'divisórias, inputs' },
  { name: 'text', hex: '#16191C', use: 'texto principal' },
  { name: 'muted', hex: '#667077', use: 'texto secundário' },
  { name: 'accent', hex: '#175C6B', use: 'ação primária, ativo' },
];

const TYPE_SCALE: Array<{ spec: string; sample: string; style: React.CSSProperties }> = [
  { spec: '26 / 600 / -0.02em', sample: 'R$ 2.940', style: { fontSize: 26, fontWeight: 600, letterSpacing: '-0.02em' } },
  { spec: '15 / 600', sample: 'Título de página', style: { fontSize: 15, fontWeight: 600 } },
  { spec: '13 / 600', sample: 'Título de seção', style: { fontSize: 13, fontWeight: 600 } },
  { spec: '13 / 400', sample: 'Corpo e células de tabela', style: { fontSize: 13 } },
  { spec: '12 / 400 · muted', sample: 'Texto de apoio e metadados', style: { fontSize: 12, color: 'var(--app-muted)' } },
  {
    spec: '11 / 600 / 0.05em caps',
    sample: 'CABEÇALHO DE COLUNA',
    style: { fontSize: 11, fontWeight: 600, letterSpacing: '0.05em' },
  },
];

const SPACING = [
  { name: 'space-1', px: 4, use: 'gap interno de chip' },
  { name: 'space-2', px: 8, use: 'gap entre controles' },
  { name: 'space-3', px: 12, use: 'padding de célula' },
  { name: 'space-4', px: 16, use: 'padding de painel' },
  { name: 'space-5', px: 20, use: 'margem de tela' },
  { name: 'space-6', px: 24, use: 'separação de blocos' },
];

export default function TokensPage() {
  return (
    <div className="tokens-page">
      <section className="token-card">
        <div className="panel-title" style={{ marginBottom: 12 }}>
          Paleta
        </div>
        <div className="palette-grid">
          {PALETTE.map((p) => (
            <div key={p.name}>
              <div className="palette-swatch" style={{ background: p.hex }} />
              <div className="palette-name">{p.name}</div>
              <div className="palette-hex mono">{p.hex}</div>
              <div className="palette-use">{p.use}</div>
            </div>
          ))}
        </div>
      </section>

      <div className="tokens-grid">
        <section className="token-card">
          <div className="panel-title" style={{ marginBottom: 12 }}>
            Tipografia — IBM Plex Sans
          </div>
          {TYPE_SCALE.map((t) => (
            <div className="type-row" key={t.spec}>
              <span className="type-spec mono">{t.spec}</span>
              <span style={t.style}>{t.sample}</span>
            </div>
          ))}
        </section>

        <div className="stack-16">
          <section className="token-card">
            <div className="panel-title" style={{ marginBottom: 12 }}>
              Espaçamento (base 4)
            </div>
            {SPACING.map((s) => (
              <div className="space-row" key={s.name}>
                <span className="space-name mono">{s.name}</span>
                <div className="space-bar" style={{ width: s.px * 2 }} />
                <span className="space-use">{s.use}</span>
              </div>
            ))}
          </section>

          <section className="token-card">
            <div className="panel-title" style={{ marginBottom: 12 }}>
              Raio e elevação
            </div>
            <div className="radius-row">
              <div className="radius-demo">
                radius-sm 6px
                <br />
                controles, badges
              </div>
              <div className="radius-demo is-md">
                radius-md 8px
                <br />
                cards, painéis
              </div>
              <div className="radius-demo is-overlay">
                shadow-overlay
                <br />
                modal, dropdown
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
