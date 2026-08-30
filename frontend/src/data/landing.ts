/** Landing page content, extracted from the design prototype. */

export interface Feature {
  title: string;
  body: string;
  icon: 'agenda' | 'people' | 'card' | 'chart' | 'clock' | 'grid' | 'terminal' | 'lock';
}

export const stats = [
  {
    figure: '1 em cada 4',
    body: 'horários marcados por telefone ou DM viram falta quando não existe confirmação automática.',
  },
  {
    figure: '2h13',
    body: 'é o tempo médio que a recepção gasta por dia só respondendo "tem horário?" no WhatsApp.',
  },
  {
    figure: '62%',
    body: 'das mensagens chegam fora do horário de funcionamento — e é aí que o cliente marca no concorrente.',
  },
];

export const features: Feature[] = [
  { icon: 'agenda', title: 'Agenda por barbeiro', body: 'Cada profissional com sua coluna, seus serviços e seus horários de trabalho.' },
  { icon: 'people', title: 'Barbeiros, unidades e serviços', body: 'Cadastro completo com duração, preço e permissão de acesso por pessoa.' },
  { icon: 'card', title: 'Clubes e assinaturas', body: 'Planos mensais com cobrança recorrente e controle de uso por cliente.' },
  { icon: 'chart', title: 'Comissão e financeiro', body: 'Fechamento por barbeiro, formas de pagamento e faturamento do mês.' },
  { icon: 'clock', title: 'Lembretes automáticos', body: 'Confirmação e lembrete no WhatsApp antes do horário, com resposta livre.' },
  { icon: 'grid', title: 'Histórico do cliente', body: 'Serviços, gastos, frequência e quem está há tempo demais sem voltar.' },
  { icon: 'terminal', title: 'Comanda e pagamento', body: 'Serviços e produtos na mesma comanda, com pagamento dividido e integração com a maquininha.' },
  { icon: 'lock', title: 'Controle de estoque', body: 'Baixa automática de pomada, shampoo e lâmina na venda, com aviso de nível mínimo.' },
];

export const aiCapabilities = [
  { title: 'Agendamento', body: ' — consulta a agenda real do barbeiro e fecha o horário na hora.' },
  { title: 'Remarcação e cancelamento', body: ' — o cliente resolve pelo chat e o horário livre volta pra fila.' },
  { title: 'Lembrete automático', body: ' — aviso antes do horário com confirmação em um toque.' },
  { title: 'Cutucada de cliente inativo', body: ' — quem não aparece há 40 dias recebe convite pra voltar.' },
  { title: 'Handoff pra humano', body: ' — reclamação, orçamento fora do padrão ou dúvida difícil cai direto no seu app.' },
];

export const steps = [
  {
    n: '01',
    title: 'Cadastre a barbearia',
    body: 'Serviços, preços, barbeiros e horários. Se você já usa outro sistema, a gente importa sua agenda e sua base de clientes.',
  },
  {
    n: '02',
    title: 'Conecte seu WhatsApp',
    body: 'Verificação do número na API oficial da Meta, feita junto com nosso time. Você continua com o mesmo número de sempre.',
  },
  {
    n: '03',
    title: 'Os clientes já agendam sozinhos',
    body: 'Você acompanha tudo pelo painel e só entra na conversa quando o atendimento é transferido pra você.',
  },
];

export const testimonials = [
  {
    headline: 'Falta caiu 31%',
    quote:
      '"O lembrete automático resolveu o que eu tentei resolver por dois anos ligando pra cliente. Em três meses a falta caiu de 22% pra 15%."',
    initials: 'RS',
    name: 'Rafael Souza',
    org: 'Barbearia Central · Campinas, SP',
  },
  {
    headline: '2 horas por dia de volta',
    quote:
      '"Minha recepcionista parou de ficar presa no WhatsApp. Hoje ela atende quem está na cadeira e o chat resolve o resto sozinho."',
    initials: 'CM',
    name: 'Camila Martins',
    org: 'Studio 47 · Belo Horizonte, MG',
  },
  {
    headline: '+18% de recorrência',
    quote:
      '"A mensagem pra cliente inativo trouxe 60 pessoas de volta no primeiro mês. Nenhuma delas eu teria lembrado de chamar."',
    initials: 'JA',
    name: 'Jonas Alves',
    org: 'Corte Fino · Curitiba, PR',
  },
];

export interface Plan {
  name: string;
  tagline: string;
  /** Monthly price in BRL; the yearly cycle gives 2 months free. */
  monthly: number;
  unit: string;
  items: string[];
  cta: string;
  featured?: boolean;
  badge?: string;
}

