# Centred 2-plate stack — results (PLAN v4, 2026-09-27)

**The robot stacks one well plate centred and aligned on the other: 90.6 % of 128 deterministic episodes meet all four
final conditions at once** — centring ≤ 5 mm, twist ≤ 3° (long edges, 0°/180° equal), tilt ≤ 3°, gripper released with
the plate at rest. Target was ≥ 40 %. The 09-26 stack policy scores 0.0 % at the same criteria.

Final policy: `WellPlate_RL/logs/rsl_rl/wellplate/2026-09-27_10-59-14_centered/model_20593.pt` (task `Wellplate-Centered-v0`).

## Evaluations (deterministic, 128 episodes)

| Policy | Criteria | Success | Time-out | Dropped |
|---|---|---|---|---|
| Centred policy (C3) | final: 5 mm / 3° / 3° | **90.6 %** | 7.8 % | 1.6 % |
| 09-26 stack policy | final: 5 mm / 3° / 3° | 0.0 % | 81.3 % | 18.8 % |
| Centred policy (C3) | 09-26 criteria: 3 cm / 1.5 cm height / 11°, no twist check | 85.9 % | 8.6 % | 5.5 % |

The last row is lower than the first although its criteria are looser; the gap is within the sampling noise of 128
episodes (±3 %). It was evaluated in the centred task (which also requires the plate to be at rest), because the
09-26 stack task has 10 fewer observations than the centred policy.

Final placement of the successful episodes (116), median [p25–p75]: centring 2.4 mm [1.7–3.2], twist 0.9° [0.4–1.5],
tilt 0.0°. The 09-26 policy centres reasonably (median 5.4 mm in its timed-out episodes) but leaves the plate twisted by
73° and never releases it.

## Curriculum (each stage warm-started from the previous one; gate ≥ 40 % deterministic)

| Stage | Centring / twist / tilt | Deterministic success | Checkpoint |
|---|---|---|---|
| C1a | 15 mm / 45° / 5° | 67.2 % | `2026-09-27_08-06-42_centered/model_15198.pt` |
| C1b | 15 mm / 30° / 5° | 67.2 % | `2026-09-27_08-33-50_centered/model_15897.pt` |
| C1c | 15 mm / 20° / 5° | 73.4 % | `2026-09-27_09-01-03_centered/model_16596.pt` |
| C1 | 15 mm / 10° / 5° | 85.2 % | `2026-09-27_09-29-10_centered/model_17595.pt` |
| C2 | 10 mm / 5° / 3° | 87.5 % | `2026-09-27_10-06-03_centered/model_19094.pt` |
| C3 | 5 mm / 3° / 3° | **90.6 %** | `2026-09-27_10-59-14_centered/model_20593.pt` |

Training success (with exploration noise) falls within each stage while the deterministic success rises; the gate is on
the deterministic eval for this reason (binary gripper: noise flips the grip).

## Files

| File | What it shows |
|---|---|
| `F5_centred_errors.png` | per-episode final centring and twist error, 09-26 policy vs centred policy |
| `F6_centred_stages.png` | deterministic success per curriculum stage |
| `V5_centred_before_vs_after.mp4` | side by side, target close-up (view S), 8 consecutive episodes each, captioned with outcome and final errors. The centred policy finishes its 8 episodes in ~17 s and then holds its last frame; the 09-26 policy's episodes run the full 15 s each |
| `V5_..._frame150.png`, `_frame400.png` | stills from V5 |
| `labelled_final_viewS.mp4`, `labelled_before_viewS.mp4` (+ `.json`) | the two halves of V5 with per-episode outcome and errors |
| `play_viewA.mp4` | the centred policy, 4 envs, oblique view |
| `eval_*.log`, `eval_Wellplate-Centered-v0_*.json` | every evaluation (the `_diag` / `final_C3` / `before_C3` ones hold per-episode final states) |
| `stages.md` | the driver's stage table |

The baseline was evaluated through `2026-09-27_02-29-31_stack_widened/model_10790.pt`: the 09-26 checkpoint widened
205 → 215 inputs with zero weights for the new twist observation (`scripts/widen_obs_checkpoint.py`), so it behaves
exactly as the original.
