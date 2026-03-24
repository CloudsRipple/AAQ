## Context

This handoff is the current working summary for the `AAQ` remediation/refactor effort.

Primary baseline:

- `docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md`

Supporting references:

- `docs/architecture/TOP_LEVEL_DESIGN_AI_ADVISORY.md`
- `docs/architecture/REFACTOR_BLUEPRINT_AI_ADVISORY.md`

Current date of this handoff: `2026-03-19`

## What Was Already Completed Before The Latest Cut

| Area | Status | Notes |
|---|---|---|
| `contracts / bootstrap / coordinator` skeleton | Done | `runtime/bootstrap.py`, `kernel/contracts.py`, `kernel/coordinator.py`, `advisory/contracts.py` were introduced as transitional anchors. |
| Entry-point cleanup | Done | `main.py` reduced to CLI entry; `app.py` turned into compatibility wrapper; `models/signals.py` now re-exports from `kernel/contracts.py`. |
| AI placeholder / AI-off parity foundation | Done | `LLM_BASE_URL` and `LLM_API_KEY` default to empty; gateway creation now respects placeholder mode; health checks no longer mark placeholder AI as hard failure. |
| Ultra placeholder behavior | Done | `ai/ultra.py` now runs in rule-only mode when AI is unconfigured; `on_news()` returns `None` in placeholder mode instead of forcing vector path initialization. |
| Runtime health behavior | Done | `DEGRADED` no longer blocks risk/execution; only `LOCKDOWN` blocks. |

## What Was Completed In The Latest Cut

This latest cut was focused on the Week 1 / P0 dependency chain:

`contracts -> bootstrap -> coordinator -> execution de-dup`

### Latest Completed Changes

| Item | Status | Files | Why it matters |
|---|---|---|---|
| `HighDecisionEvent` expanded into an execution-ready transitional contract | Done | `src/phase0/kernel/contracts.py` | `high.decision` can now carry execution-ready fields instead of only AI adjustment metadata. |
| `ExecutionIntentEvent` tightened to require execution-ready bracket/cost data | Done | `src/phase0/kernel/contracts.py` | `execution.intent` is now a real handoff object, not a partial reconstruction target. |
| Event-driven `HighEngine` now emits execution-ready `high.decision` | Done | `src/phase0/ai/high.py` | High now finalizes approved ultra signals through the old High rule kernel before publishing. |
| `ExecutionSubscriber` no longer performs second High evaluation | Done | `src/phase0/execution_subscriber.py` | This removes the major P0 violation where execution rebuilt a fake high event and called `evaluate_event()` again. |
| IBKR adapter made tolerant of approved payload / prebuilt signal shapes | Done | `src/phase0/ibkr_order_adapter.py` | Execution mapping now accepts execution-ready payloads directly. |
| Targeted regression tests added/updated | Done | `tests/test_event_driven_engines.py`, `tests/test_execution_subscriber.py` | Ensures `high.decision` is execution-ready and execution does not re-run High. |

## Current Architectural State

### Main Path Status

| Main path segment | Status | Notes |
|---|---|---|
| `MarketData -> LowContext / UltraSignal` | Partially aligned | Works, but still mixed between current runtime and legacy lane-cycle semantics. |
| `UltraSignal -> High` | Working | `HighEngine` consumes `ultra.signal` and now emits execution-ready `high.decision`. |
| `High -> OrderIntent` | Improved, still transitional | `execution_subscriber` now converts `high.decision` to `execution.intent` once, without second High. |
| `OrderIntent -> ExecutionService -> BrokerAdapter` | Working transitional path | Still routed through current `ibkr_execution.py` control-plane bridge. |
| Single-path architecture | Improved, not complete | Major conflict removed, but dual runtime semantics still exist elsewhere. |

### High-Risk Architectural Gaps Still Open

| Gap | Status | Why it still matters |
|---|---|---|
| AI still directly affects live High output | Not done | `ai/high.py` still computes live `high.decision`, rather than emitting only `AdjustmentProposal` / `RiskOverlay`. |
| Governance plane not implemented | Not done | `advisory/contracts.py` exists, but no full governance/audit/policy snapshot pipeline is wired into runtime. |
| `ai/*` daemon loops not yet moved out | Not done | `ai/high.py`, `ai/low.py`, `ai/ultra.py` still contain daemon/runtime responsibilities. |
| `state_store.py` ownership split | Not done | Logical stores are still not separated into owned modules/services. |
| Adapter-only IO boundary | Not done | Boundary is improved but not fully enforced across runtime / execution / advisory paths. |
| Bus unification / worker supervisor | Not done | The repository still has multiple runtime/bus semantics in transitional coexistence. |

## Important Current Truths About Ultra

Do not treat `Ultra` as an isolated task.

Project-level reality:

1. `Ultra` is a pre-filter and signal source, not the final decision layer.
2. Its real value depends on `High` being the unique decision closure.
3. The recent work removed a major blocker around `Execution`, which was more important than continuing to optimize `Ultra` in isolation.

Current Ultra status:

- Rule-only placeholder mode works.
- Event-driven runtime wiring works.
- Sync lane-cycle fallback still exists.
- Full advisory/governance decomposition of Ultra is not done yet.

## What Has Not Been Done Yet

