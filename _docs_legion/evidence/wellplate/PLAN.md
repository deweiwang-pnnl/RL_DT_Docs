# Well-plate task — PLAN v5 (3 plates, loose bottom plate, realistic arm, other libraries)

**Status 2026-09-27 20:20: done.** E1 52.3 %, E2 46.1 %, E3 49.2 %, E4 54.7 % (three plates, all loose, loose bottom plate,
realistic arm; deterministic, 128 episodes, gate 40 %); E5 comparison in `results/2026-09-27_libs/`. Deviations from the
definitions below: two skills (first / second placement) instead of one policy; E4 needed no retraining.

Dewei 2026-09-27: "go ahead to the end of the plan" = PLAN v4 §D4 in its order. Definitions of done below are mine
(Claude, from D4 and v3 §6); autonomy and stop rules = v4 §D3 unchanged. Chronology: `PROGRESS.md`.

**Facts measured before planning** (`scripts/probe_third_plate.py`, 09-27): Martin's three plates are the same mesh
(WellPlateSimple, 128 × 86 × 26 mm). The third plate `WellPlate_01` has its mesh aligned with its prim (like the object
plate: long side = body x); today it is a static collider 1.29 m from the robot base, out of reach. skrl 2.1.0,
rl_games 1.6.1 and Stable-Baselines3 2.9.0 are already installed in the container (no installs needed).

## E0. Code (no training)
- Third plate gets physics at spawn (dynamic rigid body, same mass / friction / contact settings as the object plate).
- **Roles**: every reward / observation / success term already reads "the plate" and "the target" by name. Two read-only
  stand-ins, `mover` and `base`, resolve per env to the real plate that is moving and the one it goes on (bottom, or a
  plate already placed). The base's orientation is expressed in the bottom plate's convention (its mesh is rotated 49°
  inside its prim), so one policy sees one consistent goal. A per-env phase switches the roles when a plate is placed.
- Task family `Wellplate-Stack3*-v0`, same 7-D action; observation layout unchanged (215), so C3 warm-starts it.
- Build check; probe: phase switch copies poses exactly; a plate rests stably on a placed plate; reach to the second
  pick area.

## E1. 3 plates (ii) — hand-off
Bottom plate fixed. Episode: place plate A on the bottom; when placed, the next plate is handed off into the pick area
(teleported there, as a person or feeder would); place it on A. Training: half the envs start with A already placed
(2 mm / 2° error), so both placements are practised; warm start from C3.
**Done:** each placed plate vs the one below ≤ 5 mm centring, ≤ 3° twist, ≤ 3° tilt, both released, the lower plate
not knocked out of tolerance — **≥ 40 % of 128 deterministic episodes**. Labelled video (view S), per-plate errors.

## E2. 3 plates (i) — all loose
Plate 3 starts on the table in a second pick area within reach (no hand-off); the robot stacks A on the bottom, then
plate 3 on A. Warm start from E1. **Done:** same criteria as E1, ≥ 40 %.

## E3. Loose bottom plate
The bottom plate becomes a dynamic body resting on the table (pose reset each episode). E2 task. Tolerances are
measured against the bottom plate's actual pose. **Done:** E2 criteria ≥ 40 %, and the bottom plate moved ≤ 1 cm.

## E4. Realistic arm
Robot gravity on, with gravity-compensation torques computed by PhysX every physics step (as a real UR controller
does); arm gains 400/80 unchanged. **Done:** IK tracking with gravity on ≈ gravity off (probe), and the E3 task
≥ 40 % with gravity on.

## E5. Other libraries / algorithms
Same task ids, one shared deterministic evaluator. skrl PPO, skrl SAC, rl_games PPO, Stable-Baselines3 PPO, and rsl_rl
PPO as the reference, each trained from scratch on Reach, then Align, with the same environment-step budget.
**Done:** table of success, wall-clock and env steps per library × algorithm × stage (a comparison — no gate).