export const plans: Plan[] = [
  {
    name: 'Básico',
    tagline: 'Agenda e financeiro, sem atendimento automatizado.',
    monthly: 129,
    unit: '/mês',
    items: [
      'Agenda por barbeiro, até 4 profissionais',
      'Cadastro de serviços e clientes',
      'Comissão e fechamento de caixa',
      'Lembrete por WhatsApp (envio manual)',
    ],
    cta: 'Começar teste',
  },
  {
    name: 'Pro com IA',
    tagline: 'Tudo do Básico mais o atendimento automatizado no WhatsApp.',
    monthly: 249,
    unit: '/mês',
    items: [
      'Barbeiros ilimitados',
      'Agendamento e remarcação pela IA',
      'Lembrete e recuperação de cliente inativo',
      'Clubes e assinatura recorrente',
      'Handoff para atendimento humano',
    ],
    cta: 'Agendar demonstração',
    featured: true,
    badge: 'recomendado',
  },
  {
    name: 'Multi-unidades',
    tagline: 'Para redes com duas ou mais lojas e gestão centralizada.',
    monthly: 199,
    unit: '/mês por unidade',
    items: [
      'Tudo do Pro em todas as unidades',
      'Relatório consolidado da rede',
      'Permissões por unidade e por cargo',
      'Onboarding e suporte dedicados',
    ],
    cta: 'Falar com vendas',
  },
];

export const faq = [
  {
    q: 'Já uso outro sistema. Perco minha agenda?',
    a: 'Não. A gente importa clientes, histórico e agendamentos futuros do seu sistema atual e roda os dois em paralelo na primeira semana.',
  },
  {
    q: 'O que a IA faz com os dados dos meus clientes?',
    a: 'Os dados são seus e ficam em servidor no Brasil, conforme a LGPD. São usados só para atender o cliente da sua barbearia — não treinam modelo nem são compartilhados.',
  },
  {
    q: 'Quanto custa o WhatsApp oficial?',
    a: 'A Meta cobra por conversa iniciada pela empresa; conversa iniciada pelo cliente é gratuita nas primeiras 24 horas. Na prática, a maioria das barbearias gasta menos de R$ 40 por mês, cobrado sem margem.',
  },
  {
    q: 'A IA vai responder errado pro meu cliente?',
    a: 'Ela só responde sobre horários, serviços e preços cadastrados por você. Qualquer coisa fora disso é transferida para uma pessoa, com o histórico da conversa.',
  },
  {
    q: 'E o suporte?',
    a: 'Atendimento por WhatsApp de segunda a sábado, das 8h às 20h, com gente que conhece rotina de barbearia. Sem chamado por e-mail.',
  },
];

export const heroChat = [
  { from: 'cliente' as const, text: 'Boa tarde, tem horário com o Rafael amanhã de tarde?' },
  {
    from: 'ia' as const,
    text: 'Boa tarde, Diego! Amanhã o Rafael tem 15:30 e 17:00. Corte + barba leva 50 min. Qual prefere?',
  },
  { from: 'cliente' as const, text: '15:30 tá ótimo' },
  {
    from: 'ia' as const,
    text: 'Fechado. Quarta, 18/09 às 15:30 com o Rafael. Te mando um lembrete 3h antes — se precisar remarcar, responde aqui mesmo.',
  },
];

export const darkChat = [
  { from: 'cliente' as const, text: 'Preciso mudar meu horário de sábado, dá pra passar pra domingo?' },
  {
    from: 'ia' as const,
    text: 'Oi, Marcos! Domingo a gente não abre. Sábado tenho 09:00 ou 18:20 com o Léo, e sexta às 19:00. Alguma serve?',
  },
  { from: 'cliente' as const, text: 'Sexta 19h então. E o plano mensal, dá pra pagar no crédito?' },
  {
    from: 'ia' as const,
    text: 'Remarcado pra sexta, 19:00 com o Léo. Sobre o plano eu vou chamar o Rafael aqui, ele te responde ainda hoje.',
  },
];

/** Day-schedule preview shown in the hero (columns: Rafael, Léo, Kaio). */
export const heroAgenda: Array<{ time: string; cells: Array<{ label: string; sub?: string } | null> }> = [
  { time: '14:30', cells: [{ label: 'Corte · Diego M.' }, { label: 'Barba · Tiago' }, null] },
  { time: '15:30', cells: [{ label: 'Corte + barba · Diego', sub: 'via WhatsApp' }, null, { label: 'Corte · Bruno' }] },
  { time: '16:30', cells: [null, { label: 'Pigmentação · Ivan' }, { label: 'Corte · Assinante' }] },
  { time: '17:00', cells: [null, { label: 'Corte · Sérgio' }, null] },
];

export const heroAgendaBarbers = ['Rafael', 'Léo', 'Kaio'];

export const navLinks = [
  { href: '#funcionalidades', label: 'Funcionalidades' },
  { href: '#whatsapp', label: 'WhatsApp com IA' },
  { href: '#como-funciona', label: 'Como funciona' },
  { href: '#planos', label: 'Planos' },
  { href: '#faq', label: 'FAQ' },
];
