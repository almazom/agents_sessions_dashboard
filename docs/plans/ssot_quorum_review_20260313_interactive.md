# SSOT Quorum Review

Date: 2026-03-13
Board: `docs/plans/ssot_kanban_20260313_062127.json`
Scope: compare SSOT task state vs implemented code and test evidence for the interactive-session initiative

## Review Setup

Six parallel review angles were used:

1. SSOT board integrity
2. Backend runtime/control implementation
3. Route/frontend tranche readiness
4. Verification and deploy evidence
5. Security, ownership, and inbound action safety
6. Product/UX alignment

Some subagents reported partial shell limitations, but quorum still converged on the same main gaps.

## Quorum Verdict

The backend helper foundation for interactive runtime/control is materially real and code-backed.

The project is not at "all tasks done in json".

The project is not yet at a browser-visible or published-proof completion state for the Kimi-web-like interactive continuation goal.

## Consensus Findings

### 1. SSOT integrity is currently unreliable

Critical finding:

- `TASK-048` is internally inconsistent in [docs/plans/ssot_kanban_20260313_062127.json](/home/pets/zoo/agents_sessions_dashboard/docs/plans/ssot_kanban_20260313_062127.json): its visible `status` is `backlog`, while its history says it already reached `done`.

Additional integrity finding:

- The board is not fully complete. Open backlog cards remain from `TASK-034` onward, including `TASK-034` through `TASK-046`, `TASK-048`, and `TASK-050` through `TASK-054`.
- There is also at least one earlier non-done item with `status: investigated`.

Impact:

- The JSON cannot currently be treated as strict execution truth without repair.
- Any automation that picks the next task from status alone can make the wrong decision.

### 2. Backend control groundwork is real, but helper-level

Quorum agrees the recent completed control tranche is real and backed by code/tests:

- [backend/api/interactive_actions.py](/home/pets/zoo/agents_sessions_dashboard/backend/api/interactive_actions.py)
- [backend/api/interactive_supervisor.py](/home/pets/zoo/agents_sessions_dashboard/backend/api/interactive_supervisor.py)
- [backend/api/interactive_store.py](/home/pets/zoo/agents_sessions_dashboard/backend/api/interactive_store.py)
- [backend/api/interactive_events.py](/home/pets/zoo/agents_sessions_dashboard/backend/api/interactive_events.py)
- [tests/interactive/test_task_024.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_024.py)
- [tests/interactive/test_task_025.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_025.py)
- [tests/interactive/test_task_026.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_026.py)
- [tests/interactive/test_task_027.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_027.py)
- [tests/interactive/test_task_028.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_028.py)
- [tests/interactive/test_task_029.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_029.py)
- [tests/interactive/test_task_030.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_030.py)
- [tests/interactive/test_task_031.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_031.py)
- [tests/interactive/test_task_032.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_032.py)
- [tests/interactive/test_task_033.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_033.py)
- [tests/interactive/runtime_control_bundle.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/runtime_control_bundle.py)
- [tests/interactive/test_task_049.py](/home/pets/zoo/agents_sessions_dashboard/tests/interactive/test_task_049.py)

What this proves:

- ownership lock rules
- supervisor start/stop lifecycle
- event normalization
- fallback event rendering
- prompt submit, cancel/interrupt, and waiting-response action shapes
- inbound action validation
- a milestone bundle proving these helpers compose coherently

What this does not yet prove:

- a real `/interactive` route
- browser shell behavior
- replay-to-live UI handoff in the browser
- deployed interactive continuation

### 3. The route/frontend tranche is still largely unimplemented

Quorum agrees the next real product step is `TASK-034`, not more helper refinement.

Main gaps:

- no proven dedicated `/interactive` route loader
- no proven interactive page shell
- no proven frontend state machine or reducer for replay/live flow
- no proven direct GET journey into interactive mode
- no proven CTA and return-path UX between dossier page and interactive page

Recommendation from quorum:

