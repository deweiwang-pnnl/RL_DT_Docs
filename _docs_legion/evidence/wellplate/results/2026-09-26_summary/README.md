# 2026-09-26 — well-plate summary set (for the team)

**Result:** the robot now picks up a 96-well plate and stacks it on a second plate. Deterministic evaluation, 128 episodes
per stage (no exploration noise; `eval_*.json` in each stage folder):

| Stage | Training tolerance | Strict tolerance | Checkpoint |
|---|---|---|---|
| Align | **82.0 %** (4 cm, 20°) | 0.0 % (2 cm, 15°/10°) | `2026-09-26_19-42-36_align/model_1297.pt` |
| Lift | **87.5 %** (6 cm up, tilt < 10°) | 14.8 % (10 cm up, tilt < 5°) | `2026-09-26_20-29-26_lift/model_3295.pt` |
| Stack (2 plates) | **50.8 %** (3 cm / 1.5 cm / 11°) | 22.7 % (1 cm / 5 mm / 5°) | `2026-09-27_02-29-31_stack/model_10790.pt` |

On 09-20/21 lift and stack were 0 %: no plate was ever lifted.

| File | What it shows |
|---|---|
| `F4_success_by_stage.png` | the table above as a chart |
| `V3_lift_before_after_viewA.mp4`, `..._closeup.mp4` | lift, 09-21 vs 09-26, same camera |
| `V4_stack_8_episodes_labelled.mp4` | 8 consecutive stack episodes (close-up on the target), each captioned with how it ended: 4 success, 3 timeout, 1 dropped — not cherry-picked |
| `S2_stack_success_sequence.png` | one successful stack: plate at start → gripped → carried → released on the target |
| `V1_sweep_G0_vs_G1.mp4`, `V2_grasp_G0_vs_fixed.mp4`, `S1_grasp_sequence.png`, `F1_pad_height_during_close.png` | the gripper fix (see `../2026-09-26_gripper_fix/README.md`) |
