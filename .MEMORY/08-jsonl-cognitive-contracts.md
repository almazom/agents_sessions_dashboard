# Memory Card: JSONL Cognitive Contracts

Contracts:
- `jsonl-cognitive-request@1.1.0`
- `jsonl-cognitive-result@1.1.0`

Important result fields:
- `meta.prompt_id`
- `meta.selected_provider`
- `meta.provider_attempts`
- `source.user_message_count`
- `summary.first_user_message`
- `summary.last_user_message`
- `summary.intent_bullets`
- `summary.intent_steps_ru`

Rules:
- intent bullets must be short, ideally 3-5 words
- `intent_steps_ru` should read like semantic steps, not raw quotes
- summary text should not end with `...`
- provider output must be parsed into strict JSON before returning
