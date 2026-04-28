# Frontend V2

Clean PatentIQ V2 frontend target.

This app replaces the old dashboard-shaped UI in [frontend_v1](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1) with a workspace-first V2 implementation.

## Purpose

Use this app for:

1. Portfolio V2
2. Family V2
3. Market Intelligence V2
4. Publication V2
5. Compare V2
6. Data Room V2

Do not add new V2 work to `frontend_v1`.

## API config

Set:

1. `NEXT_PUBLIC_API_BASE_URL`

Example:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Behavior:

1. local development may omit the variable and the client falls back to `http://localhost:8000`
2. production builds and runtime must set `NEXT_PUBLIC_API_BASE_URL`
3. if production is missing the variable, the app now fails fast instead of silently targeting localhost

## Local browser vs containerized browser

Normal local browser usage should keep:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`frontend_v2` already contains a small browser-bridge rewrite in [config.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/lib/config.ts):

1. if the page is opened from `host.docker.internal`,
2. and the API base is `localhost` or `127.0.0.1`,
3. the client rewrites the request host to `host.docker.internal`.

This is intended for MCP / containerized browser audits and should not require a separate frontend build.

Important:

1. this frontend rewrite alone is not enough,
2. the backend must also be reachable from the container path,
3. CORS must allow `http://host.docker.internal:3000` or the relevant frontend origin.

## Frontend run commands

Use Node 22 for this app. `frontend_v2` is now pinned to the 22.x line because the current Next 16 production build path is stable there and not stable on the newer ad hoc runtimes already present on this machine.

If you use `nvm`:

```bash
cd frontend_v2
nvm use
```

If you do not use `nvm`, make sure `node -v` resolves to a 22.x build before running `npm` scripts.

Use:

```bash
cd frontend_v2
npm run dev
```

for normal local-browser development. The default dev script now pins:

1. `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
2. `--hostname 127.0.0.1`
3. `--port 3000`
4. webpack as the current default dev bundler

This keeps the most common local path stable and reachable.

Use:

```bash
cd frontend_v2
npm run dev:turbo
```

if you explicitly want the Turbopack dev server instead of webpack.

If route compilation feels slow on the default Next 16 dev path, compare with:

```bash
cd frontend_v2
npm run dev:webpack
```

or:

```bash
cd frontend_v2
npm run dev:local:webpack
```

Use:

```bash
cd frontend_v2
npm run dev:mcp
```

for containerized browser / MCP validation. This binds the frontend on `0.0.0.0:3000` while keeping the API base compatible with the browser-bridge rewrite.

For the same MCP/browser flow with webpack, use:

```bash
cd frontend_v2
npm run dev:mcp:webpack
```

## Example env file

Create `.env.local` from this baseline:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Test coverage

Use:

```bash
cd frontend_v2
npm run test:e2e
```

This suite now covers:

1. smoke checks for `/`, `/portfolio`, `/market`, `/portfolio/[ownerId]`, and `/family/[familyId]`
2. portfolio drilldown smoke coverage for citations, technology, and forecast tab states
3. deterministic API mocks for portfolio and family workspaces
4. accessibility checks with `axe-core` for serious and critical violations on the same core routes and portfolio drilldown tabs

The Playwright setup targets the locally installed Chrome application and starts the built app automatically.

## Build reliability

`frontend_v2` no longer depends on `next/font/google` network fetches during build. The font token system now uses local font stacks so production builds and E2E runs remain reproducible in restricted environments.

The default production build now uses webpack:

```bash
cd frontend_v2
npm run build
```

This is intentional. On the current workspace, Next 16 Turbopack builds are materially slower than webpack in end-to-end production builds. If you want to compare or retest Turbopack, use:

```bash
cd frontend_v2
npm run build:turbo
```
