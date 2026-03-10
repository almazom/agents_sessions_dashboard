# Memory Card: Latest Session Shell Tips

Goal: quickly find the latest canonical session file from each AI provider root without manually traversing nested folders.

Core rule:

- prefer `find ... -printf '%T@ %p\n' | sort -nr | head -n 1`
- avoid `find ... | xargs ls -lt | head -n 1` because it often prints `terminated by signal 13`
- if only the path is needed, append `| cut -d' ' -f2-`

Gemini caveat:

- Gemini is the main exception in this set
- look in `~/.gemini/tmp`, not in a `sessions` root
- look for `session-*.json`, not `jsonl`
- avoid broad `*.json` scans if you want only canonical chat sessions

Canonical provider commands:

## Codex

```bash
find ~/.codex/sessions -type f -name 'rollout-*.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1
```

## Claude

```bash
find ~/.claude/projects -type f -name '*.jsonl' ! -path '*/subagents/*' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1
```

## Pi

```bash
find ~/.pi/agent/sessions -type f -name '*.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1
```

## Qwen

```bash
find ~/.qwen/projects -type f -path '*/chats/*.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1
```

## Kimi

Use `wire.jsonl` as the canonical session artifact.

```bash
find ~/.kimi/sessions -type f -name 'wire.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1
```

## Gemini

Gemini currently stores chat session artifacts as `.json`, not `.jsonl`.
Gemini also keeps them under `~/.gemini/tmp`.

```bash
find ~/.gemini/tmp -type f -path '*/chats/session-*.json' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1
```

Path-only variants:

```bash
find ~/.codex/sessions -type f -name 'rollout-*.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-
find ~/.claude/projects -type f -name '*.jsonl' ! -path '*/subagents/*' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-
find ~/.pi/agent/sessions -type f -name '*.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-
find ~/.qwen/projects -type f -path '*/chats/*.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-
find ~/.kimi/sessions -type f -name 'wire.jsonl' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-
find ~/.gemini/tmp -type f -path '*/chats/session-*.json' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-
```

Human-readable variant pattern:

```bash
find <ROOT> -type f <MATCH> -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null | sort -r | head -n 1
```

Relation to CLI:

- these shell one-liners are the low-level reference
- `tools/nx-collect/nx-collect --latest` should agree with them for the same provider roots and canonical patterns