### Immediate Next Work, In Correct Order

| Priority | Task | Expected outcome |
|---|---|---|
| P0 | Freeze formal `TradeDecision` and `OrderIntent` naming/contracts | Stop relying on the transitional `HighDecisionEvent` name as the long-term authority. |
| P1 | Move AI out of direct live decisioning into governance | AI should produce only `AdjustmentProposal` / `RiskOverlay`, then governance decides what becomes effective. |
| P1 | Split `ai/ultra.py` into lane sentinel vs advisory interpretation | Keep Ultra rules/event contract in lane; move vector/news interpretation into advisory. |
| P1 | Move daemon/runtime loops out of `ai/*` | Align with master plan boundary: runtime host manages worker lifecycles. |
| P1 | Separate `execution service` vs `broker adapter` more explicitly | Reduce remaining cross-layer coupling in `ibkr_execution.py`. |
| P1 | Start logical store ownership split | Break `state_store.py` into runtime/execution/risk/lane-context ownership modules. |

### Later Work

| Priority | Task | Expected outcome |
|---|---|---|
| P2 | Unify bus and worker supervision | One host/supervisor model, one authoritative bus. |
| P2 | Add recovery/reconcile order guarantees | Match master plan recovery sequence and degrade modes. |
| P2 | Clarify hard/soft parameter boundaries | AI must not modify hard risk parameters online. |
| P3 | Add architecture guard tests | Dependency guard, single-path test, AI-off parity test, recovery smoke test. |
| P3 | Paper-ready runtime modes | `OFF / SHADOW / BOUNDED_AUTO / HUMAN_APPROVAL` startup baseline. |
| P3 | Cleanup old compatibility layers | Reduce remaining legacy path surface area after new authority is stable. |

## Recommended Working Method For The Next Session

Use this order and do not skip steps:

1. Re-read `MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md`.
2. Treat the current authority as:
   - `runtime/bootstrap.py`
   - `kernel/contracts.py`
   - `kernel/coordinator.py`
   - latest `execution_subscriber.py` after second-High removal
3. Do **not** start with more Ultra-only work.
4. Start by freezing the formal `TradeDecision / OrderIntent` contract names and shape.
5. Then redirect AI influence into governance:
   - advisory produces proposal/overlay only
   - High reads approved parameter snapshot only
6. Only after that, continue the Ultra split:
   - rule sentinel stays in lane
   - vector/news interpretation moves to advisory
7. Then continue store ownership and adapter-only IO cleanup.

## Concrete Next-Session Implementation Plan

### Step 1

Introduce or rename toward formal `TradeDecision` and `OrderIntent` contracts in `kernel/contracts.py`, while keeping compatibility aliases if needed.

Goal:

- stop using `HighDecisionEvent` as the conceptual long-term endpoint
- keep transition safe

### Step 2

Refactor `ai/high.py` so AI no longer directly writes final live decision parameters.

Goal:

- AI produces proposal-like objects or inputs to governance
- High applies only approved/effective policy snapshot

### Step 3

Create governance path skeleton:

- intake validation
- registry/meta binding
- policy validation
- audit
- effective snapshot application

Goal:

- `advisory/contracts.py` stops being dead-end scaffolding

### Step 4

Split `ai/ultra.py`:

- lane/service side keeps rule engine + `UltraSignal` contract behavior
- advisory side gets vector/news interpretation

Goal:

- Ultra matches blueprint role

## Known Transitional Compromises

These are currently acceptable but must not be mistaken for final architecture:

- `ai/high.py` still calls legacy `lanes/high.evaluate_event()` internally as a bridge.
- `high.decision` is still a transitional name, even though it is now execution-ready.
- `execution_subscriber.py` is cleaner now, but `TradeDecision` naming/governance are still not finalized.
- `state_store.py` remains monolithic.

## Validation Already Run

The following have passed during this session:

- `python3 -m py_compile` on modified source/tests
- `python3 -m unittest -q tests.test_event_driven_engines tests.test_execution_subscriber`
- `python3 -m unittest -q tests.test_integration_e2e tests.test_replay tests.test_main_runtime_mode`
- `python3 -m unittest -q tests.test_non_ai_validation_report`
- `python3 -m compileall src/phase0 tests`

## Files Most Relevant To Continue From

- `src/phase0/kernel/contracts.py`
- `src/phase0/ai/high.py`
- `src/phase0/execution_subscriber.py`
- `src/phase0/ibkr_order_adapter.py`
- `src/phase0/advisory/contracts.py`
- `src/phase0/ai/ultra.py`
- `src/phase0/lanes/__init__.py`
- `src/phase0/state_store.py`

## Suggested Prompt For The Next Window

Use this exact instruction in the new conversation:

> 请先阅读 `/Users/cloudsripple/Documents/trae_projects/AAQ/docs/handoffs/2026-03-19_master-plan_execution-dedup_handoff.md`，并严格以 `/Users/cloudsripple/Documents/trae_projects/AAQ/docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md` 为总基线。先给出当前任务定位、已完成事项、未完成事项，然后从“冻结正式 `TradeDecision / OrderIntent` 契约，并把 AI 压回 governance 边界”开始继续实施。继续使用多 agent 思维，但最终只输出一版统一、收敛、可执行方案并直接动手改代码。

