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

Terminal view:
- use `①②③④⑤⑥⑦`
- keep the pretty mode compact and glanceable
