# Round 2026-09-14 — Isaac Lab on the tube-racking task

**Goal.** Isaac Lab only, toolkit paused. Learn the framework on Alvika's `digitaltwin_rl-master`
(TubeRacking_RL) with Martin's 09-04 assets: zero-action agent, video from `logs/`, the four RL
libraries side by side, then a first pass at the racking reward. Work lives in
`RL_DT/_isaaclab_tuberacking/`; `_toolkits/` untouched.

**Context (Dewei's notes 09-03 / 09-10).** Env-robot `RidgebackWithURGripper/Ridgeback_UR7e_2f140.usd`;
env-task `ENV_TubeRacking_UR/WellPlates.usd`; Alvika's active config
`tuberacking_rl_env_cfg_DTreorg.py`. Martin will split robot and tube into separate USDs. Reward
design is ours; Alvika handles camera-detected locations.

## Plan

1. Mount and register — **done**
2. Fix USD path (`TubeRacking_v2.usd` does not exist → `WellPlates.usd`), zero-action agent, write-up
3. Video from `logs/` — short rsl_rl run, `play.py --video`, `record_reset_validation.py`
4. rl_games, skrl, sb3 on the same task
5. Reward design — reading + proposal (waits on Martin's split)

## Log

### Before the round — folder cleanup

- Martin's 09-04 `digital_twin_models-DT_reorg (2)` replaces the 08-25 copy. Diff: 2F-85 and
  2F-140-reworked gripper variants, `Ridgeback_UR7e_2f85/2f140_reworked.usd`, TubeRacking rigid
  rack + `WellPlates.usd`, Labware additions, modified `Ridgeback.usd` / `ur7e.usd`. **Door task
  code unchanged** — D10 not addressed.
- `isaaclab_dt-main (2)` was the *older* pristine export, not an update; kept the working copy,
  copied in the six dotfiles it lacked, deleted `(2)`.
- Our `RL_CloudTesting/` additions were already in `_toolkits/toolkit-isaaclab/isaac_integration/`;
  four stragglers copied over. 867 MB of root-owned container logs parked in
  `RL_Twin/_old_DT_root_owned_leftovers/` for `sudo rm`.

### Step 1 — mount and register (done)

- Second container `isaac-lab-tuberacking` from the existing image via a compose override +
  own env file (`RL_DT/_isaaclab_tuberacking/docker/`); the toolkit container keeps running.
  Note: that older container's `envs_external` bind now points at the *stale* inode of the
  replaced DT folder — recreate it before using it again.
- `pip install -e source/TubeRacking_RL` → `Template-Tuberacking-Rl-v0` listed by `list_envs.py`.
- Gotcha: `PYTHONUNBUFFERED=1` needed or `simulation_app.close()` eats the printed output.

## Open

- `FALCON_ENV_USD` in the active config names `TubeRacking_v2.usd`, absent from Martin's folder.
- `TUBE_PRIM_REL = /TubeRacking/Environment/FalconTube_50ml_01` must be checked against `WellPlates.usd`.
- Container writes root-owned files through the mounts.

## Next

Step 2.

### After step 1 — assets inspected, guide written

- `RL_DT` tracked from now on, one commit per implementation (`04f551c`, then the guide).
- **All three `ENV_TubeRacking_UR` USDs embed a robot.** `WellPlates.usd` = UR7e + 2F-140 + table
  + three 6-well plates, **no tubes, no rack**; `TubeRacking.usd` and `_rigidTubeRack.usd` = the
  *older* UR5e + 2F-85 robot + 4 Falcon tubes + rack. Alvika's config spawns the robot separately
  and expects a tubes-only `TubeRacking_v2.usd` that Martin's folder does not contain. Loading
  any of the three as-is gives a second robot; `WellPlates.usd` also leaves `TUBE_PRIM_REL`
  unresolved. This is the split Martin promised on 09-10.
- Inspector script: `usd_tree.py` (run through `isaaclab.sh -p … --headless`; bare `python.sh`
  has no `pxr`). Kept in `RL_DT/_isaaclab_tuberacking/scripts/`.
- Guide written for printing: `RL_DT/_isaaclab_tuberacking/GUIDE-isaaclab-and-docker.md` —
  Docker, Isaac Lab anatomy, zero-action agent, the four RL libraries, video, cheat sheet.

### Step 2a — new `WellPlates.usd`, first zero-agent attempt

- Dewei re-downloaded `WellPlates.usd` (14 KB, 09-14 07:56): **environment only** — table, ground,
  `WellPlate`/`WellPlate_01` (static meshes), three `_6WellPlate_thin*` prims whose payload is a
  `.fbx` USD cannot open (typeless in the tree). 0 rigid bodies, 0 articulations. Robot
  `Ridgeback_UR7e_2f140.usd` matches Alvika's `ROBOT_CFG` as-is (articulation root, `ur7e_*`
  joints, `finger_joint`).
- Edited `tuberacking_rl_env_cfg_DTreorg.py`: `FALCON_ENV_USD` → `WellPlates.usd`, dated comment
  keeps the old value. (Lives in `digitaltwin_rl-master`, outside `RL_DT` git.)
- `zero_agent.py --num_envs 1 --headless`: scene creation OK (0.45 s, robot + table loaded), then
  `RuntimeError: Could not find prim with path /World/envs/env_.*/TubeTable/TubeRacking/Environment/FalconTube_50ml_01`
  — the `tube` RigidObject. Exactly the predicted first failure; nothing else complained.
- Warnings for Martin: robot USD references `C:/users/prat615/.../camera.usd` (Gemini335L camera
  mesh, cosmetic); `WellPlates.usd` payloads `Labware/WellPlates/96WellPlate_thin.fbx` (unloadable).
- Found `Labware/FalconTube_50ml.usdc` — standalone tube mesh, no physics APIs. Isaac Lab's
  `UsdFileCfg(rigid_props=…)` only *modifies* an existing RigidBodyAPI (`schemas.modify_*`), it
  does not add one, so spawning it directly is not enough.

### Step 2b — tube spawned (option A), gripper weld found broken

- Alvika's pattern was: robot spawned separately; scene USD `TubeRacking_v2.usd` (her own
  robot-free edit of Martin's file, never committed) spawned static; tube wrapped with
  `spawn=None` because it already carried `RigidBodyAPI`. The new `WellPlates.usd` has no tube.
- Built `dw_tuberacking.tube_spawner.TubeCfg` (`RL_DT/_isaaclab_tuberacking/`, pip-installed in
  the container via a third bind mount): references `Labware/FalconTube_50ml.usdc` and applies
  rigid body + convexHull collision — the schemas Martin's scene tubes carry. Tube mesh is the
  same `Cylinder_017` (30 × 116 mm, metres, Z-up), so Alvika's quaternions still apply.
  Config change: `tube.prim_path="{ENV_REGEX_NS}/Tube"`, `spawn=TubeCfg(usd_path=TUBE_USD)`.
- Zero-agent now passes scene creation and simulation start, then fails on the **robot**:
  `finger_joint` absent from the articulation (only 3 base + 6 arm joints), PhysX error
  "PhysxMimicJointAPI … not part of an articulation".
- Cause: `AssemblerFixedJoint.body0` in `Ridgeback_UR7e_2f140.usd` targets
  `…/ur7e/ur7e/wrist_3_link` (an empty leftover prim) instead of `…/ur7e_wrist_3_link`.
  Alvika's `scripts/fix_gripper_weld.py` retargets it and **saves Martin's file in place**.
  → Asset bug for Martin.

### Step 2c — weld fixed (option B), zero-action agent runs

- Dewei chose option B: ran Alvika's `fix_gripper_weld.py`, which rewrote
  `RidgebackWithURGripper/Ridgeback_UR7e_2f140.usd` in place (`AssemblerFixedJoint.body0`:
  `…/wrist_3_link` → `…/ur7e_wrist_3_link`). Original kept beside it as
  `Ridgeback_UR7e_2f140.usd.orig-2026-09-04`. **Re-apply after any re-download of the DT folder.**
- `zero_agent.py --num_envs 1 --headless`: **runs.** Scene 0.78 s, sim start 0.58 s,
  obs `(1,160)` = 5-step history × (6 joint pos + 6 joint vel + 7 ee pose + 7 tube pose + 6 last
  action), action `(1,6)`, TCP–tube distance at reset 0.415 m, 1 800+ steps without error
  (stopped by hand at 120 s). Managers: 1 action term, 2 reset events (`reset_robot`,
  `reset_tube`), 7 reward terms (reaching 0.1, success_bonus 30, align_tube 0.05,
  gripper_down 0.03, three L2 penalties), 4 terminations (time_out, success, tube_dropped,
  arm_unstable).
- Remaining PhysX warning: `ur7e_robot_gripper_joint` (Martin's fixed joint, `body1` empty)
  has "disjointed body transforms … will snap objects together". Harmless so far; one more for
  Martin.
- Open: `--num_envs 4`, a render to *see* the scene (step 3), and the tube's settled pose vs
  `TUBE_SPAWN_Z` — not checked yet, only the TCP distance.

### Step 3 — working copy, placement fix, first learning run with video (done)

- **Working copy**: `RL_DT/_isaaclab_tuberacking/TubeRacking_RL/` (rsync of `digitaltwin_rl-master`,
  no logs) is now the container's `external_projects`; Alvika's original restored pristine.
  `.gitignore` in `RL_DT` no longer drops `.mp4`/`.pt`/`videos/` (Dewei: track everything).
- **First video** (16 envs, 20 it.) showed the problem: table is a 1.0 m cube at Alvika's
  `TABLE_POS`, 1.5 m from the robot; tube spawned in open air, free-fell, `tube_dropped` after 4
  steps in every episode. Probes: `scripts/probe_tube_drop.py`, `probe_scene_bounds.py`.
- **Fix** (working copy only): `TABLE_POS (1.2,-1.0,0) → (0.78, 0.75, 0)` so the cube's +x edge
  (1.32) sits against the base footprint (x ≥ 1.333) under the spawn rectangle; rectangle
  trimmed to x 1.13–1.27, y 0.55–0.88 (edge, well plate). Verified: tube settles at z = 1.014 on
  the table, 4 envs × 40 steps, no drops.
- **rsl_rl PPO, 512 envs, 300 iterations (~20 min)**: success 0 → **0.86**, episode length
  289 → 72 (ends on success), `tube_dropped` ≈ 4 %. Videos at it. 0/100/200 and a
  `play.py --video` replay of `model_299.pt` (exports `policy.pt/.onnx`).
  `results/2026-09-14_rsl_rl_300it/` — commits `22176a2`, `a384095`.
- Lesson: leftover `python` processes inside the container after `pkill` on the host wrapper
  starve later runs — kill with `docker exec … pkill -9 -f scripts/`.
- Not done: camera pose for a presentable video (`env_cfg.viewer`); step 4 (other 3 libraries);
  step 5 (reward design).

## 2026-09-20 — re-scoped to the well-plate task; overnight ladder launched

- Dewei's correction: the task is the **well plate**, not the tube. `WellPlates.usd` inspected: a 1 m
  cube table, three identical 96-well plates (128 × 85 × 26 mm) flat side by side, no holder, no
  physics. Decisions: T2 stacking onto Martin's second plate; his three plates with physics added
  at spawn; binary gripper; base locked; PPO/rsl_rl only tonight.
- New folder `RL_DT/_isaaclab_wellplate/` — `PLAN.md` (v2.1), package `WellPlate_RL` with five
  stage configs sharing one 7-D action / 205-D observation layout so checkpoints warm-start the
  next stage, `run_ladder.sh` (gates, one loosened retry, videos from views A/B, commit per stage),
  `PROGRESS.md` (the morning read). Commit `c80cd2c`.
- Calibration: plate root = mesh centre, rests at z 1.013; local x = long side; stack target at
  (1.16, 1.00); gripper closes on **negative** binary action, mimic knuckle follows.
- Smoke test (64 envs × 6 it., Hydra override, video) clean; ladder launched ~09:10 host time:
  reach 500 → align 500 → lift 1000 → stack 1500 → place 1500 iterations, 512 envs.

## 2026-09-20 (day) — the well-plate ladder: reach and align solved, lift blocked by the gripper asset

- **Result:** reach 96.7 %, align 96 % (loosened tolerance) with the corrected TCP frame; lift 0 % after
  eight relaunches, each one fixing a real, verified defect. Everything is in `RL_DT/_isaaclab_wellplate/`
  (`PROGRESS.md` is the chronology, `results/gripper_*.png` the evidence), commits up to `7057c75`.
- **Defects found, in order:** (1) v1 driver captured its own echo as the success number; (2) Martin's
  2F-140 USD has collision APIs on Xforms, none on the meshes → colliders added at spawn; (3) two probe
  frames I added made FrameTransformer index 0 a finger link → three stages measured the gripper housing
  (my bug; fixed, verified); (4) strict first-pass tolerances score 0 even when the policy converges;
  (5) success as a *terminal* is reward-negative once shaping is dense → success is a truncation now;
  (6) the converted linkage lost its loop joints → pads swing into a V; driving all finger joints to
  the URDF mimic ratios makes them parallel; (7) grasp height had to move three times (pads on the plate
  top / in the table / 10 mm clearance); (8) the plate's physics frame is yawed 90° vs its USD prim
  frame → closing axis flipped to the short side; finger drive too strong (plate flipped) then too weak.
- **State at 22:45:** lift run 8 hovers precisely, aligns partially, closes at the plate (`grasp_ready`
  0.68) — and never lifts it in hand. Whether the pinch holds is the open question; needs the GUI.
- **Also:** start-up is ~17 min per stage since the collider cooking; the laptop suspended twice (lid);
  probes alongside training slow it 4×; eight relaunches cost the day. Lessons in memory
  (`feedback_isaaclab_pitfalls.md`).
- **For Martin:** gripper meshes have no colliders; loop-closure joints dropped in conversion; weld joint
  `AssemblerFixedJoint.body0` wrong; gripper base sits ~25 cm off the wrist flange in the assembly;
  `WellPlates.usd` payloads an unloadable `.fbx`. **For Alvika:** the FrameTransformer ordering and the
  success-as-truncation findings apply to her config too.
