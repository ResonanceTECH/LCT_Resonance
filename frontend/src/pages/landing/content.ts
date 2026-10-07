export const landingHero = {
  brand: 'LCT Resonance',
  brandTagline: 'IT-найм с доказанными навыками',
  label: 'Resonance для IT-найма',
  lines: ['Resonance', 'для IT-найма'] as const,
  subtitle:
    'Кандидат с ФСП. Работодатель с Match Score. Предложение с зарплатой — контакты только после accept.',
  primaryCta: { label: 'Начать', to: '/register' },
  secondaryCta: { label: 'Demo-вход', to: '/login' },
  scrollLabel: 'Листай',
  scrollLabelMouse: 'Прокрутите вниз',
  scrollTarget: '#hero-continue',
};

export const landingDock = [
  { id: 'how-it-works', label: 'Как работает', href: '#how-it-works' },
  { id: 'roles', label: 'Роли', href: '#roles' },
  { id: 'features', label: 'Возможности', href: '#features' },
] as const;

export const landingHowItWorks = {
  id: 'how-it-works',
  label: 'Как это работает',
  steps: [
    {
      id: 'step-01',
      number: '01',
      title: 'Профиль + ФСП',
      description: 'Кандидат заполняет стек и синхронизирует подтверждённые достижения из ФСП.',
    },
    {
      id: 'step-02',
      number: '02',
      title: 'Talent Pool',
      description: 'Работодатель фильтрует пул и видит Match Score по конкретной вакансии.',
    },
    {
      id: 'step-03',
      number: '03',
      title: 'Оффер с зарплатой',
      description: 'Отклик только через предложение: вилка и условия до обмена контактами.',
    },
    {
      id: 'step-04',
      number: '04',
      title: 'Accept → контакты',
      description: 'После принятия Backend открывает контакты. До accept — тишина.',
    },
  ],
};

export const landingRoles = {
  id: 'roles',
  label: 'Для кого',
  titleLines: ['Две роли', 'один сигнал'],
  cards: [
    {
      id: 'candidate',
      title: 'Кандидат',
      subtitle: 'Покажи доказанный стек,\nа не только резюме.',
      features: ['профиль и навыки', 'ФСП-верификация', 'тесты и Career Passport'],
    },
    {
      id: 'employer',
      title: 'Работодатель',
      subtitle: 'Найди match по вакансии\nбез шума контактов.',
      features: ['Talent Pool', 'Match Score + причины', 'shortlist и офферы'],
    },
  ],
};

export type FeaturesMode = 'candidate' | 'employer';

export const landingFeatures = {
  id: 'features',
  label: 'Возможности',
  titleLines: ['Как работает', 'платформа'],
  modes: [
    { id: 'candidate' as const, label: 'Кандидат' },
    { id: 'employer' as const, label: 'Работодатель' },
  ],
  views: {
    candidate: {
      subtitle: 'Собери профиль, подтяни ФСП, пройди тесты — получи офферы с цифрами.',
      steps: [
        {
          id: 'profile',
          number: '1',
          title: 'Собери профиль',
          description: 'Стек, грейд, ожидания по зарплате и формату работы.',
        },
        {
          id: 'fsp',
          number: '2',
          title: 'Синхронизируй ФСП',
          description: 'Подтверждённые достижения отделены от self-reported навыков.',
        },
        {
          id: 'tests',
          number: '3',
          title: 'Пройди тесты',
          description: 'Результаты идут в Match Score — без ручного «украшательства».',
        },
        {
          id: 'offers',
          number: '4',
          title: 'Получай офферы',
          description: 'Зарплата и условия до accept. Контакты — только после согласия.',
        },
      ],
    },
    employer: {
      subtitle: 'Фильтруй Talent Pool, сравнивай кандидатов и отправляй офферы с вилкой.',
      steps: [
        {
          id: 'vacancy',
          number: '1',
          title: 'Опубликуй вакансию',
          description: 'Требования к стеку, грейду и компенсация как часть сигнала.',
        },
        {
          id: 'pool',
          number: '2',
          title: 'Смотри Talent Pool',
          description: 'Match Score и причины match/mismatch по каждому кандидату.',
        },
        {
          id: 'compare',
          number: '3',
          title: 'Сравни shortlist',
          description: 'Радар навыков и ФСП рядом — без переключения вкладок.',
        },
        {
          id: 'offer',
          number: '4',
          title: 'Отправь оффер',
          description: 'Контакты открываются только после accept на стороне кандидата.',
        },
      ],
    },
  },
};

export const landingCta = {
  id: 'cta',
  title: 'Найм без\nхолодных контактов',
  subtitle: 'Зарегистрируйся как кандидат или работодатель — демо-аккаунты уже в форме входа.',
  cta: { label: 'Начать', to: '/register' },
};
