# Showing the well-plate progress to the team

*How to present the 2026-09-28 results: the slides, the recordings (with where the good moments are) and the training
curves in TensorBoard — from the work computer, or live from the Legion laptop.*

## 0. Before the meeting (10 minutes)

1. Sync both repos into **one parent folder**, side by side — the slides find the videos by relative path:
   ```
   RL_Twin/
   ├── RL_DT/          code + results (videos, charts) — _isaaclab_wellplate/results/
   └── RL_DT_docs/     docs — _docs_legion/presentations/2026-09-28-weekly/slides.html
   ```
2. Copy the TensorBoard bundle `RL_Twin/_exports/tensorboard_wellplate_2026-09-28.tar.gz` (14 MB, **not in git** — the
   logs are git-ignored) from the Legion laptop, e.g. `scp aidev@trossen-ai:RL_Twin/_exports/tensorboard_wellplate_2026-09-28.tar.gz .`
   or a USB stick.
3. Open `RL_DT_docs/_docs_legion/presentations/2026-09-28-weekly/slides.html` in Chrome / Edge / Firefox and click
   through once: every video should show a poster frame and play. If one does not, the path printed under it is the
   file to open directly.
4. Start TensorBoard (§ 3) in a second window, so it is ready when someone asks "how did training go?".

## 1. The slides

| | |
|---|---|
| `slides.html` | 17 slides, offline. → / Space next, ← back, **F** full screen, **P** print (one slide per page → Save as PDF). `slides.html#9` jumps to slide 9. |
| `slides.md` | Same slides for **Marp for VS Code**; "Export Slide Deck" → PowerPoint / PDF (videos become links). |
| `README.md` | One-page hand-out: what was done, what comes next, questions for the team. |

Suggested flow for a 15-minute slot: slides 1–2 (headline) → 4–5 (lift blocker, play V2) → 7 (centred, play V5
from ~0:00, point at the right side) → 9–11 (three plates, play V6 at 1:07) → 12 (realistic arm) → 13 (libraries) →
15–16 (limits, asks). Slides 3, 6, 8, 14, 17 are for questions.

## 2. The recordings

All under `RL_DT/_isaaclab_wellplate/results/`. Every labelled video carries a caption per episode with its outcome and
the final errors, so the team can read what they see.

| Video | Length | What it shows | Where to look |
|---|---|---|---|
| `2026-09-26_gripper_fix/V2_grasp_G0_vs_fixed.mp4` | 22 s | the same scripted grasp with the 09-20 gripper setup (left) and the fixed one (right) | left: pads never hold, plate stays; right: lifted 10 cm |
| `2026-09-26_gripper_fix/V1_sweep_G0_vs_G1.mp4` | 14 s | gripper closing in the air, old vs fixed pad joint | left pads bend into a V; right stay parallel |
| `2026-09-26_summary/V3_lift_before_after_viewA.mp4` | 15 s | lift policy before (09-20) and after the fix | before: nothing lifted |
| `2026-09-26_summary/V4_stack_8_episodes_labelled.mp4` | 60 s | 2-plate stack, 8 consecutive episodes | captions say success / time-out per episode |
| `2026-09-27_centered/V5_centred_before_vs_after.mp4` | 101 s | 8 episodes each: 09-26 stack policy vs the centred policy | right side: 8/8 centred within ~17 s, then it holds the last frame; left: twisted plates, time-outs |
| `2026-09-27_stack3/V6_three_plates_E4_viewT.mp4` | 97 s | **final setting**: three loose plates, loose bottom plate, realistic arm; 6 episodes, overview | **0:00–0:06** episode 1 (fast success); **1:07–1:15** episode 4, the cleanest full sequence; episode 2 shows a failure (middle plate pushed 16 mm) |
| `2026-09-27_stack3/V7_three_plates_E4_viewS.mp4` | 97 s | the same, close-up of the stack | 1:10 white plate centred on the black one; 1:14 yellow on top |

The bottom plate renders **black** (same mesh as the others; cause not checked) — mention it before someone asks.

