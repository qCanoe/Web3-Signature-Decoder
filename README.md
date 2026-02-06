# Signature Decoder v2

Single-core TypeScript monorepo for signature and transaction analysis.

## Structure

- `packages/core-schema`: v2 request/result schemas + shared types
- `packages/core-knowledge`: validated knowledge JSON loader
- `packages/core-llm`: LLM providers (OpenAI and gateway)
- `packages/core-engine`: normalize -> parse -> enrich -> llm -> risk -> dto
- `packages/core-renderers`: Snap/UI renderers for `AnalysisResultV2`
- `packages/test-fixtures`: golden fixtures
- `packages/test-harness`: unit/contract/integration tests
- `apps/snap`: MetaMask Snap using `core-engine`
- `apps/test-api`: minimal API (`/v2/analyze`, `/v2/health`, `/v2/fixtures/validate`)
- `apps/test-web`: minimal web shell for testing and replaying fixtures

## Quick start

```bash
npm install
npm run build
npm run test
```

Run test API and web shell:

```bash
npm run dev:test-api
npm run dev:test-web
```

## Environment

Copy `.env.example` to `.env` and set required values.

- `OPENAI_API_KEY`: required for test-api reasoning
- `OPENAI_MODEL`: default `gpt-4o-mini`
- `OPENAI_TIMEOUT_MS`: request timeout
- `TEST_API_PORT`: API port, default `4000`
- `TEST_WEB_PORT`: web shell port, default `4173`
- `SNAP_GATEWAY_URL`: endpoint that Snap calls for LLM reasoning (defaults to test-api gateway)
- `SNAP_GATEWAY_TOKEN`: optional bearer token for gateway auth

## Legacy code

Previous Python/Snap implementations are kept under `legacy-*` folders and are not used by v2 runtime.
