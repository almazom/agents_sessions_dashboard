# Interactive Transport ADR v1

Status: accepted
Date: 2026-03-13

Context

The browser continuation route needs one explicit transport decision after the
fixture, matrix, and probe tasks. The repo must stop mixing three different
surfaces into one promise:

- `codex app-server` is the primary continuation contract for a managed backend runtime
- `codex exec --experimental-json` is a raw streamed backend surface
- `@openai/codex-sdk` is a Node wrapper over raw exec, not a browser transport

Decision

primary_browser_transport: codex_app_server
fallback_policy: raw_exec_and_sdk_are_backend_only_fallbacks
sdk_role: node_sidecar_adapter
interactive_route: /sessions/[harness]/[id]/interactive
non_goals: direct_browser_sdk, pty_scraping, qemu_or_browser_vm

Decision details

- The browser-facing interactive route will attach to a backend-owned Codex app-server flow.
- Raw exec stays available for probes, fixture seeding, and backend-side event debugging.
- The TypeScript SDK is allowed as a backend sidecar adapter where it helps with streaming, resume, or event normalization.
- The SDK must not be presented as a direct browser transport for v1.

Fallback policy

- If the app-server path is unavailable, the system may use raw exec or the SDK only behind a backend owner.
- Any raw exec or SDK fallback must preserve the same honest browser contract: no fake terminal ownership and no browser-only continuation promise.
- Fallbacks are support tooling for backend orchestration, not a change to the primary browser transport choice.

Non-goals for v1

- No PTY scraping transport.
- No QEMU, browser VM, or fake terminal emulation as the session continuation base.
- No direct client-side SDK execution in the browser.

Consequences

- Backend tasks should implement app-server-aligned lifecycle, resume, and status behavior first.
- Frontend tasks can treat `/sessions/[harness]/[id]/interactive` as the stable GET entrypoint.
- Tests may keep using raw exec and SDK helpers, but the product language must stay anchored to the app-server choice.