To record new videos (Legion laptop only, needs the container):
```bash
docker exec -e DISPLAY= isaac-lab-tuberacking bash -c "cd /workspace/isaaclab/dw_wellplate/WellPlate_RL && \
  /workspace/isaaclab/isaaclab.sh -p scripts/rsl_rl/record_labelled.py --task Wellplate-Stack3LooseBottomRealArm-v0 \
  --num_envs 1 --headless --video --view T --episodes 6 --out my_videos \
  --checkpoint logs/rsl_rl/wellplate/2026-09-27_21-46-39_stack3a/model_23486.pt \
  --checkpoint2 logs/rsl_rl/wellplate/2026-09-27_22-08-55_stack3b/model_27385.pt \
  env.events.reset_multi.params.phase2_prob=0.0 env.terminations.success.params.sequential=True env.episode_length_s=30.0"
```
Views: `A` oblique, `S` stack close-up, `T` three-plate overview (defined in `scene.py`, `VIEWS`).

## 3. TensorBoard

### A. On the work computer (from the bundle)

```powershell
# PowerShell, in the folder where the bundle was copied
tar -xzf tensorboard_wellplate_2026-09-28.tar.gz
python -m pip install tensorboard          # once
tensorboard --logdir tensorboard_wellplate_2026-09-28 --port 6006
# open http://localhost:6006
```

The bundle has 40 runs (event files only, no checkpoints); its `README.md` maps each folder to a stage.

### B. Live, on the Legion laptop (all 4.6 GB of logs)

```bash
~/RL_Twin/SciOptControlToolkit/.venv/bin/tensorboard \
  --logdir ~/RL_Twin/RL_DT/_isaaclab_wellplate/WellPlate_RL/logs --port 6006
# from another machine on the network:  ssh -L 6006:localhost:6006 aidev@trossen-ai   then open http://localhost:6006
```

### What to show

In the **Scalars** tab set smoothing to ~0.9, then use the run filter (left) with these regexes:

| Story | Run filter | Tag (filter box) | What to point out |
|---|---|---|---|
| Centred curriculum | `_centered$` | `Episode_Termination/success` | six stages end to end (C1a … C3); iteration numbers continue across warm starts |
| Why we evaluate separately | `_centered$` | `Episode_Termination/success` | training success **falls** within C1–C3 while the deterministic evaluation rose 85 → 88 → 91 % (chart T1 in the slides) — exploration noise opens the binary gripper |
| Rising stack → three plates | `_stack3b$` | `Episode_Termination/success`, `Episode_Reward/lower_disp` | rising-stack stages, then B2 learning from ~0 to 64 %; the displacement penalty shrinking as the policy stops dragging the stack |
| Mass curriculum | `_stack3a$` | `Episode_Termination/success`, `Episode_Reward/bottom_disp` | 20 kg → 50 g |
| Release incentive | `_centered$` | `Episode_Reward/success_bonus` | nonzero only after the bonus fix |
| Library comparison | `_e5_align$` and skrl `ppo_torch` | `Loss/learning_rate` (rsl_rl), `Learning / Learning rate` (skrl) | rsl_rl's adaptive rate at its 1e-5 floor vs skrl's ~1e-4 — tested, **not** the explanation |

A static version of the key curves (for slides and for people without TensorBoard):
`RL_DT/_isaaclab_wellplate/results/2026-09-28_presentation/T1_training_curves.png`, with the CSVs in `curves/`.

## 4. If someone asks for a number

| Question | Answer and source |
|---|---|
| "How precise is the stack?" | 2-plate: median 2.4 mm / 0.9° / 0.0° (`results/2026-09-27_centered/README.md`) |
| "How often does the three-plate stack work?" | 54.7 % in the final setting; 36 % time-outs, 9 % drops (`results/2026-09-27_stack3/README.md`) |
| "Is it repeatable?" | One seed per run so far — the next thing to add |
| "What was actually wrong with the gripper?" | § 3 of `reports/wellplate-round-2026-09-28.md` |
| "Why two policies?" | one policy forgot the first placement (swap test) — report § 6, E1 |
| "Which RL library should we use?" | not decided; skrl PPO learned the harder stage from scratch, reason open — report § 7 |
