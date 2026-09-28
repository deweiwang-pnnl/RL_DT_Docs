# Well-plate stacking — round report, 2026-09-22 → 09-28

*Dewei Wang (with Claude) · Legion laptop `trossen-ai` (RTX 5090) · round file:
[`../rounds/Round-2026-09-22-wellplate-grasp-fix.md`](../rounds/Round-2026-09-22-wellplate-grasp-fix.md) · meeting
slides: [`../presentations/2026-09-28-weekly/`](../presentations/2026-09-28-weekly/)*

Links to `results/`, `PROGRESS.md` and `PLAN.md` open the copies in [`../evidence/wellplate/`](../evidence/wellplate/);
`run_*.sh` and `WellPlate_RL/` are code in the `RL_DT` repo (`RL_DT/_isaaclab_wellplate/`). [`PROGRESS.md`](../evidence/wellplate/PROGRESS.md) is the complete chronology (every run, diagnosis and decision with its
evidence); this report is the organised version.

---

## 1. Results

Every number is a **deterministic evaluation** (the policy's mean action, no exploration noise) over **128 episodes**
(64 environments × 2), produced by `WellPlate_RL/scripts/rsl_rl/eval_policy.py`, separate from training. One training
seed per run.

| # | Task | Success criterion | Result | Baseline | Evidence |
|---|---|---|---|---|---|
| 1 | Grasp gate (scripted, before training) | plate held, lifted 10 cm | **16 / 16** | 09-20 setup: 0 | [`results/2026-09-26_gripper_fix/`](../evidence/wellplate/results/2026-09-26_gripper_fix/) |
| 2 | Align | 4 cm / 20° | **82.0 %** | — | [`results/2026-09-26_summary/`](../evidence/wellplate/results/2026-09-26_summary/) |
| 3 | Lift | 6 cm up, tilt < 10° | **87.5 %** | 0 % (09-21) | same |
| 4 | Stack, 2 plates | 3 cm / 1.5 cm height / 11° | **50.8 %** | 0 % | same |
| 5 | Centred stack, 2 plates | ≤ 5 mm centring, ≤ 3° twist, ≤ 3° tilt, released, at rest | **90.6 %** | 09-26 policy: 0 % | [`results/2026-09-27_centered/`](../evidence/wellplate/results/2026-09-27_centered/) |
| 6 | E1 three plates, hand-off | each placed plate as in 5 vs the one below; lower plate stays in place | **52.3 %** | C3 alone: 0 % | [`results/2026-09-27_stack3/`](../evidence/wellplate/results/2026-09-27_stack3/) |
| 7 | E2 three plates, all loose | as 6 | **46.1 %** | 26.6 % | same |
| 8 | E3 + loose bottom plate (50 g) | as 6, bottom plate moved ≤ 1 cm | **49.2 %** | — | same |
| 9 | E4 + realistic arm (gravity on + compensation) | as 8 | **54.7 %** | E3 gravity off 49.2 % | same |
| 10 | E5 other libraries | Reach / Align from scratch | table in § 7 | — | [`results/2026-09-27_libs/`](../evidence/wellplate/results/2026-09-27_libs/) |

Final policies: two-plate centred `logs/rsl_rl/wellplate/2026-09-27_10-59-14_centered/model_20593.pt` (C3); three
plates first placement `2026-09-27_21-46-39_stack3a/model_23486.pt`, second placement
`2026-09-27_22-08-55_stack3b/model_27385.pt`. (Checkpoints are git-ignored; they are on the Legion laptop.)

---

## 2. Setup

| Item | Value |
|---|---|
| Simulator | Isaac Sim 5.1 + Isaac Lab 2.3.2 (manager-based RL env), container `isaac-lab-tuberacking` |
| Robot | Martin's Ridgeback + UR7e + Robotiq 2F-140 (`Ridgeback_UR7e_2f140.usd`), base locked; arm joints PD 400 / 80 |
| Scene | Martin's `WellPlates.usd` (1 m cube table, three 96-well plates 128 × 85 × 26 mm); physics added at spawn by our code |
| Action (7-D) | relative differential IK of the TCP (2 cm, 0.05 / 0.05 / 0.1 rad per unit) + binary gripper (closes on negative) |
| Observation | privileged simulator state: arm joints, TCP pose, plate pose, goal pose, gripper, last action, twist to the goal (5-step history, 215 inputs) |
| Algorithm | PPO, rsl_rl 5.0.1, 512 parallel environments, 24 steps per iteration, MLP 512-256-128 ELU |
| Control | 30 Hz policy, 120 Hz physics |
| Robot gravity | off during training (see § 6, E4); plates always have gravity |
| Gates | every stage gated on the deterministic evaluation (≥ 40 % for centred and three-plate stages), one retry, then stop |

Unattended drivers: `run_ladder_v3.sh` (align → lift → stack), `run_centered.sh` (C1a → C3), `run_stack3.sh`,
`run_skills.sh`, `run_e3.sh`, `run_stack3_e4.sh`, `run_libs.sh` / `run_libs2.sh`. The plans they executed: [`PLAN.md`](../evidence/wellplate/PLAN.md)
v3 (grasp fix + ladder), v4 (centred stack), v5 (three plates → libraries), each with its definition of done.

---

## 3. The lift blocker (09-22 → 09-26)

On 09-21 no plate had ever been lifted. Martin's updated robot (GRIPPERFIX, 09-22) turned out to be an assembly layer
that does not compose with our robot file (the gripper lands 0.86 m from the wrist) and was not used. Working on our
own setup, four defects were found — each measured before it was fixed:

| Defect | Evidence | Fix |
|---|---|---|
| Pad joint driven to 0 (ratio copied from the URDF, where it is a fixed pad mount); in the USD it closes the four-bar loop and must follow +q | pads tilt into a V: 12° at the 85 mm contact, 24° closed (sweep, F2) | pad joint follows +q (as Isaac Lab's 2F-140 helper does) |
| Grasp height | pads travel 18.4 mm toward the table while closing (18.3 predicted from the USD anchors, F1) — they hit the table | pre-open 0.2 rad (112 mm), grasp point 16 mm above the plate root |
| Closing axis | plate body x = 127.6 mm, y = 85.4 mm; `CLOSING_AXIS_INDEX` had been 0 since 09-20 | index 1 (close across the 85 mm side) |
| Contact physics | under a two-sided squeeze the pads sank through the plate (one-sided push worked) | Isaac Lab's UR10e + 2F-140 contact settings (depenetration 5, max impulse 1e32, 5 mm contact offset; plate 32 solver iterations) |

Gripper variant G2 (Isaac Lab's drives, mimic kept, NVIDIA colliders as shipped) + these settings held **16 of 16**
plates, lifted 99.5 mm, tilt 0.6° (scripted grasp probe, [`results/2026-09-26_gripper_fix/`](../evidence/wellplate/results/2026-09-26_gripper_fix/), S1, V2). G1 (all finger
joints driven hard) spun the plate out. Also found: the 09-20 "no colliders" conclusion rested on an invalid teleport
test; the arm stalls ~0.3–0.4 m short of IK targets with robot gravity on and no compensation → robot gravity off
(Dewei's decision), revisited in E4.

## 4. The ladder: align → lift → stack (09-26)

`run_ladder_v3.sh`; results F4 in [`results/2026-09-26_summary/`](../evidence/wellplate/results/2026-09-26_summary/). What it took, each confirmed by a measurement:

- **Gate on the deterministic evaluation.** With a binary gripper, exploration noise flips the grip open; lift training
  success read 19.9 % while the deterministic policy lifted 87.5 %.
- **Entropy 0.01 → 0.001, std reset at warm start.** The action std grew 1.0 → 3.7 across stages (actions are clipped
  to ±1, so a wide std costs nothing) and collapsed the stack stage.
- **Stack rewards.** Goal terms were gated at rest + 4 cm, but a stacked plate sits at rest + 2.6 cm — placing lost
  reward. Gated at 1 cm off the table; a `placed` reward added.
- **Release.** The policy placed but never let go (gripper command −3, noise 0.5) → gripper-only exploration std 2.0.
- **Success bonus never paid.** Isaac Lab's `is_terminated_term` masks truncations; success is a truncation here → own
  `success_reward` term.

## 5. Centred stacking (plan v4, 09-26 → 09-27)

Definition: centring ≤ 5 mm, twist ≤ 3° (long edges, 0° and 180° both count), tilt ≤ 3°, gripper open, plate at rest.
The 09-26 stack policy scored 0 % at these criteria (median twist 73°, mostly still holding the plate).

| Problem (measured) | Fix |
|---|---|
| Twist never improved (flat at ~60° for 500 it.) | the target plate's mesh is rotated 48.97° inside its prim → twist measured on the real long axes; twist as an observation (sin 2Δ, cos 2Δ); checkpoint widened 205 → 215 inputs with zero weights |
| rsl_rl's adaptive learning rate pinned at its 1e-5 floor (median 2.3e-5) | fixed learning rate 1e-4 |
| Only ~15 % of each relative wrist command is realised per step | wrist-yaw action scale 0.05 → 0.1 (with a compensated warm start) |
| With success only below 10° twist, nothing was ever rewarded | twist tolerance curriculum C1a 45° → C1b 30° → C1c 20° → C1 10° |
| Placed but never released at C1a (1.6 %) — success bonus 50 × 1/30 s = 1.7, below the critic's noise (value loss 25–48) | bonus weight 600 (≈ 20 per success) → C1a 67.2 % |
| Driver restarted C1 from the 09-26 policy after C1a–C1c | fixed within a minute; C1 continues from C1c |

Curriculum results (deterministic): C1a 67.2 % · C1b 67.2 % · C1c 73.4 % · C1 85.2 % · C2 (10 mm / 5° / 3°) 87.5 % ·
**C3 (5 mm / 3° / 3°) 90.6 %**. Successful episodes: median 2.4 mm, 0.9° twist, 0.0° tilt. Evidence
[`results/2026-09-27_centered/`](../evidence/wellplate/results/2026-09-27_centered/) (F5 per-episode errors before/after, F6 stages, V5 before/after video).

## 6. Three plates, loose bottom plate, realistic arm (plan v5, 09-27)

### E0 — code (no training)
Martin's third plate (`WellPlate_01`, the same mesh as the others) made dynamic at spawn. Every reward / observation /
success term reads "the plate" and "the target"; three read-only **role stand-ins** (`mover`, `base`, `lower`,
`mdp/multi_plate.py`) resolve per environment to the plate being moved and what it goes on, so the existing terms and
the 215-input observation carry over. Tasks `Wellplate-Stack3Handoff-v0` (E1), `-Stack3Loose-v0` (E2),
`-Stack3LooseBottom-v0` (E3), `-Stack3LooseBottomRealArm-v0` (E4). Checked by `scripts/probe_multi_plate.py` before
any training (exact stand-ins, 0.00 mm drift of a pre-placed plate, phase switch carries the placed pose within 1 mm,
reach to the second pick area sub-mm).

### E1 — hand-off: five attempts
| Attempt | What happened (measured) | Diagnosis | Next |
|---|---|---|---|
| 1 one policy | first placements 15 % → 0 in 200 it. | a 180°-flipped base plate's quaternion became a ~100σ input (the goal inputs never varied in C3 training, normaliser std ≈ 0) | canonical base orientation |
| 2 | same collapse; collapsed checkpoint scores 0.8 % on the 2-plate task | swap test: C3 weights + new normaliser 93 %, new weights + C3 normaliser 3.9 % → the **weights** were overwritten | train single placements |
| 3 | 84.4 % retained at 200 it., 10.2 % at 1100 it.; the policy stopped grasping | C3 carries at a height that clears one plate; with a 2-plate stack it crashes into it; crashes/drops teach "don't grasp" in both phases | two skills |
| 4 two skills, kinematic middle plate at full height | second placement 4.7 % → 0.8 % | it never finds "carry and release 26 mm higher" | rising stack |
| 5 rising stack + hand-off start states | h 0 / 6.5 / 13 / 19.5 / 26 mm: 80.5 / 70.3 / 82.8 / 92.2 / 91.4 %; then the dynamic sequence 1.6 % — at the hand-off the second skill's first move dragged the placed plate (> 5 mm in 61 % of envs within 5 steps) | trained from the home pose only | 2000 recorded hand-offs (the first skill's releases) as start states + displacement penalty → **52.3 %** |

**Two skills**: policy A (C3, unchanged) places the first plate, policy B places the second; the evaluator switches by
the environment's phase (`eval_policy.py --checkpoint A --checkpoint2 B`). A kinematic middle plate can start inside
the bottom plate (kinematic bodies do not collide), so at 0 mm the task equals C3 and the height rises in steps.

### E2 — all loose
Plate 3 in its own pick area (reach checked); B continued on loose-mode starts (half from hand-offs): **46.1 %**
(before: 26.6 %).

### E3 — loose bottom plate
First attempt: the first skill, fine-tuned on a 50 g loose bottom plate, collapsed into not grasping within ~10
iterations (C3 untrained: 11.7 %; it presses on its goal and shoves the plate 25–45 mm). Fix: displacement penalty
(both phases) + **mass curriculum** 20 kg → 2 → 0.5 → 0.15 kg → 50 g: 82.8 / 60.2 / 50.8 / 49.2 / **61.7 %** first
placements; then B on the loose bottom plate → full sequence **49.2 %**.

### E4 — realistic arm
`mdp/gravity_comp.py`: the IK arm action plus, every physics step, the joint torques G(q) from PhysX's inverse
dynamics as feed-forward efforts (arm and gripper joints). IK tracking after 300 steps (16 envs): gravity off 0.0 mm;
gravity on without compensation 434 mm; with compensation 0.0 mm. The E3 policies unchanged on the gravity-on arm:
**54.7 %**.

Evidence: [`results/2026-09-27_stack3/`](../evidence/wellplate/results/2026-09-27_stack3/) (README, F7 results, F8 curricula, V6 overview video, V7 close-up,
`stages.md` with every stage and checkpoint, `eval_*` including the diagnostics named above).

## 7. Other libraries (E5, 09-27 → 09-28)

Same task ids, from scratch, 512 envs, same env-step budget, same deterministic evaluation (`scripts/eval_common.py`
added to each library's play script). Settings mirror the rsl_rl reference where a counterpart exists
(`agents/*_cfg.yaml`).

| Stage | rsl_rl PPO | rsl_rl PPO, fixed lr 1e-4 | skrl PPO | skrl SAC | rl_games PPO | SB3 PPO |
|---|---|---|---|---|---|---|
| Reach (6.1 M steps) | 100 % · 14 min | 100 % · 14 min | 100 % · 11 min | 0 % · 17 min | 100 % · 13 min | 0 % · 9 min |
| Align (12.3 M steps) | 3.9 % · 26 min | 0 % · 25 min | **98.4 %** · 24 min | 0 % · 37 min | 0 % · 20 min | 0 % · 19 min |

- The skrl / rsl_rl gap on Align is **not explained**: rsl_rl's KL-adaptive rate sat at its 1e-5 floor early (median
  7.6e-5, skrl 1.4e-4), but rsl_rl with a fixed 1e-4 also scored 0 %. Untested: skrl normalises value targets; skrl
  starts at a higher rate (~6e-4); seed luck with one seed.
- SB3 PPO: fixed rate 3e-4 and KL early stop (target 0.01, measured 0.015) end most updates after one epoch.
- skrl SAC: one gradient step per vectorised step = 12 000 / 24 000 updates for 6.1 / 12.3 M env steps — too few; a fair
  SAC test needs more updates per step. Its first start failed on a skrl 2.1 config name (fixed).
- rl_games: learning rate healthy (median 2e-4); Align 0 %, cause not investigated.

## 8. Limitations and threats to validity

- **One seed per training run.** One standard deviation of a 128-episode success rate near 50 % is about 4.4 percentage points;
  run-to-run variance is unmeasured.
- **Final setting: 36 % time-outs, 9 % drops.**
- **Two policies switched by the environment** (phase is known to the evaluator), not one policy that decides.
- **Privileged observations** (exact plate poses); locked base; fixed pick areas; no randomisation of plate mass,
  friction or robot base.
- **Realistic arm** = gravity + exact compensation; no joint friction, latency or motor model.
- **Kinematic curriculum stages** (middle plate inside the bottom plate) are physically impossible scenes used only to
  shape learning; the gates that count use real dynamic plates.
- **Rendering:** the bottom plate appears black in our container (same mesh as the others; cause not checked).

## 9. Code changes this round (in `WellPlate_RL/`)

| Area | Files |
|---|---|
| Gripper fix | `scene.py` (variants G0/G1/G2, reference physics, closing axis, grasp point), `robot_spawner.py`, `mdp/mimic_gripper.py` |
| Centred stacking | `centered_env_cfg.py`, `mdp/wellplate_mdp.py` (twist measures, centred success), `scripts/widen_obs_checkpoint.py`, `set_checkpoint_lr.py`, `reset_action_std.py` |
| Three plates | `mdp/multi_plate.py` (role stand-ins, phase switch, resets, hand-off bank), `stack3_env_cfg.py`, `data/handoff_bank.pt` |
| Realistic arm | `mdp/gravity_comp.py`, `realistic_arm.py` |
| Libraries | `agents/{skrl_ppo,skrl_sac,rl_games_ppo,sb3_ppo}_cfg.yaml`, `scripts/{skrl,rl_games,sb3}/`, `scripts/eval_common.py` |
| Evaluation / tools | `scripts/rsl_rl/eval_policy.py` (`--diag_stack`, `--checkpoint2`, `--track_switch`, `--save_handoff_bank`), `record_labelled.py`, probes `probe_*.py`, plots `plot_*.py`, `swap_normalizer.py` |

## 10. Reproduce

```bash
# inside the Legion laptop's container workflow (see guides/SHOWING_PROGRESS.md for the exact docker exec prefix)
START_STAGE=C1a ./run_centered.sh                 # centred 2-plate curriculum C1a → C3
START_STAGE=B1h00 ./run_skills.sh                  # second skill: rising stack → B2 (E1) → E2
./run_e3.sh                                        # loose bottom plate: mass curriculum → E3b
./run_libs.sh; LIBS=rsl_rl_fixed ./run_libs2.sh    # E5
# evaluate the final three-plate policies on the realistic arm (E4)
scripts/rsl_rl/eval_policy.py --task Wellplate-Stack3LooseBottomRealArm-v0 --num_envs 64 --episodes 2 --headless \
  --checkpoint logs/rsl_rl/wellplate/2026-09-27_21-46-39_stack3a/model_23486.pt \
  --checkpoint2 logs/rsl_rl/wellplate/2026-09-27_22-08-55_stack3b/model_27385.pt --diag_stack \
  env.events.reset_multi.params.phase2_prob=0.0 env.terminations.success.params.sequential=True env.episode_length_s=30.0
```
