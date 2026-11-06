import Icon from '@/shared/ui/Icon';

export default function Topbar({ title }: { title: string }) {
  return (
    <header className="topbar">
      <h1 className="topbar-title">{title}</h1>
      <div className="topbar-actions">
        <div className="fake-search">
          <Icon name="search" size={13} />
          <span>Buscar cliente, telefone…</span>
        </div>
        <button type="button" className="icon-button" aria-label="Notificações">
          <Icon name="bell" />
        </button>
      </div>
    </header>
  );
}
