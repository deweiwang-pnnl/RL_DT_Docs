# Three plates, loose bottom plate, realistic arm — results (PLAN v5 E1–E4, 2026-09-27)

**The robot stacks all three of Martin's plates — each centred on the one below within 5 mm, twisted ≤ 3°, tilted ≤ 3°,
both released, the lower plate not knocked out of place — with every plate starting loose, the bottom plate loose
(moved ≤ 1 cm), and the realistic arm (robot gravity on + compensation): 54.7 % of 128 deterministic episodes**
(target ≥ 40 %).

| Step | Setting | Result (deterministic, 128 episodes) | Baseline |
|---|---|---|---|
| E1 | hand-off: after plate A is placed, the next plate appears in the pick area | **52.3 %** | 0 % (C3 policy alone) |
| E2 | all loose: plate 3 lies in its own pick area B | **46.1 %** | 26.6 % (E1 skills) |
| E3 | as E2 with the bottom plate loose (50 g, may move ≤ 1 cm) | **49.2 %** | — (both skills retrained) |
| E4 | as E3 with the realistic arm (gravity on + compensation torques) | **54.7 %** | 49.2 % (E3, gravity off) — no retraining |

Final policies (rsl_rl): first placement `2026-09-27_21-46-39_stack3a/model_23486.pt`, second placement
`2026-09-27_22-08-55_stack3b/model_27385.pt`; the evaluator runs the first in phase 1 and the second in phase 2
(`eval_policy.py --checkpoint … --checkpoint2 …`).

## How it got there (details and evidence in PROGRESS.md, 09-27)

1. **One policy for both placements failed three ways.** A flipped base plate's quaternion became a ~100σ input (fixed:
   canonical orientation); then training on the second placement overwrote the first-placement skill — the weights, not
   the input normaliser (swap test: C3 weights + new normaliser 93 %, new weights + C3 normaliser 3.9 %); single-placement
   training only delayed it (84 % at 200 it., 10 % at 1100 it.: the policy learned not to grasp, because every carry toward
   the 2-plate stack ended in a crash).
2. **Two skills.** The C3 policy keeps the first placement; a second policy, fine-tuned from it, learns the second.
3. **Rising stack.** Trained directly at full stack height the second skill fell from 4.7 % to 0.8 %. A kinematic middle
   plate that starts inside the bottom plate (kinematic bodies do not collide) and rises 0 → 6.5 → 13 → 19.5 → 26 mm:
   80 → 70 → 83 → 92 → 91 % (F8, left).
4. **Hand-off start states.** With a dynamic middle plate the sequence gave 1.6 %: at the hand-off the second skill's first
   move dragged the plate just placed (> 5 mm within 5 steps in 61 % of envs). Training from 2000 recorded hand-offs (the
   first skill's releases) plus a penalty while the placed plate sits displaced → E1 52.3 %.
5. **Loose bottom plate.** The first skill pushed the 50 g plate (11.7 %) and, fine-tuned directly, collapsed into not
   grasping. Displacement penalty + a mass curriculum 20 kg → 2 → 0.5 → 0.15 kg → 50 g: 83 → 60 → 51 → 49 → 62 % (F8, right).
6. **Realistic arm.** Compensation torques from PhysX's inverse dynamics make the gravity-on arm track exactly like the
   gravity-off arm (probe: 0.0 mm at step 250 both; 434 mm off without compensation), so the E3 skills transfer unchanged.

## Files

| File | What it shows |
|---|---|
| `F7_three_plates.png` | the four results against their baselines |
| `F8_curricula.png` | rising-stack and bottom-plate-mass curricula |
| `V6_three_plates_E4_viewT.mp4` | final setting (E4), 6 consecutive episodes, overview of both pick areas and the stack, captioned with outcome and per-plate errors (4/6 successes) |
| `V7_three_plates_E4_viewS.mp4` | the same, close-up of the stack (4/6) |
| `stages.md` | every training stage with its deterministic evaluation and checkpoint |
| `eval_*.log` / `eval_*.json` | every evaluation, incl. the diagnostics named above (`seq_switch_track`, `diag_*`, baselines) |

In the videos Martin's bottom plate renders black (same mesh as the other two; cause not checked); the other two are
the white and the yellow plate.

Remaining failures in the final setting: 36 % time-outs (mostly the second placement not finished, or the middle plate
pushed out of tolerance) and 9 % dropped plates.
