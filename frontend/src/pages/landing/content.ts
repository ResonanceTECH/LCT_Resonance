export const landingHero = {
  brand: 'FSP Talent',
  brandTagline: 'Федерация спортивного программирования',
  label: 'Найм, где навык уже доказан',
  headline: 'Найм, где навык уже доказан',
  subtitle:
    'Не обещания из резюме — а ФСП, тесты и оценка соответствия. Вилка до контактов. Контакты — только после согласия.',
  primaryCta: { label: 'Начать', to: '/register' },
  secondaryCta: { label: 'Демовход', to: '/login' },
  scrollLabel: 'Как это работает',
  scrollTarget: '#how-it-works',
  heroImage: '/auth-hero.png',
};

export const landingDock = [
  { id: 'how-it-works', label: 'Как работает', href: '#how-it-works' },
  { id: 'roles', label: 'Роли', href: '#roles' },
  { id: 'features', label: 'Возможности', href: '#features' },
] as const;

export const landingHowItWorks = {
  id: 'how-it-works',
  label: 'Как это работает',
  title: 'Четыре шага до сигнала',
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
      title: 'Пул кандидатов',
      description: 'Работодатель фильтрует пул и видит оценку соответствия по конкретной вакансии.',
    },
    {
      id: 'step-03',
      number: '03',
      title: 'Предложение с зарплатой',
      description: 'Отклик только через предложение: вилка и условия до обмена контактами.',
    },
    {
      id: 'step-04',
      number: '04',
      title: 'Согласие → контакты',
      description: 'После согласия система открывает контакты. До этого — тишина.',
    },
  ],
};

export const landingRoles = {
  id: 'roles',
  label: 'Для кого',
  title: 'Две роли — один сигнал',
  cards: [
    {
      id: 'candidate',
      title: 'Кандидат',
      subtitle: 'Покажи доказанный стек, а не только резюме.',
      features: ['Профиль и навыки', 'Достижения ФСП', 'Тесты и карьерный паспорт'],
    },
    {
      id: 'employer',
      title: 'Работодатель',
      subtitle: 'Найди совпадение по вакансии без шума контактов.',
      features: ['Пул кандидатов', 'Оценка соответствия и причины', 'Избранное и предложения'],
    },
  ],
};

export type FeaturesMode = 'candidate' | 'employer';

export const landingFeatures = {
  id: 'features',
  label: 'Возможности',
  title: 'Как работает платформа',
  modes: [
    { id: 'candidate' as const, label: 'Кандидат' },
    { id: 'employer' as const, label: 'Работодатель' },
  ],
  views: {
    candidate: {
      subtitle: 'Собери профиль, подтяни ФСП, пройди тесты — получи предложения с цифрами.',
      steps: [
        {
          id: 'profile',
          number: '1',
          title: 'Собери профиль',
          description: 'Стек, уровень, ожидания по зарплате и формату работы.',
        },
        {
          id: 'fsp',
          number: '2',
          title: 'Синхронизируй ФСП',
          description: 'Подтверждённые достижения отделены от заявленных навыков.',
        },
        {
          id: 'tests',
          number: '3',
          title: 'Пройди тесты',
          description: 'Результаты идут в оценку соответствия — без ручного «украшательства».',
        },
        {
          id: 'offers',
          number: '4',
          title: 'Получай предложения',
          description: 'Зарплата и условия до согласия. Контакты — только после принятия.',
        },
      ],
    },
    employer: {
      subtitle: 'Фильтруй пул кандидатов, сравнивай и отправляй предложения с вилкой.',
      steps: [
        {
          id: 'vacancy',
          number: '1',
          title: 'Опубликуй вакансию',
          description: 'Требования к стеку, уровню и компенсация как часть сигнала.',
        },
        {
          id: 'pool',
          number: '2',
          title: 'Смотри пул кандидатов',
          description: 'Оценка соответствия и причины совпадения или расхождения по каждому.',
        },
        {
          id: 'compare',
          number: '3',
          title: 'Сравни избранное',
          description: 'Радар навыков и ФСП рядом — без переключения вкладок.',
        },
        {
          id: 'offer',
          number: '4',
          title: 'Отправь предложение',
          description: 'Контакты открываются только после согласия кандидата.',
        },
      ],
    },
  },
};

export const landingCta = {
  id: 'cta',
  title: 'Найм без холодных контактов',
  subtitle: 'Зарегистрируйся как кандидат или работодатель — демоаккаунты уже в форме входа.',
  cta: { label: 'Начать', to: '/register' },
};

export type FooterLink =
  | { label: string; to: string }
  | { label: string; href: string; external?: boolean };

export const landingFooter = {
  brand: 'FSP Talent',
  tagline: 'Найм IT-специалистов с подтверждёнными компетенциями',
  description:
    'Платформа для кандидатов и работодателей на базе визуальной айдентики Федерации спортивного программирования.',
  columns: [
    {
      title: 'Платформа',
      links: [
        { label: 'Как работает', href: '#how-it-works' },
        { label: 'Возможности', href: '#features' },
        { label: 'Начать', to: '/register' },
        { label: 'Демовход', to: '/login' },
      ] satisfies FooterLink[],
    },
    {
      title: 'Роли',
      links: [
        { label: 'Кандидат', href: '#roles' },
        { label: 'Работодатель', href: '#roles' },
        { label: 'Карьерный паспорт', to: '/p/passport-cand-1' },
      ] satisfies FooterLink[],
    },
    {
      title: 'Ресурсы',
      links: [
        { label: 'Дизайн-система', to: '/ui-kit' },
        { label: 'Брендбук ФСП', href: 'https://fsp-russia.ru/press/brandbook/', external: true },
        { label: 'Сайт ФСП', href: 'https://fsp-russia.ru/', external: true },
      ] satisfies FooterLink[],
    },
  ],
  meta: {
    copyright: '© 2026 FSP Talent',
    note: 'Разработано командой Резонанс',
  },
};