Not in D4, left for later: Alvika's camera-based plate detection (v3 §6.5); lift precision at 10 cm.

---

# Well-plate task — PLAN v4 (centred 2-plate stack)

Approved by Dewei 2026-09-26 (evening). v3 (grasp fix → 2-plate stack) is below, kept as the record of Parts A–B.
Chronology of runs: `PROGRESS.md`.

**Status 2026-09-27 05:15: done — C3 (5 mm / 3° / 3°, released) 90.6 % deterministic over 128 episodes** (09-26 policy
0.0 %). C1 was split into a twist curriculum C1a–C1c (45° / 30° / 20°). Results: `results/2026-09-27_centered/README.md`.

**Objective:** the top plate stacked **centred and aligned** on the bottom plate, then run to the end without stopping
unless one of the four stop conditions in §D3 applies.

## D1. Definition of done

| Quantity | Meaning | Target |
|---|---|---|
| Centring | centre of the top plate vs centre of the bottom plate, seen from above | ≤ **5 mm** |
| Yaw (twist) | top plate's long side vs bottom plate's long side, seen from above; 0° and 180° both count as aligned | ≤ **3°** |
| Level (tilt) | top plate's lean away from flat, seen from the side | ≤ **3°** |
| Released | gripper open, plate resting on its own | required |
| Success rate | deterministic eval, 128 episodes, all four conditions at once | ≥ **40 %** |

Starting point (09-26, `2026-09-27_02-29-31_stack/model_10790.pt`): 50.8 % at 3 cm / 1.5 cm / 11° with no yaw check;
22.7 % at 1 cm / 5 mm / 5°; median placement error of the timed-out episodes ≈ 9 mm.

## D2. Steps

**C0 — code, no training (~1 h)**
- `mdp`: yaw error between the plates (long axes, modulo 180°); `stack_centered_success` (centring, yaw, height, level,
  released); rewards near the goal: centring kernel (std 1 cm), yaw alignment, both counted only when the plate is off
  the table and within ~5 cm of the goal; `placed` requires the centred condition of the current stage.
- `stack_centered_env_cfg.py` (task `Wellplate-StackCentered-v0`), tolerances as Hydra-overridable parameters so the
  curriculum stages below are overrides, not new code.
- `eval_policy.py --diag_stack` and `record_labelled.py` report centring error, yaw error and tilt.
- Build check (64 envs × 2 it.).

**C1 → C3 — tightening curriculum**, each stage warm-started from the previous one (C1 from the 09-26 stack
checkpoint), gate on the deterministic eval:

| Stage | Centring | Yaw | Level | Gate |
|---|---|---|---|---|
| C1 | 1.5 cm | 10° | 5° | ≥ 0.4 |
| C2 | 1 cm | 5° | 3° | ≥ 0.4 |
| C3 (final) | **5 mm** | **3°** | **3°** | ≥ 0.4 |

About 1–1.5 h of training per stage; 4–8 h in total with fixes. The ladder driver runs the stages; a gate miss gets one
retry, then the §D3 rule.

**Deliverables**
- Eval table at the final criteria and at today's criteria (for comparison); centring / yaw / tilt error distributions.
- Labelled videos of consecutive episodes (target close-up, view S); before/after: today's policy vs the centred one.
- Chart of centring and yaw error; `PROGRESS.md` morning read; round file; commits (never push).

## D3. Autonomy rules (Dewei 2026-09-26: "work to the end")

**I decide and continue** on: iterations and retries; intermediate tolerances between stages (including adding stages);
reward weights and shaping within this task; exploration / noise settings; checkpoint choice; bug fixes inside the
well-plate package. Each decision goes into `PROGRESS.md` with its evidence and is committed on its own.

