# AGENTS.md

## Cursor Cloud specific instructions

Web3 Signature Decoder is a TypeScript **npm-workspaces monorepo** (Node `>=20.11`). The shared logic lives in `packages/@sd/core-*`; the runnable apps live in `apps/`. See `README.md` for the full architecture, API routes, and env var table.

### Build is required before running apps or tests (non-obvious)
The apps and tests import the **compiled `dist/` output** of the `@sd/*` workspace packages (each package's `main` is `dist/index.js`), not their TypeScript source. So on a fresh checkout you MUST build the library packages before `dev`/`test` will work. The startup update script already runs the library builds (`@sd/core-schema`, `core-knowledge`, `core-llm`, `core-engine`, `core-renderers`, `test-fixtures`, `test-harness`); if you add/checkout a fresh tree yourself, rebuild them (dependency order: `core-schema` first). The dev servers themselves run via `tsx` on their own `src/`, so only the imported `@sd/*` libraries need building, not the apps.

### Port mismatch gotcha (test-api vs test-web)
`apps/test-api` defaults to `TEST_API_PORT=4005` in code, but `apps/test-web` (and the README) default the browser API base to `http://localhost:4000`. To make the test-web UI work against the API out of the box, start the API on port 4000: `TEST_API_PORT=4000 npm run dev:test-api`.

### Running the services (dev mode, from repo root)
- `TEST_API_PORT=4000 npm run dev:test-api` — Express REST API (`/v2/health`, `/v2/analyze`, `/v2/fixtures/validate`, `/v2/reason`).
- `npm run dev:test-web` — browser test shell on `http://localhost:4173` (select a fixture → `POST /v2/analyze`).
- `npm run dev:site` — landing / Snap-init page on `http://localhost:8000`.
- `npm run dev:snap` — MetaMask Snap watcher (`mm-snap watch`); needs MetaMask Flask in a real browser to fully exercise.
- `npm run dev` runs test-api + snap + site together (note: it starts test-api on its 4005 default, so point test-web at 4005 or run test-api separately on 4000).

### LLM / OpenAI behavior without a key (expected, not a bug)
There is no `OPENAI_API_KEY` by default and no `.env.example` in the repo (despite the README mention). With no key the engine is **fail-closed**:
- Benign requests (e.g. SIWE login) return `decision.value: "error"` with `policyReason: "analysis_unavailable"`.
- Requests with critical knowledge signals (`infinite_allowance`, `malicious_address_hit`, `malicious_domain_hit`, `phishing_domain`) still deterministically return `decision.value: "block"` with `policyReason: "high_risk"`.
- Consequently `POST /v2/fixtures/validate` returns `pass: false` (fixtures expecting `allow` get `error`). This is expected without a key.
To exercise the full LLM path and get `allow` decisions on benign fixtures, `OPENAI_API_KEY` must be set (see env configuration below).

### Env configuration (Cloud Agent)
Config precedence is **injected `process.env` (Cursor Secrets) > workspace-root `.env`** — `apps/test-api` loads `.env` via dotenv, which does NOT override already-set env vars. Full variable list is in `README.md`.
- Durable / cross-VM values (e.g. `OPENAI_API_KEY`, `OPENAI_MODEL`, `SNAP_GATEWAY_TOKEN`): set them as **Cursor Secrets** — they are injected as env vars into every new VM. A workspace-root `.env` is git-ignored and does NOT persist to a fresh VM, so don't rely on it for cross-run config. Do not set env vars in the startup update script.
- Model selection: `OPENAI_MODEL` (default `gpt-5.2` from `apps/test-api`). Note some newer models only accept the default `temperature`, which is why the OpenAI request no longer hardcodes `temperature`.
- Start the API on port 4000 (see port gotcha above): `TEST_API_PORT=4000 npm run dev:test-api`.

### Lint / test / build
- No dedicated `lint` script and no committed ESLint/Prettier config; the effective static check is the strict-mode TypeScript build. `npx prettier --check` reports diffs against Prettier defaults, but reformatting would rewrite existing source — do not run `--write` as a "lint fix".
- Tests: `npm run test` (Vitest harness + Jest snap install test). Harness only: `npm run test:harness`.
- Build all (incl. snap): `npm run build`. Note `mm-snap build` (run by `npm run build` and `dev:snap`) rewrites `apps/snap/snap.manifest.json`'s `shasum`; that incidental change should not be committed.
- The `clean` npm scripts use PowerShell (`Test-Path`) syntax and fail on Linux/bash — delete `dist/` manually instead of `npm run clean`.

### Fixture request shape
`packages/test-fixtures/src/fixtures/*.json` wrap the request as `{ name, request, expected }`; the object to POST to `/v2/analyze` is the inner `request`. The inline fixtures in `apps/test-web/public/app.js` are already raw request objects.
