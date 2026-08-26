import type { Feature } from '@/data/landing';

/** Ícones 20×20 das funcionalidades, traçados na cor de acento da landing. */
export default function FeatureIcon({ name }: { name: Feature['icon'] }) {
  const common = {
    width: 20,
    height: 20,
    viewBox: '0 0 20 20',
    fill: 'none',
    stroke: 'var(--site-accent)',
    strokeWidth: 1.3,
    'aria-hidden': true,
    focusable: 'false' as const,
  };

  switch (name) {
    case 'agenda':
      return (
        <svg {...common}>
          <rect x="2.5" y="3.5" width="15" height="14" rx="2" />
          <line x1="2.5" y1="7.5" x2="17.5" y2="7.5" />
          <line x1="7.5" y1="7.5" x2="7.5" y2="17.5" />
          <line x1="12.5" y1="7.5" x2="12.5" y2="17.5" />
        </svg>
      );
    case 'people':
      return (
        <svg {...common}>
          <circle cx="10" cy="7" r="3" />
          <path d="M4 17c0-3.3 2.7-5 6-5s6 1.7 6 5" />
        </svg>
      );
    case 'card':
      return (
        <svg {...common}>
          <rect x="2.5" y="5.5" width="15" height="10" rx="2" />
          <line x1="2.5" y1="9" x2="17.5" y2="9" />
        </svg>
      );
    case 'chart':
      return (
        <svg {...common}>
          <line x1="3" y1="16.5" x2="17" y2="16.5" />
          <rect x="4.5" y="10" width="3" height="5" />
          <rect x="9" y="6.5" width="3" height="8.5" />
          <rect x="13.5" y="3.5" width="3" height="11.5" />
        </svg>
      );
    case 'clock':
      return (
        <svg {...common}>
          <circle cx="10" cy="10" r="7" />
          <path d="M10 6v4.2l3 1.8" />
        </svg>
      );
    case 'grid':
      return (
        <svg {...common}>
          <rect x="3" y="3" width="6" height="6" rx="1" />
          <rect x="11" y="3" width="6" height="6" rx="1" />
          <rect x="3" y="11" width="6" height="6" rx="1" />
          <rect x="11" y="11" width="6" height="6" rx="1" />
        </svg>
      );
    case 'terminal':
      return (
        <svg {...common}>
          <rect x="2.5" y="4.5" width="15" height="11" rx="2" />
          <line x1="6" y1="12" x2="10" y2="12" />
          <circle cx="14" cy="12" r="1.2" />
        </svg>
      );
    case 'lock':
      return (
        <svg {...common}>
          <rect x="3" y="7" width="14" height="10" rx="2" />
          <path d="M7 7V5.5A3 3 0 0 1 13 5.5V7" />
          <line x1="10" y1="11" x2="10" y2="13" />
        </svg>
      );
  }
}