- keep `TASK-034` as the next active implementation card
- split route and frontend concerns more aggressively if any open card mixes too much:
  - route loader and capability gating
  - interactive shell/state machine
  - replay/live handoff UX
  - prompt/action roundtrips
  - published browser proof

### 4. Verification is still below user-visible confidence

Quorum agrees current confidence is not 95% for the actual intended feature.

Why:

- completed proof today is mostly unit/helper and synthetic bundle evidence
- published/browser/Playwright proof for the interactive route is still backlog
- repo rules require published verification for major user-visible changes

Specific missing proof types:

- local browser E2E for interactive route
- published browser E2E for interactive route
- route separation proof between dossier page and interactive page
- degraded-state proof on real runtime failures
- reconnect/restart proof on the published stack

### 5. Security is only partially proven

Positive finding:

- helper-level inbound action validation is explicit and reasonably strict in [backend/api/interactive_actions.py](/home/pets/zoo/agents_sessions_dashboard/backend/api/interactive_actions.py)

Remaining gaps called out by quorum:

- no route-level auth proof yet
- no explicit CSRF/origin proof for interactive write actions
- no request-boundary or stale-event protection proof
- no explicit single-writer lease proof at real route level
- replay/live isolation is still mostly architectural intent, not route-enforced evidence

### 6. Product/UX goal is still only partially covered

Quorum agrees the plan is technically plausible but under-specifies the final user-facing experience.

Main UX gaps:

- dossier page vs interactive page separation is not frozen as a product rule
- duplication prevention between evidence blocks and operational blocks is not explicit enough
- commit readability and non-duplication are not yet proven as preserved invariants
- degraded interactive states need explicit UX acceptance criteria
- the entry journey into interactive mode needs clearer definition:
  - CTA location
  - preview/tail before live mode
  - session identity confirmation
  - return path back to dossier

## Cross-Angle Synthesis

The six review angles converge on one key distinction:

- the backend control substrate is advancing correctly
- the shipped product goal is still open

In other words:

- done helper cards are real
- done helper cards do not mean the interactive feature is done

## Concrete Improvement Actions

### Immediate corrections

1. Repair `TASK-048` in [docs/plans/ssot_kanban_20260313_062127.json](/home/pets/zoo/agents_sessions_dashboard/docs/plans/ssot_kanban_20260313_062127.json) so `status`, `history`, and `execution_state` agree.
2. Add a board-consistency checker that rejects impossible combinations such as:
   - `status: backlog` with history ending in `done`
   - `status: done` with `tdd_passed: false`
   - `status: done` with empty or misleading completion artifacts
3. Normalize `artifacts_of_completion` for done reproduce gates so both green and broken-path proof are recorded consistently.

### Next implementation order

1. Start `TASK-034` as the thinnest real backend `/interactive` route over the existing helper seams.
2. Add route-level integration tests immediately after the loader lands.
3. Move into interactive page shell/state machine work.
4. Add route separation and duplication-prevention proof.
5. Finish Playwright and published verification before claiming user-visible completion.

### Suggested SSOT expansions

Quorum suggested adding or sharpening cards for:

- dossier vs interactive IA contract
- interactive entry and return UX
- non-duplication rule for commit/evidence blocks
- strict route-level auth and action-envelope security
- ownership/writer lease and reconnect rules
- published interactive-route canary verification
- board consistency auditing

## Confidence Statement

High confidence:

- recent backend runtime/control cards are genuinely implemented
- the board is not fully complete
- `TASK-048` currently needs repair
- the interactive browser feature is not yet complete

Moderate confidence:

- the open frontend/route tranche should likely be split more finely
- UX/IA rules need to be made more explicit in the SSOT

## Recommended Use Of This Report

Use this file as the improvement checklist before trusting the SSOT as closed-loop truth for the interactive initiative.

Short version:

1. fix board integrity first
2. then build the real `/interactive` route
3. then prove it in browser and on the published URL