**I stop and ask Dewei only if:**
1. the final definition (5 mm / 3° / 3°) looks unreachable and would need changing;
2. a fix needs something outside the package (Martin's assets, Isaac Lab itself, the robot model);
3. three fixes in a row give no measurable improvement (out of evidence-based ideas);
4. an infrastructure failure I cannot recover from (container, GPU, disk).

**How I ask:** a message in this conversation plus a push notification to Dewei's phone (Claude Code app); email if
that gets set up. The question also goes at the top of `PROGRESS.md`.

## D4. After this plan (from v3 §6, unchanged order)

Three plates ((ii) hand-off, then (i) all loose); loose bottom plate; realistic arm (gravity on + compensation);
other libraries / algorithms. Open side issues: lift precision at 10 cm (14.8 %), 12.5 % of stack episodes drop the plate.

---

# Well-plate task — PLAN v3 (Round-2026-09-22: grasp fix → 2-plate stack)

Approved by Dewei 2026-09-26. Supersedes v2.1 (2026-09-20; in git history). Chronology of runs: `PROGRESS.md`.

**Objective:** stack one well plate onto another tonight, with videos. Three plates, then other
libraries and algorithms, in later rounds.

## 1. Decisions (Dewei)

| Topic | Decision |
|---|---|
| Robot | Martin's Ridgeback + UR7e + 2F-140 only — no Isaac Lab built-in robot |
| Martin's asset | not waited on; all fixes in our Python, his files untouched |
| Tonight's scope | 2-plate stack + videos |
| 3 plates | later: (ii) plate 3 handed off into the pick area, then (i) all plates start loose, as its own stage |
| Gripper | pre-opens to ~112 mm (0.2 rad) before a grasp; closes across the plate's 85 mm side |
| Align | re-run 300 iterations, warm-started |
| Robot gravity | off for now (the arm behaves like the real, gravity-compensated UR); current arm gains kept (Dewei 09-26). Realistic arm later: gravity on + explicit gravity-compensation torques, as its own stage |
| Bottom plate | Martin's target plate fixed (kinematic) tonight; loose later as its own stage |
| Failed / stuck stage | diagnose; if confident of the cause, fix and continue (fix logged + committed on its own); stop and wait for Dewei when a decision is his (task, success criteria beyond agreed loosening, robot/asset, anything outside this package) or when unsure about something important |

## 2. Done — last round (09-14 → 09-21)

| Item | Result |
|---|---|
| Tube task brought up (zero-action agent, table fix, 300-it PPO) | 86 % tube reach — pipeline works |
| Well-plate package: physics on Martin's plates, 5 stage configs (7-D action, 205-D obs), ladder driver, probes | committed |
| Reach / Align | **96.7 %** / **96 %** (loosened) |
| Lift / Stack / Place | 0 % across 8 runs / 0 % / not run |
| Fixes kept | weld joint, TCP frame order, success as truncation, first-pass tolerances, short-side grasp, lid switch |
| Fixes to revisit | extra gripper colliders + pad boxes, removed mimic, all finger joints driven hard |

## 3. Done — this round so far (09-22 → 09-26)

- Martin's `Ridgeback_UR7e_2f140_reworked.GRIPPERFIX.usd` checked: does not compose with our `Ridgeback_UR7e.usd`, uses the broken `2f140_reworked.usd`. Messaged; no reply.
- Our training robot (`Ridgeback_UR7e_2f140.usd`) checked: NVIDIA `Robotiq_2F_140_physics_edit`, correct weld, exact parallelogram (100 mm / 19 mm links).
- Lift failure explained on paper (to be confirmed in A2/A3): (1) the pads travel ~18 mm toward the table while closing from full open to the 85 mm contact, so pads started 10 mm above the table hit it first; (2) `mimic_gripper.py` drove `*_inner_finger_pad_joint` to 0, but in the USD that joint closes the four-bar loop and must be at +q (Isaac Lab's own 2F-140 helper sets it to +q) → drives fight the loop → pads tilt into a V.

## 4. Part A — today, attended (no training)

- **A1 code:** pad target +q, open angle 0.2 rad (`mdp/mimic_gripper.py`); GRASP_POINT from the measured sweep, gripper-variant flag (`scene.py`, `robot_spawner.py`); stack "released" = back at pre-grasp opening (`stack_env_cfg.py`); new `probe_gripper_sweep.py`, `probe_grasp_ab.py`, `eval_policy.py`, `run_ladder_v3.sh` (gate stop, stuck watchdog 20 min, per-stage eval + videos).
- **A2 sweep probe** (1 env, no plate), current vs fixed → F1 pad-bottom height, F2 pad tilt, F3 pad gap vs 85 mm, V1 side-by-side closing video.
- **A3 grasp probe** (16 envs; align policy positions, arm IK descends, close, lift 10 cm, hold 2 s) — variants G0 current (control), G1 minimal fix, G2 = G1 + Isaac Lab reference drives (mimic back, only finger_joint driven, extra colliders off). **Gate: ≥ 12/16 held, tilt < 5°**; winner = higher hold rate, tie → G2. → V2 side-by-side grasp video, S1 four-frame strip. **Stop and show Dewei before any training.** If G0 gate fails: no training; overnight gripper-settings sweep instead.
- **A4 smoke test:** 64 envs × 5 it per stage config, with a video.

**Status 2026-09-26:** A1–A3 done — gate passed with variant G2 + reference contact physics (16/16 held, lifted
10 cm, tilt 0.6°); closing axis corrected to the 85 mm side. Evidence: `results/2026-09-26_gripper_fix/`. Open for
Dewei before Part B: robot gravity / arm gains (PROGRESS.md 09-26). A4 not run yet.

**Status 2026-09-26 20:24:** Part B done — align 82.0 %, lift 87.5 %, 2-plate stack 50.8 % (deterministic, training
tolerances; strict 0.0 / 14.8 / 22.7 %). Six diagnosed fixes on the way (PROGRESS.md 09-26). Evidence: `results/2026-09-26_summary/`.

## 5. Part B — tonight: 2-plate stack

| # | Stage | From | Iterations | Time | Gate |
|---|---|---|---|---|---|
| 1 | Align (new grasp height) | align ckpt | 300 | ~50 min | ≥ 0.8 |
| 2 | Lift | 1 | 1000 | ~2 h 15 | ≥ 0.4 |
| 3 | Stack onto Martin's target plate | 2 | 1500 | ~3 h | ≥ 0.3 |
| 4 | Deterministic eval + videos (A, D) per stage | — | — | ~45 min | — |

Rules: one loosened retry per gate, then the failure rule in §1; no probes during training; commit per stage, never push; `PROGRESS.md` live, plain language. Morning: PROGRESS.md, eval success (strict 1 cm/5 mm/5° and loose 2 cm/1 cm/10°), videos, curves vs the eight failed lift runs.

## 6. Part C — later

1. 3 plates (ii): stack stage on a 1- or 2-plate base, `eval_stack3.py` calls the policy twice.
2. 3 plates (i): wider pick area stage (reach check for the third plate).
3. Loose bottom plate stage.
4. skrl PPO/SAC and the other libraries on the same task ids.
5. Alvika's camera-based plate detection.

6. Realistic arm: robot gravity on with gravity-compensation torques (Dewei 09-26: "later we need realistic simulation").

## 7. Risks

| Risk | Response |
|---|---|
| Sim ≠ geometry prediction | use the measured curve for GRASP_POINT |
| G1 and G2 both < 12/16 | gripper-settings sweep instead of training; report |
| Grasp holds but lift RL stays 0 | check `grasp_ready` vs `lifting` timing; failure rule |
| Plate tilts on release | stack success needs level; check release frames |
| Isaac start-up hangs | watchdog kills after 20 min without an iteration; one relaunch |
