# Memory Card: Session Collect CLI

Goal: locate canonical session artifacts across providers before any cognitive or UI layer works with them.

Current tool:

- `tools/nx-collect/nx-collect`

Current mode:

- `latest`

Rule:

- `latest` can return only one global match
- `latest` should not expose a `--limit` flag
- the JSON response for `latest` should expose one `latest` object, not `matches` or `provider_latest` arrays

Why it exists:

- find the single newest canonical session file across providers
- return the exact source path
- expose human-readable recency and activity state
- attach semantic intent steps through `nx-cognize`
- provide a stable normalized JSON response for later filters and cards

Latest runtime:

- `latest` should be coordinated by one isolated CLI process
- it should launch provider-specific raw shell finder jobs in parallel
- it should not use AI subagents for provider probing
- for `Codex`, AI subagents can create their own rollout files and distort `latest`
- default timezone should be `Europe/Moscow`

Canonical provider patterns:

- `codex`: `~/.codex/sessions/**/rollout-*.jsonl`
- `claude`: `~/.claude/projects/**/*.jsonl` excluding `subagents/`
- `gemini`: `~/.gemini/tmp/**/chats/session-*.json`
- `qwen`: `~/.qwen/projects/**/chats/*.jsonl`
- `pi`: `~/.pi/agent/sessions/**/*.jsonl`
- `kimi`: `~/.kimi/sessions/**/wire.jsonl`

Gemini caveat:

- Gemini is different from the other providers
- its canonical session artifacts currently live under `~/.gemini/tmp`
- its chat session files are `session-*.json`, not `jsonl`
- broad `*.json` scans under `~/.gemini/` will catch non-session files like settings, projects, and logs

Activity windows:

- `live`: last modified within 10 minutes by default
- `active`: last modified within 60 minutes by default
- `idle`: older than active window

CLI examples:

```bash
tools/nx-collect/nx-collect --latest
tools/nx-collect/nx-collect latest
tools/nx-collect/nx-collect --latest --project ~/zoo/agents_sessions_dashboard
tools/nx-collect/nx-collect --latest --providers codex,qwen
tools/nx-collect/nx-collect --latest --timezone Europe/Moscow
```

Rule:

- treat canonical session artifacts as the source of truth
- do not mix cache/config JSON files into session collection output
- if cognitive enrichment fails, keep the latest result and mark it as local fallback
- `--project` should narrow latest lookup before any downstream cognitive tool runs
