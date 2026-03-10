# Idea Generator Client

Frontend application for the Idea Generator monorepo.

## Stack

- React `19`
- TypeScript
- Vite
- Tailwind CSS `4`
- `shadcn` UI config with the `radix-nova` style

## Development server

The Vite dev server runs on:

- `http://localhost:3000`

API requests to `/api` are proxied to the FastAPI backend at `http://localhost:8000`.

## Scripts

From `packages/client`:

```bash
bun run dev
bun run build
bun run lint
bun run preview
```

## Project structure

```text
packages/client/
├── src/
│   ├── components/ui/   # reusable design-system primitives
│   ├── lib/             # shared utilities
│   ├── App.tsx          # app entry component
│   └── main.tsx         # React bootstrap
├── public/
├── vite.config.ts
└── components.json      # shadcn/ui configuration
```

## Design-system guidance

The app already includes reusable UI primitives in `src/components/ui/`.
When adding new screens or features, prefer those components over raw repeated markup so the UI stays consistent and easier to evolve.

## Path aliases

The Vite config exposes the `@` alias for `src`:

- `@/components`
- `@/lib`
- `@/components/ui`

## Build output

Production assets are generated into `dist/` when running:

```bash
bun run build
```

## Related docs

- monorepo overview: `../../README.md`
- backend API docs: `../server/README.md`