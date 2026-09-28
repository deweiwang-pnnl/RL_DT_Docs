# Round 2026-09-22 — Well plate: grasp fix, then the 2-plate stack

**Goal.** Resolve the lift blocker with Martin's robot (no built-in robot), then train the well-plate
ladder through a 2-plate stack with videos. Plan: `RL_DT/_isaaclab_wellplate/PLAN.md` v3 (approved
2026-09-26). Continues [Round-2026-09-14](Round-2026-09-14-isaaclab-tuberacking.md).

## Log

### 09-22 — Martin's GRIPPERFIX checked

- `_reference/digital_twin_models_updated_Martin_09222026/Ridgeback_UR7e_2f140_reworked.GRIPPERFIX.usd`
  is a 12 KB assembly layer. Against our 09-04 `RidgebackWithURGripper/Ridgeback_UR7e.usd` it composes
  every gripper prim as an undefined `over` (it expects `ur7e` under `RidgebackWithBasicJoints`; ours
  has it beside `RidgebackWithStructure`), so the weld target is missing and the gripper sits 0.86 m
  from the wrist. Its gripper payload is `2f140_reworked.usd` (the file Martin's README calls broken;
  `PhysxDrivePerformanceEnvelope` still applied). Not usable. Inspection ran with the host Isaac Sim
  `pxr` libs, no simulator.
- Our training robot `Ridgeback_UR7e_2f140.usd` embeds NVIDIA `Robotiq_2F_140_physics_edit`: mimic
  on the right knuckle, loop-closure joints excluded, exact parallelogram (100 mm / 19 mm), joint frames
  consistent, gripper base coincident with the wrist (the "25 cm off the flange" item for Martin does
  not hold for this file).

### 09-25 — Message to Martin

Asked for one self-contained robot USD with the `physics_edit` gripper. No reply by 09-26; we proceed
on our own.

### 09-26 — Cause of the lift failure (on paper), plan v3 approved

- Pads travel ~18 mm along the approach axis while closing from full open to the 85 mm contact
  (four-bar geometry from the USD anchors) → pads started 10 mm above the table hit it at ~0.17 rad
  (observed stall 0.24 rad), or closed over the plate top when higher.
- `mdp/mimic_gripper.py` drove `*_inner_finger_pad_joint` to 0; in the USD that joint closes the loop
  (inner_finger → inner_knuckle) and must be at +q (Isaac Lab's `set_finger_joint_pos_robotiq_2f140`
  sets +q). The URDF joint of the same name is a fixed pad mount — the ratio was copied from there.
- The 09-20 "no colliders" conclusion rested on an invalid teleport test; to be A/B-tested (G2).
- Decisions: see PLAN.md v3 §1.

### 09-26 — Part A: grasp fixed and verified (gate 16/16)

Evidence and chronology: `RL_DT/_isaaclab_wellplate/results/2026-09-26_gripper_fix/README.md`.

- **Sweep (in the air, robot gravity off):** G0 pads tilt into a V (12° at the 85 mm contact, 24° closed); with the
  pad joint at +q the pads stay at 0.0°. Pad travel toward the table from full open to contact: 18.4 mm measured,
  18.3 mm predicted. Grasp height 16 mm above the plate root → pads 9.7 mm above the table at the 112 mm pre-open,
  3 mm at contact. Figures F1–F3, video V1.
- **Grasp probe** needed three fixes before it measured the gripper at all: the align policy hovered 4–9 cm off; relative
  IK plateaus 1–5 cm off even with robot gravity off (stalls ~0.3 m short with gravity on) → scripted joint-space pose
  controller; FrameTransformer data is stale right after reset → one step before reading it.
- **Closing axis wrong since 09-20 21:45:** plate body x = 127.6 mm, y = 85.4 mm (USD geometry relative to the plate
  prim); `CLOSING_AXIS_INDEX` 0 → 1. Lift run 8 on 09-20 closed across the 128 mm side.
- **Pads sank through the plate under a two-sided squeeze** (one-pad push moved it; trace shows no pause at contact).
  Grip effort, closing speed, plate mass, plate depenetration alone did not fix it. Isaac Lab's UR10e + 2F-140 contact
  settings did (robot max depenetration 5, max contact impulse 1e32, 5 mm contact / 0 rest offset; plate 32 iterations,
  5 mm contact offset).
- **G1 (all finger joints driven, 8 N·m) spins the plate out; G2 (Isaac Lab drives, mimic kept, NVIDIA colliders as
  shipped) holds 16/16, lifted 99.5 mm, tilt 0.6°.** Default is now G2 + reference physics; verified again without
  overrides (16/16).
- Other defects found: the 09-20 pad box colliders were placed in the wrong frame (finger link frames are rotated vs
  the gripper base); Isaac Lab's IK action applies the TCP-offset Jacobian correction in the body frame (sign wrong
  with the gripper pointing down; slows convergence, not the plateau's cause); ContactSensor with a filter read 0 N
  during a push that moved the plate — not trusted here.

### 09-26 afternoon/evening — ladder v3: align → lift → stack (2 plates)

Chronology with every diagnosis: `RL_DT/_isaaclab_wellplate/PROGRESS.md` (09-26 entries). Deterministic evaluation,
128 episodes each: **align 82.0 %, lift 87.5 %, 2-plate stack 50.8 %** at the training tolerances; strict 0.0 / 14.8 /
22.7 %. Evidence set for the team: `results/2026-09-26_summary/`.

- Robot gravity off (Dewei; realistic arm later): arm reaches IK targets to 0.2 mm vs ~410 mm off with gravity on.
- Ladder gate moved to the deterministic eval: with a binary gripper, exploration noise flips the grip open, so the
  training success under-reports (lift 19.9 % noisy vs 87.5 % deterministic).
