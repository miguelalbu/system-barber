import { useState } from 'react';
import Icon from '../components/Icon';
import { Badge } from '../components/Badge';
import { barberRecords, cadastroTabs, serviceChips } from '@/data/app';

const COLUMNS = ['Barbeiro', 'Unidade', 'Serviços habilitados', 'Comissão', 'Horas/semana', 'Status', ''];

export default function CadastrosPage() {
  const [tab, setTab] = useState(1);
  const [formOpen, setFormOpen] = useState(false);

  return (
    <div style={{ padding: 20 }}>
      <div className="tab-row">
        {cadastroTabs.map((label, i) => (
          <button
            type="button"
            key={label}
            className={`pill pill-lg${tab === i ? ' is-active' : ''}`}
            onClick={() => setTab(i)}
          >
            {label}
          </button>
        ))}
      </div>

      <section className="panel">
        <div className="toolbar">
          <div className="fake-search-sm">
            <Icon name="search" size={13} />
            <span>Buscar barbeiro</span>
          </div>
          <button type="button" className="btn btn-sm" style={{ height: 28, padding: '0 10px' }}>
            Unidade: todas
          </button>
          <button type="button" className="btn btn-sm" style={{ height: 28, padding: '0 10px' }}>
            Status: ativos
          </button>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <span className="record-count">{barberRecords.length} registros</span>
            <button type="button" className="btn-primary" onClick={() => setFormOpen(true)}>
              Novo barbeiro
            </button>
          </div>
        </div>

        <table className="table">
          <thead>
            <tr>
              {COLUMNS.map((c, i) => (
                <th key={c || 'actions'} className={i === COLUMNS.length - 1 ? 'col-right' : undefined}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {barberRecords.map((r) => (
              <tr key={r.id}>
                <td>
                  <div className="staff-cell">
                    <div className="avatar avatar-sm">{r.initials}</div>
                    <div>
                      <div className="staff-name">{r.name}</div>
                      <div className="staff-email">{r.email}</div>
                    </div>
                  </div>
                </td>
                <td className="cell-muted">{r.unit}</td>
                <td className="cell-muted">{r.services}</td>
                <td className="tnum">{r.commission}</td>
                <td className="cell-muted tnum">{r.hours}</td>
                <td>
                  <Badge kind={r.kind}>{r.status}</Badge>
                </td>
                <td className="col-right">
                  <button type="button" className="btn btn-sm" onClick={() => setFormOpen(true)}>
                    Editar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {formOpen ? (
        <section className="panel" style={{ marginTop: 16 }}>
          <div className="panel-head">
            <div className="panel-title">Editar barbeiro · Diego Martins</div>
            <button type="button" className="btn-quiet" onClick={() => setFormOpen(false)}>
              Fechar
            </button>
          </div>

          <div className="form-grid">
            <label className="field">
              <span className="field-label">Nome completo</span>
              <input className="input" defaultValue="Diego Martins" />
            </label>
            <label className="field">
              <span className="field-label">E-mail de acesso</span>
              <input className="input" defaultValue="diego@barbeariacentral.com.br" />
            </label>
            <label className="field">
              <span className="field-label">Unidade</span>
              <select className="select" defaultValue="Centro">
                <option>Centro</option>
                <option>Zona Sul</option>
              </select>
            </label>
            <label className="field">
              <span className="field-label">Comissão padrão</span>
              <input className="input" defaultValue="45%" />
            </label>
            <label className="field">
              <span className="field-label">Jornada</span>
              <input className="input" defaultValue="Seg–Sáb, 09:00–19:00" />
            </label>
            <label className="field">
              <span className="field-label">Status</span>
              <select className="select" defaultValue="Ativo">
                <option>Ativo</option>
                <option>Inativo</option>
              </select>
            </label>

            <div className="field-full">
              <div className="field-label" style={{ marginBottom: 7 }}>
                Serviços habilitados
              </div>
              <div className="chip-row">
                {serviceChips.map((s) => (
                  <span key={s.label} className={`chip${s.enabled ? ' is-on' : ''}`}>
                    {s.label}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="panel-foot">
            <button type="button" className="btn" onClick={() => setFormOpen(false)}>
              Cancelar
            </button>
            <button type="button" className="btn-primary" onClick={() => setFormOpen(false)}>
              Salvar alterações
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
