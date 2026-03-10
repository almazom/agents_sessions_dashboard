# Memory Card: extract-intent CLI

Goal:
- give the user one direct CLI for semantic intent extraction over one session file

Tool:
- `tools/extract-intent/extract-intent`
- convenience wrapper: `./extract-intent`

Rules:
- default output is strict JSON
- `--pretty` is the human terminal mode
- always use `intent-vector-ru` prompt through `nx-cognize`
- steps should be 3-7 items and easy to read in Russian
- do not echo the source file path in the result payload or pretty output
- `--project` is a thin orchestration mode: first resolve latest session via `nx-collect`, then run normal intent extraction
- `--provider` means source provider
- `--processing-provider` means the AI provider that generates the semantic summary

Terminal view:
- use `①②③④⑤⑥⑦`
- keep the pretty mode compact and glanceable

Examples:

```bash
extract-intent --input /full/path/to/session.jsonl --pretty
extract-intent --project ~/zoo/agents_sessions --pretty
extract-intent --project ~/zoo/agents_sessions --provider gemini --processing-provider gemini
extract-intent --project ~/zoo/agents_sessions --providers codex,claude,gemini,qwen,pi,kimi
```
