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

## Open

- Robot gravity and arm gains in training (relative IK cannot hold small corrections): Dewei's decision.

## Next

Show Dewei F1–F3, V1, V2, S1 and the gate; then A4 smoke test and the overnight ladder v3 (G2).
