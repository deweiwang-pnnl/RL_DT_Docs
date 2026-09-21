# Well-plate task in Isaac Lab — status for the 2026-09-21 meeting

*Dewei Wang · Legion laptop (RTX 5090) · everything referenced here is in `RL_DT/_isaaclab_wellplate/`*

## 1. What the task is

Stack a 96-well plate (128 × 85 × 26 mm) onto another plate on a bench, with the Ridgeback + UR7e +
Robotiq 2F-140 mobile manipulator, base locked, in Martin's `WellPlates.usd` scene. Trained as a
five-stage curriculum, each stage warm-starting the next:

| # | Stage | Success criterion | Result |
|---|---|---|---|
| 1 | **Reach** | TCP 3 cm above the plate centre, gripper pointing down (4 cm / 20°) | **96.7 %** |
| 2 | **Align** | at grasp height, fingers across the plate's short side (+ yaw 20°) | **96 %** ¹ |
| 3 | **Lift** | close, lift 10 cm, keep level, plate in hand | 0 % — blocked by the gripper asset (§ 4) |
| 4 | Stack | carry onto the second plate, release within 2 cm / 1 cm / 10° | 0 % (needs 3) |
| 5 | Place | same, target at a random spot each episode | not run |

¹ measured on a run that used a mis-placed TCP frame (§ 4, item 3); the corrected run learns the
same behaviour but was scored before the "success as truncation" fix — re-run is 1 h.

Algorithm: PPO (rsl_rl), 512 parallel environments, ~4 s per iteration, 500–1500 iterations per stage.
One run of the whole ladder takes a night.

## 2. How it is set up

```
RL_Twin/
├── isaaclab_dt-main/            Alvika's Isaac Lab fork + Docker recipe  (container: isaac-lab-tuberacking)
├── digital_twin_models-DT_reorg Martin's USD assets  (mounted at /workspace/isaaclab/envs_external)
├── digitaltwin_rl-master        Alvika's TubeRacking_RL, pristine
└── RL_DT/                       our git repo — everything below is tracked
    ├── _isaaclab_tuberacking/   working copy of Alvika's task + container config (docker/compose.sh)
    └── _isaaclab_wellplate/     THE WELL-PLATE TASK
        ├── WellPlate_RL/        Isaac Lab "external project": 5 task ids, scene, MDP, scripts, logs/
        ├── run_ladder_v2.sh     unattended curriculum driver (gates, retries, videos, commits)
        ├── PROGRESS.md          chronological log of every run and finding
        ├── PLAN.md              the approved plan
        └── results/             per-stage videos, frames, curves, READMEs; gripper_*.png evidence
```

- **Scene:** `WellPlates.usd` (1 m cube table + Martin's three plates) placed so the cube edge meets the
  robot base; physics is added to the plates *at spawn* (`scene.py: spawn_wellplates_table`) — object
  plate rigid (50 g, friction 0.8), stack-target plate kinematic, third plate a static obstacle.
- **Robot:** Martin's `Ridgeback_UR7e_2f140.usd` with the gripper weld fixed (Alvika's script) and
  colliders added to the gripper meshes at spawn (`robot_spawner.py`).
- **MDP (Isaac Lab manager-based):** 6-D differential-IK arm action + binary gripper; 5-step history
  observation (joints, TCP pose, plate pose, goal pose, gripper); reaching / alignment / lifting /
  goal-tracking rewards; time-out, success, plate-dropped, arm-unstable terminations; plate re-spawned
  flat at a random pose each episode. One config file per stage (`*_env_cfg.py`).
- **Run it:**
  ```bash
  RL_DT/_isaaclab_tuberacking/docker/compose.sh up -d isaac-lab-base        # container
  docker exec -it isaac-lab-tuberacking bash
  cd /workspace/isaaclab && ./isaaclab.sh -p -m pip install -e dw_wellplate/WellPlate_RL/source/WellPlate_RL -e dw_tuberacking
  cd dw_wellplate/WellPlate_RL
  ../../isaaclab.sh -p scripts/zero_agent.py  --task Wellplate-Reach-v0 --num_envs 4 --headless   # sanity
  ../../isaaclab.sh -p scripts/rsl_rl/train.py --task Wellplate-Reach-v0 --num_envs 512 --max_iterations 500 --headless --video
  ```
  or the whole ladder: `START_STAGE=reach ./run_ladder_v2.sh`.

## 3. What was done (2026-09-14 → 09-21)

- 09-14: Alvika's tube task brought up on this machine; zero-action agent, first training video, table
  placement fixed; 86 % tube-reach in 300 iterations — proved the pipeline.
- 09-20: well-plate task built (package, scene with physics on Martin's plates, five stage configs,
  ladder driver, calibration probes); reach and align solved; a day of diagnosis on lift.
- 09-21: ladder run end-to-end unattended (lift/stack 0 % as predicted); presentation videos.

## 4. Issues found and resolved — all verified, all in git

