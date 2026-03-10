# Memory Card: Provider Fallback Chain

Goal: make one-shot cognitive operations reliable even when some AI CLIs are unavailable.

Default chain:
- `qwen`
- `gemini`
- `claude`
- `pi`
- `local`

Rules:
- run provider preflight probes in parallel when health is stale or a forced refresh is requested
- keep provider health in a local state file with last availability and latency
- reorder runtime attempts so the fastest recently available provider goes first
- stop at the first provider that returns valid JSON
- keep stdout clean for JSON
- send diagnostics to stderr

Provider notes:
- `qwen`, `gemini`, `claude`: cwd-style prompt execution
- `pi`: deterministic `--no-tools` mode
- `local`: last-resort non-LLM fallback that preserves output contract

State:
- default cache file: `tools/nx-cognize/provider-state.local.json`
- keep it out of git
