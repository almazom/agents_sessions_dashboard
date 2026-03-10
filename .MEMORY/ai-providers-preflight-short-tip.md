# Memory Short Tip: AI Providers Preflight

Goal: run a fast one-line preflight before starting a longer provider session.

Rules:
- Run the provider preflight first and expect a one-word `ok` response.
- If preflight fails, do not start the longer runtime command.
- Use `cwd` mode for `gemini`, `qwen`, and `claude`.
- Use `at_file` mode for `pi`.
- Keep `pi` in no-tools mode.

Quick map:
- `gemini`: preflight `gemini -p "Ответь одним словом: ok.NOW TOOLS alowed"`; runtime `gemini --approval-mode yolo`; mode `cwd`; timeouts `45s / 600s`
- `qwen`: preflight `qwen -p "Ответь одним словом: ok.NOW TOOLS alowed"`; runtime `qwen --approval-mode yolo`; mode `cwd`; timeouts `45s / 600s`
- `pi`: preflight `pi --no-session --provider zai --model glm-5 --thinking off --no-tools -p "Ответь одним словом: ok"`; runtime `pi --print --no-tools --thinking high`; mode `at_file`; timeouts `45s / 600s`; special `deterministic, no-tools`
- `claude`: preflight `claude -p --model MiniMax-M2.5 --no-session-persistence "Ответь одним словом: ok.NOW TOOLS alowed"`; runtime `claude --approval-mode yolo`; mode `cwd`; timeouts `45s / 600s`; model `MiniMax-M2.5`
