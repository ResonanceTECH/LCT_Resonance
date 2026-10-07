# LCT Resonance — Frontend

Клиент обратного рекрутинга (кандидат ↔ работодатель) по `TECH_SPEC.md`.  
UI-kit: [`UI_KIT.md`](./UI_KIT.md).

## Stack

- React 19 + TypeScript + Vite
- React Router 7, TanStack Query, React Hook Form + Zod
- MSW mocks (`VITE_USE_MOCKS=true`)

## Run

```bash
npm install
npm run dev
```

Demo accounts (password `demo1234`):

- `candidate@demo.ru`
- `employer@demo.ru`
- `admin@demo.ru`

## Env

```
VITE_API_BASE_URL=/api
VITE_USE_MOCKS=true
```

Для реального Backend: `VITE_USE_MOCKS=false` и `VITE_API_BASE_URL=https://...`.