| # | Issue | Fix |
|---|---|---|
| 1 | Alvika's config references a scene file (`TubeRacking_v2.usd`) not in Martin's repo; his `WellPlates.usd` has no tubes | task re-scoped to the well plate (Dewei) |
| 2 | Gripper weld joint targets a dead prim → gripper outside the articulation | Alvika's `fix_gripper_weld.py` applied (Martin's file patched in place) |
| 3 | **My bug:** two extra frames in the TCP `FrameTransformer` made frame 0 a finger link — three stages measured the gripper housing | single target; verified 0.20 m along the flange axis |
| 4 | Gripper meshes have no colliders (CollisionAPI on Xforms only) → fingers pass through the plate | colliders applied at spawn |
| 5 | Converted linkage lost its loop-closure joints → pads swing into a V | all finger joints driven with URDF mimic ratios (`mdp/mimic_gripper.py`) |
| 6 | Success as a *terminal* is reward-negative once shaping is dense (align fell 22 → 5 %) | success is a truncation (bootstrapped) |
| 7 | 2 cm / 15° / 10° first-pass tolerances score 0 even when converged | 4 cm / 20° first pass |
| 8 | Grasp height / closing axis: plate physics frame yawed 90° vs its USD prim; pads on top / in the table | closing axis = short side; pads 10 mm above the table |
| 9 | Laptop suspends on lid close; Kit start-up 17 min per stage with collider cooking | `HandleLidSwitch=ignore`; accepted overhead |

**Open (the blocker for stage 3):** with Martin's converted 2F-140 the fingertips sweep an arc and land
on the plate's top face during closing; the drives cannot hold the pads parallel under contact
(`results/gripper_short_side_tips_on_top_22-50.png`). The policy does its part — hovers within 5 mm,
aligns, closes at the plate 68–100 % of the time — but no plate was ever lifted in hand across eight
lift runs.

## 5. Plan and what is remaining

1. **Gripper:** swap in Isaac Lab's built-in parallel-jaw Robotiq 2F-85 for the RL work (~1 h), re-run
   lift; in parallel give Martin the evidence to fix the 2F-140 conversion (colliders, loop joints,
   weld, wrist offset). *Decision needed.*
2. Lift → stack → place with the working gripper (one night).
3. Re-run reach/align cleanly with the current config for publishable numbers (1 h each).
4. Then, per the 09-20 meeting: SAC (skrl) and the other libraries on the same task ids; camera-based
   plate detection (Alvika) replaces one observation term; domain randomisation beyond plate pose;
   force/torque limits.

## 6. Videos — where, and how to make more

Presentation set (rendered 09-21 morning, corrected camera and lighting):
`RL_DT/_isaaclab_wellplate/results/2026-09-21_presentation/`
`reach_viewA.mp4` · `reach_viewD.mp4` · `align_viewA.mp4` · `align_viewD.mp4` · `lift_viewA.mp4` ·
`lift_viewD.mp4` (+ `_mid.png` / `_end.png` frames). View A = oblique over the table (4 envs),
view D = close-up of the gripper (1 env). Per-stage training clips and replays are in
`results/<date>_<stage>/`; the gripper diagnosis frames are `results/gripper_*.png`.
Playback: Firefox/Chrome or VS Code (GNOME Videos lacks H.264).

Two problems in the first videos, both fixed: (a) the camera looked at world coordinates while
env 0 sits at (2.5, −2.5) → `viewer.origin_type = "env"`; (b) over-exposure → dome light 2500 → 600.
Any checkpoint can be re-recorded at any time without retraining:

```bash
# inside the container, from /workspace/isaaclab/dw_wellplate/WellPlate_RL
DISPLAY= ../../isaaclab.sh -p scripts/rsl_rl/play.py --task Wellplate-Reach-v0 --num_envs 4 --headless \
    --video --video_length 400 --load_run '.*_reach' --view A        # A oblique · B overhead · C side · D close-up
# -> logs/rsl_rl/wellplate/<run>/videos/play/rl-video-step-0.mp4
```
Presets live in `scene.py: VIEWS`; add one by giving an (eye, look-at) pair in env-0 coordinates.
During training, `--video --video_interval 2400` writes a clip every 100 iterations to
`<run>/videos/train/` (initial-state check = the step-0 clip).

## 7. TensorBoard

```bash
docker exec -it isaac-lab-tuberacking /workspace/isaaclab/isaaclab.sh -p -m tensorboard.main \
  --logdir /workspace/isaaclab/dw_wellplate/WellPlate_RL/logs/rsl_rl/wellplate --port 6006 --bind_all
```
then http://localhost:6006 (container uses host networking). Runs are named `<date>_<stage>`.
Curves that matter: `Episode_Termination/success` (the real metric), `Episode_Reward/<term>` (which
shaping term is doing the work — e.g. `grasp_ready` vs `lifting` was the lift diagnosis), and
`Train/mean_episode_length`.

## 8. Items for the team

- **Martin:** 2F-140 USD — no mesh colliders, loop-closure joints dropped, `AssemblerFixedJoint.body0`
  wrong, gripper ~25 cm off the flange; `WellPlates.usd` payloads an unloadable `.fbx`; the plate prim
  frame vs physics frame are yawed 90°. Frames in `results/gripper_*.png`.
- **Alvika:** FrameTransformer with several targets does not keep config order; success-as-terminal
  penalises success once shaping is dense — both apply to the tube task; `fix_gripper_weld.py` patches
  Martin's file in place, better upstream.
- **Reference:** `RL_DT_docs/_docs_legion/rounds/Round-2026-09-14-isaaclab-tuberacking.md`, `_isaaclab_wellplate/PROGRESS.md`.
