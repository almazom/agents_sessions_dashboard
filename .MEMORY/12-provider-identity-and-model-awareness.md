# Provider Identity And Model Awareness

Rule:
- provider name alone is not enough for session identity when one CLI shell can run different models.
- keep provider identity and model identity as separate fields whenever the source format allows it.

Important cases:
- `qwen`: capture the concrete model used when available.
- `claude`: capture Claude Code shell plus the actual model or upstream provider when available.
- `pi`: capture the concrete model identity when the runtime exposes it.
- `pi mino`: treat it as a model/runtime identity under the `pi` family, not as a separate top-level provider.
- `kimi`, `minimax`, and other multi-model shells: do not collapse everything into one provider label if the file reveals more detail.

Collector implication:
- `nx-collect` should prefer explicit fields such as `provider`, `shell`, `model`, and `upstream_provider` when parsers can recover them.
- provider-specific parsers should not throw model information away if it exists in JSON or JSONL artifacts.

UI implication:
- cards should eventually show `provider + model` instead of provider alone.
- filters should later support provider and model separately.
- logos and colors should map to the provider family, while text can show the specific model.
