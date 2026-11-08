/** 16×16 stroke icons from the prototype, drawn with `currentColor`. */

export type IconName =
  | 'dashboard'
  | 'agenda'
  | 'inbox'
  | 'clientes'
  | 'cadastros'
  | 'financeiro'
  | 'tokens'
  | 'chevron-down'
  | 'chevron-left'
  | 'chevron-right'
  | 'search'
  | 'bell'
  | 'warning'
  | 'close'
  | 'logout'
  | 'unit'
  | 'scissors'
  | 'clock'
  | 'bottle'
  | 'layers'
  | 'star'
  | 'ticket'
  | 'card'
  | 'settings';

const PATHS: Record<IconName, string> = {
  dashboard: 'M3 9.5 8 4l5 5.5V13a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z',
  agenda: 'M3.5 4h9a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1h-9a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM2.5 7h11M5.5 2.5v3M10.5 2.5v3',
  inbox: 'M2.5 3.5h11v7h-6l-3 2.5v-2.5h-2z',
  clientes:
    'M6 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM1.5 13.5c0-2.2 2-3.5 4.5-3.5s4.5 1.3 4.5 3.5M11 4.2a2.2 2.2 0 0 1 0 4.3M12.5 13.5c0-1.4-.5-2.3-1.4-2.9',
  cadastros: 'M2.5 5.5 8 2.5l5.5 3v5L8 13.5l-5.5-3zM2.5 5.5 8 8.5l5.5-3M8 8.5v5',
  financeiro: 'M2.5 4.5h11v7h-11zM8 6.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3',
  tokens: 'M2.5 3.5h11v9h-11zM2.5 7h11M6 7v5.5',
  'chevron-down': 'M4 6.5 8 10.5 12 6.5',
  'chevron-left': 'M9.5 3.5 5 8l4.5 4.5',
  'chevron-right': 'M6.5 3.5 11 8l-4.5 4.5',
  search: 'M7 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM10.6 10.6 14 14',
  bell: 'M8 2a4 4 0 0 0-4 4v3l-1.2 2h10.4L12 9V6a4 4 0 0 0-4-4zM6.5 13.2a1.6 1.6 0 0 0 3 0',
  warning: 'M8 2.5 14.5 13.5h-13zM8 6.5v3.2M8 11.6v.2',
  close: 'M4 4l8 8M12 4l-8 8',
  logout: 'M9.5 2.5h2.5a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H9.5M9 8H2.5M4.5 5.5 2 8l2.5 2.5',
  unit: 'M3 13.5v-9l5-2 5 2v9M2 13.5h12M6.5 13.5v-3h3v3M5.5 6.5h1M9.5 6.5h1M5.5 8.5h1M9.5 8.5h1',
  scissors:
    'M4.5 6a1.7 1.7 0 1 0 0-3.4 1.7 1.7 0 0 0 0 3.4zM4.5 13.4a1.7 1.7 0 1 0 0-3.4 1.7 1.7 0 0 0 0 3.4zM5.9 5.3 13.5 12M5.9 10.7 13.5 4',
  clock: 'M8 14a6 6 0 1 0 0-12 6 6 0 0 0 0 12zM8 4.8V8l2.2 1.5',
  bottle:
    'M6.5 2h3M7 2v2.3L5.3 6a1.4 1.4 0 0 0-.4 1v6a1 1 0 0 0 1 1h4.2a1 1 0 0 0 1-1V7a1.4 1.4 0 0 0-.4-1L9 4.3V2M4.9 9h6.2',
  layers: 'M8 2.5l6 3-6 3-6-3zM2 8.3l6 3 6-3M2 11l6 3 6-3',
  star: 'M8 2.2l1.8 3.7 4 .6-2.9 2.8.7 4L8 11.4l-3.6 1.9.7-4-2.9-2.8 4-.6z',
  ticket: 'M2.5 4.5h11v2a1.5 1.5 0 0 0 0 3v2h-11v-2a1.5 1.5 0 0 0 0-3zM10 4.5v7',
  card: 'M2 4h12v8H2zM2 6.8h12M4.5 10h2',
  settings:
    'M8 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM8 1.8v1.7M8 12.5v1.7M1.8 8h1.7M12.5 8h1.7M3.6 3.6l1.2 1.2M11.2 11.2l1.2 1.2M3.6 12.4l1.2-1.2M11.2 4.8l1.2-1.2',
};

interface IconProps {
  name: IconName;
  size?: number;
  stroke?: string;
  className?: string;
  style?: React.CSSProperties;
}

export default function Icon({ name, size = 15, stroke = 'currentColor', className, style }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke={stroke}
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
      style={{ flex: 'none', ...style }}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