- PPO action std grew 1.0 → 3.7 across warm-started stages (entropy 0.01, actions clipped to ±1) and collapsed stack →
  entropy 0.001, std reset to 0.5 at warm start (`scripts/reset_action_std.py`).
- Stack reward bugs: goal terms and `lifting` were gated at rest + 4 cm while the stacked plate sits at rest + 2.6 cm,
  so placing lost reward → gated at rest + 1 cm, `placed` term, grasp_ready 5 → 1.
- Placed but never released (gripper mean −3, std 0.5) → gripper-only exploration std 2.0 → 28.9 % → 50.8 %.
- Tools added: `eval_policy.py` (+ `--diag_stack` timeout diagnostic), `record_labelled.py` (captioned consecutive
  episodes), `probe_plate_frames.py`, view preset S (stack target close-up).

### 09-26 night → 09-27 morning — PLAN v4: centred 2-plate stack (unattended, "work to the end")

Chronology: `RL_DT/_isaaclab_wellplate/PROGRESS.md` (09-26 night / 09-27 entries). Evidence:
`results/2026-09-27_centered/` (README, F5, F6, V5). **Final criteria — centring ≤ 5 mm, twist ≤ 3° (long edges,
0°/180° equal), tilt ≤ 3°, released at rest: 90.6 % deterministic over 128 episodes** (target ≥ 40 %; the 09-26 stack
policy 0.0 %). Successful episodes: median 2.4 mm, 0.9° twist, 0.0° tilt. Final policy
`2026-09-27_10-59-14_centered/model_20593.pt`, task `Wellplate-Centered-v0`.

- Curriculum (deterministic): C1a 15 mm/45°/5° 67.2 % → C1b 30° 67.2 % → C1c 20° 73.4 % → C1 10° 85.2 % →
  C2 10 mm/5°/3° 87.5 % → C3 5 mm/3°/3° 90.6 %.
- Twist measured on the long edges; the target mesh is rotated 48.97° inside its prim.
- Twist observation (sin 2Δ, cos 2Δ) added; checkpoints widened with zero weights (`scripts/widen_obs_checkpoint.py`).
- Adaptive LR pinned at its 1e-5 floor → fixed 1e-4; wrist-yaw action scale 0.1 (only ~15 % of a relative command is
  realized per step). A probe showed turning the grasped plate is physically easy (42° → 5.7°).
- Success only below 10° twist rewarded nothing → twist curriculum 45° → 30° → 20° → 10°.
- Placed but never released: the success bonus (weight 50 × dt = 1.7 once) was below the critic's noise under
  truncation bootstrapping → weight 600 (C1a 1.6 % → 67.2 %).
- Driver bug (C1 restarted from the 09-26 policy after C1a–C1c) caught within a minute.

### 09-27 — PLAN v5: three plates, loose bottom plate, realistic arm (Dewei: "go ahead to the end of the plan")

Chronology: `RL_DT/_isaaclab_wellplate/PROGRESS.md` (09-27 entries); evidence `results/2026-09-27_stack3/` (README,
F7, F8, V6, V7). All results deterministic, 128 episodes, each placed plate within 5 mm / 3° twist / 3° tilt of the
one below, released, lower plate still in place (gate ≥ 40 %):

| Step | Setting | Result | Baseline |
|---|---|---|---|
| E1 | 3 plates, next plate handed off into the pick area | **52.3 %** | 0 % (C3 alone) |
| E2 | 3 plates, all loose (plate 3 in its own pick area) | **46.1 %** | 26.6 % |
| E3 | as E2, bottom plate loose (50 g, moved ≤ 1 cm) | **49.2 %** | — |
| E4 | as E3, realistic arm (robot gravity on + compensation torques) | **54.7 %** | no retraining needed |

- Third plate = Martin's `WellPlate_01` made dynamic at spawn; role stand-ins (`mover` / `base` / `lower`) let every
  existing term follow the plate being moved and its base; tasks `Wellplate-Stack3{Handoff,Loose,LooseBottom}-v0`, E4
  `Wellplate-Stack3LooseBottomRealArm-v0`.
- One policy for both placements failed (quaternion flip of a 180°-symmetric base; then catastrophic forgetting of the
  first placement — swap test: weights, not normaliser; then learned avoidance of grasping). **Two skills**: the C3
  policy places the first plate, a second policy fine-tuned from it the second (evaluator `--checkpoint2`).
- Second placement learnable only with a **rising stack** (kinematic middle plate 0 → 26 mm: 80–92 %; trained at full
  height directly 0.8 %) and **start states recorded at real hand-offs** (the second skill's first move otherwise
  dragged the plate just placed: > 5 mm in 61 % of envs within 0.17 s) plus a displacement penalty.
- Loose bottom plate: displacement penalty + **mass curriculum** 20 kg → 50 g for the first skill (untrained 11.7 %).
- Realistic arm: gravity-compensation torques from PhysX inverse dynamics every physics step; tracking identical to
  gravity off (434 mm off without compensation) → skills transfer unchanged.

## Open

- Strict precision of the 09-26 ladder (lift 10 cm: 14.8 %) — superseded for stacking by the centred policy (90.6 % at 5 mm).
- Centred stack failures at C3: 7.8 % time out (mostly the plate never picked up cleanly), 1.6 % drops.
- Three-plate failures in the final setting: 36 % time-outs (second placement unfinished or middle plate pushed out of
  tolerance), 9 % drops. Single seed per training run.
- Realistic arm (gravity on + compensation) — Dewei: later.

## Next

Dewei's review of PLAN v5 (3 plates, loose bottom plate, realistic arm done; library comparison E5 in PROGRESS.md /
`results/2026-09-27_libs/`). Not in D4: camera-based plate detection (Alvika), a single policy for both placements.
