import { Link } from 'react-router-dom';

/**
 * Modules the prototype left out of scope. They follow the same table, filter
 * and form pattern as the Records screen.
 */
export default function ModulePlaceholder({ title }: { title: string }) {
  return (
    <div className="module-placeholder">
      <div className="module-placeholder-inner">
        <div className="module-placeholder-title">{title}</div>
        <div className="module-placeholder-body">
          Módulo fora do escopo desta exploração. Segue o mesmo padrão de tabela, filtros e
          formulário do módulo de Cadastros.
        </div>
        <Link to="/app/cadastros" className="btn" style={{ display: 'inline-block', marginTop: 14, lineHeight: '28px' }}>
          Ver padrão de cadastro
        </Link>
      </div>
    </div>
  );
}
