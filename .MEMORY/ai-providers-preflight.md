# Memory Card: AI Providers Preflight

Goal: verify that a provider CLI is available and responsive before starting a longer runtime session.

Rules:
- Always run the preflight command first.
- Expect the preflight to answer with a single word: `ok`.
- Start the runtime command only after preflight succeeds.
- Keep the provider-specific mode and timeout settings consistent.

## Gemini

Preflight:

```bash
gemini -p "Ответь одним словом: ok.NOW TOOLS alowed"
```

Runtime:

```bash
gemini --approval-mode yolo
```

Settings:
- mode: `cwd`
- timeouts: `45s / 600s`

## Qwen

Preflight:

```bash
qwen -p "Ответь одним словом: ok.NOW TOOLS alowed"
```

Runtime:

```bash
qwen --approval-mode yolo
```

Settings:
- mode: `cwd`
- timeouts: `45s / 600s`

## Pi

Preflight:

```bash
pi --no-session --provider zai --model glm-5 --thinking off --no-tools -p "Ответь одним словом: ok"
```

Runtime:

```bash
pi --print --no-tools --thinking high
```

Settings:
- mode: `at_file`
- timeouts: `45s / 600s`
- special: `deterministic, no-tools`

## Claude

Preflight:

```bash
claude -p --model MiniMax-M2.5 --no-session-persistence "Ответь одним словом: ok.NOW TOOLS alowed"
```

Runtime:

```bash
claude --approval-mode yolo
```

Settings:
- mode: `cwd`
- timeouts: `45s / 600s`
- model: `MiniMax-M2.5`

Project-specific reminder:
- Use the preflight as a fast CLI sanity check.
- Keep `pi` isolated in no-tools mode.
- Keep the longer runtime invocation separate from the preflight command.
