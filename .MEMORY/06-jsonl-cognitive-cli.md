# Memory Card: JSONL Cognitive CLI

Goal: provide one isolated CLI that can read a JSON or JSONL file and return a
structured cognitive summary.

Tool:
- `tools/nx-cognize/main.py`

Responsibility:
- read source file
- extract user-like messages and useful text snippets
- run provider fallback chain
- load reusable prompt instructions from YAML
- return strict JSON only on stdout

Output focus:
- first user message
- last user message
- `intent_steps_ru` for friendly Russian semantic steps
- 3-7 short intent bullets
- short summary without ellipsis
- key topics

Isolation rules:
- do not import `backend/`
- do not import `frontend/`
- keep provider commands declarative in `providers.json`
- keep prompt bodies in `tools/nx-cognize/prompts/*.yaml`
