# PROGRESS — well-plate ladder (plain-language log for the morning read)

## 2026-09-20 evening — setup and calibration (done with Dewei watching)

- Package `WellPlate_RL` built from Alvika's tree; five task ids register (`Wellplate-Reach/Align/Lift/Stack/Place-v0`).
  Mounted at `/workspace/isaaclab/dw_wellplate`, pip-installed editable in `isaac-lab-tuberacking`.
- Scene: Martin's `WellPlates.usd` at the verified table pose; his three plates get physics at spawn
  (`scene.py: spawn_wellplates_table`): `Environment/WellPlate` = object (rigid, 50 g, friction 0.8),
  `WellPlate` = stack target (kinematic), `WellPlate_01` = static obstacle.
- Calibration probe (`scripts/probe_scene.py`, 4 envs):
  - plate root = mesh centre; rests at z = **1.013** on the cube top (all envs); top face +0.013
  - plate local x = long side (extents 0.142 × 0.108 × 0.026 in its frame) → fingers close along local y
  - stack target root (1.160, 1.004, 1.015), yaw = table yaw (−95°), 0.64 m from the robot base
  - TCP–plate 0.55–0.63 m at reset; arm home puts the TCP at z 0.885 beside the cube (x 1.67 > edge 1.32)
  - gripper: all 10 joints are articulation DOFs, `finger_joint` ∈ [0, 0.785]; **binary action closes on
    negative values** (Isaac Lab convention); close → 0.70 rad with the right knuckle mimicking (0.699)
- Not measured: fingertip pad separation when closed (link origins all coincide with the base in Martin's
  USD, so body positions don't show it). Stage 3's `lifting` reward is the test.

## Ladder run started Sun 20 Sep 2026 02:12:17 AM PDT

- 02:12 container up, packages installed, calibration done (see scene.py constants)
- 02:12 train reach: 500 iterations, 512 envs  
- 03:43 reach: success=[02:12] train reach: 500 iterations, 512 envs  
0.841 (gate 0.6)
- 03:50 (Claude) the "reach: success=[02:12] …" line above is a driver bug — v1 captured its own
  log echo as the success number, so the gate check errored and was skipped. **Real reach success:
  0.841 (mean of last 20 it.), 0.86 at it. 499 — gate 0.6 passed.** Curve: 0 → 0.19 (it. 250) →
  0.65 (300) → 0.83 (350) → 0.86 (499). Fixed in `run_ladder_v2.sh`, which takes over at the start
  of the align stage (START_STAGE=align); nothing from reach is lost.
- 03:52 recorded reach → results/2026-09-20_reach
- 03:52 train align: 500 iterations, 512 envs (warm start from reach) 

## Ladder run started Sun 20 Sep 2026 03:52:39 AM PDT

- 03:52 container up, packages installed, calibration done (see scene.py constants)
- 03:52 reach: skipped (done by the earlier driver, success 0.841 (earlier driver))
- 03:52 train align: 500 iterations, 512 envs (warm start from reach) 
- 04:05 (Claude) reach replay videos re-recorded with the camera made env-relative
  (`viewer.origin_type="env"` in base_env_cfg — the first cut looked at world (1.05, 0.75) while env 0
  sits at (2.5, −2.5)). `results/2026-09-20_reach/play_viewA_last.png` shows the trained policy: arm over
  the cube, gripper above the white plate, yellow plate = stack target. Later stages record correctly.
- 05:32 align: success=0.000 (gate 0.5)
- 05:32 align below gate → retry once with loosened tolerances: env.terminations.success.params.threshold=0.04 env.terminations.success.params.min_down=0.94 env.terminations.success.params.min_align=0.94
- 05:32 train align: 500 iterations, 512 envs (warm start from align) env.terminations.success.params.threshold=0.04 env.terminations.success.params.min_down=0.94 env.terminations.success.params.min_align=0.94
- 05:45 (Claude) align stage: 0 % success after 500 warm-started iterations. Diagnosis (probe
  `scripts/probe_gripper_extent.py`): fingertips end 7.6 mm past the TCP, open gap 144 mm, fingers
  separate along base y — geometry is fine; the problem is the grasp point at "top face + 5 mm": the
  fingertips land on the plate unless yaw is already aligned, and the alignment shaping (weight 0.05)
  was too weak to teach align-then-descend. The driver's loosened retry (20° yaw/tilt, 4 cm) is running.
  For every later process start: GRASP_POINT → plate-root height (pads 5 mm above the table, over the
  whole plate side — also the right height for a real grasp) and align_plate weight 0.05/0.2 → 0.3.
  Lift will warm-start from whatever align produces; the ladder continues regardless of the gate.
- 07:07 align (loosened): success=0.964
- 07:16 recorded align → results/2026-09-20_align
- 07:16 train lift: 1000 iterations, 512 envs (warm start from align) 
- 08:15 (Claude) lift stage ~200 it. in: aligned at the grasp point, `lifting` ≈ 0. Four scripted grasp
  tests were all inconclusive (my placement geometry, arm sag, and direct IK deltas that did not move the
  arm — open question for a GUI session); the finger Xforms do carry CollisionAPI + convexHull + a physics
  material, so contact should exist. Probes stopped — they were sharing the GPU and slowed training 4×.
  Lift continues on its own (800 it. + retry); stack/place follow regardless of its gate.
- 09:20 (Claude) **lift stage failed for a physical reason**: the gripper had no colliders. Martin's USD
  puts PhysicsCollisionAPI on the finger *Xforms*; PhysX only builds shapes from mesh gprims, so a closing
  gripper passed straight through the plate. Over 800 iterations the policy learned to *flick* the plate
  (lifting reward sporadic, plate_dropped 2 % → 11 %, reward 16 → 2.6). Fix: `robot_spawner.py` applies
  convexHull colliders + a friction-1.0 material to all 11 gripper meshes at spawn; `lifting` and
  `lift_success` now require the plate within 4 cm of the TCP (held, not flicked). Lift is relaunched from
  the align checkpoint with the fix; the first lift run stays in results/ as the record of the failure.
- 09:55 (Claude) contact test (`scripts/probe_finger_contact.py`): with the new colliders a plate placed
  inside the pads is kicked 0.48 m sideways instead of falling straight through — **fingers now collide
  with the plate.** (Three earlier scripted grasp tests were invalid: pinning/teleporting overrides the
  solver; the IK-driven one never reached its target. Kept in scripts/ for reference.)
- 10:13 (Claude) old lift run (no colliders) stopped at ~it. 2400/2497 to save the night; lift relaunched from the align checkpoint with the fixed gripper (START_STAGE=lift)

## Ladder run started Sun 20 Sep 2026 10:13:45 AM PDT

- 10:13 container up, packages installed, calibration done (see scene.py constants)
- 10:13 reach: skipped (done by the earlier driver, success 0.841 (earlier driver))
- 10:13 align: skipped (done by the earlier driver, success 0.964 (earlier driver))
- 10:13 train lift: 1000 iterations, 512 envs (warm start from align) 
- 11:50 (Claude) **ROOT CAUSE of the lift failure — my bug, found and fixed.** For the 09-20 calibration
  probe I had added two finger frames to the `ee_frame` FrameTransformer. With several targets the frame
  order is not the config order: index 0 became a finger link, whose origin coincides with the gripper base
  in Martin's USD and which carries no TCP offset. So every reward, observation and success test in reach,
  align and lift measured the **gripper housing**, not the TCP 0.20 m out — the policy learned to park the
  housing 5.3 cm above the plate (housing half-thickness 3.8 + plate top 1.3), lying sideways on it, and
  "gripper down" was a finger link's axis. Verified after the fix (`scripts/probe_tcp_frame.py`): one
  target, TCP 0.20 m along the base z, orientation identical. The reach/align checkpoints learned the wrong
  point, so the ladder restarts from reach. Old results kept as `results/2026-09-20_{reach,align}_wrongframe/`.
  The gripper-collider fix from 09:20 stands (it was real and separate).

## Ladder run started Sun 20 Sep 2026 11:35:23 AM PDT

- 11:35 container up, packages installed, calibration done (see scene.py constants)
- 11:35 train reach: 500 iterations, 512 envs  
- 13:09 reach: success=0.000 (gate 0.6)
- 13:09 reach below gate → retry once with loosened tolerances: env.terminations.success.params.threshold=0.04 env.terminations.success.params.min_down=0.94
- 13:09 train reach: 500 iterations, 512 envs (warm start from reach) env.terminations.success.params.threshold=0.04 env.terminations.success.params.min_down=0.94
- 13:15 (Claude) corrected reach run: reward/reaching rise steadily (best yet), no drops, but the policy
  settles just outside the strict 2 cm / 15° box → success 0 %; the 4 cm / 20° retry is running. First-pass
  tolerances of reach and align set to those retry values so later stages don't lose an hour each; the retry
  mechanism then acts as a continuation.
- 13:30 (Claude) the reach retry hung at start-up (18 min, no iteration, GPU idle): my config-check probe
  started a second Kit instance while it was starting and both share the shader-cache volumes. Killed;
  ladder relaunched from reach (fresh first pass at the 4 cm / 20° tolerance). Rule from here: no probes
  while a training process is starting.

## Ladder run started Sun 20 Sep 2026 01:28:59 PM PDT

- 13:28 container up, packages installed, calibration done (see scene.py constants)
- 13:28 train reach: 500 iterations, 512 envs  
- 13:42 (Claude) correction: the 13:09 retry was not hung — start-up now takes ~17 min (scene 400 s +
  simulation start 600 s, vs 2 min this morning) because of the convex-hull cooking for the gripper
  colliders and plates across 512 envs. I killed a run that was about to start. The 13:28 relaunch is on the
  same schedule; expected iteration 0 at ~13:46. Start-up cost per stage is a known overhead now
  (optimisation candidate: cook once / instanceable colliders), not a fault.
- 14:46 reach: success=0.967 (gate 0.6)
- 14:49 recorded reach → results/2026-09-20_reach
- 14:49 train align: 500 iterations, 512 envs (warm start from reach) 
- 16:03 align: success=0.054 (gate 0.5)
- 16:03 align below gate → retry once with loosened tolerances: env.terminations.success.params.threshold=0.04 env.terminations.success.params.min_down=0.94 env.terminations.success.params.min_align=0.94
- 16:03 train align: 500 iterations, 512 envs (warm start from align) env.terminations.success.params.threshold=0.04 env.terminations.success.params.min_down=0.94 env.terminations.success.params.min_align=0.94
- 16:12 (Claude) align: 5.4 % at the gate but the curve tells the real story — 21.6 % at iteration 50, then
  down to 4–8 % while reaching/alignment rewards kept rising: success *terminated* the episode and forfeited
  ~0.5/step of shaping, more than the 30 bonus, so the agent learned to hover just outside the box. Fix:
  success is now a truncation (`time_out=True`) in align/lift/stack/place — rsl_rl bootstraps the value at
  the cut, so succeeding is pure gain; the metric is unchanged. The align retry (same flaw) was cut; lift
  relaunched now, warm-started from the align checkpoint (which hovers aligned at the grasp height).
  Align videos will be recorded in the final pass.

## Ladder run started Sun 20 Sep 2026 04:05:07 PM PDT

- 16:05 container up, packages installed, calibration done (see scene.py constants)
- 16:05 reach: skipped (done by the earlier driver, success 0.967 (earlier driver))
- 16:05 align: skipped (done by the earlier driver, success nan (earlier driver))
- 16:05 train lift: 1000 iterations, 512 envs (warm start from align) 
- 17:35 (Claude) lift (with the frame fix) hovered at the grasp point but never lifted in hand (0 over ~150 k
  episodes). Close-up `results/…/grasp_d2.png` and a valid descent test: at the grasp height the fingertip
  pads touch/penetrate the table (they were 5 mm above it by geometry; contacts are soft under the arm's
  drives), and when closing the fingers pass the 85 mm contact angle. Changes: grasp point +1.5 cm (pads
  2 cm above the table, over the top 19 mm of the plate side), gripper effort 30 → 8 N·m, solver iterations
  16/4 on the robot and the plate. Lift relaunched from the align checkpoint. **Asked Dewei for a GUI
  check of one grasp** — the remaining uncertainty is whether the pads collide with the plate at all.

## Ladder run started Sun 20 Sep 2026 05:25:13 PM PDT

- 17:25 container up, packages installed, calibration done (see scene.py constants)
- 17:25 reach: skipped (done by the earlier driver, success 0.967 (earlier driver))
- 17:25 align: skipped (done by the earlier driver, success nan (earlier driver))
- 17:25 train lift: 1000 iterations, 512 envs (warm start from align) 
- 18:25 (Claude) crude P-control tests are unusable in contact: the arm drives (150 N·m) plow the fingers
  into the table and fold the finger joint *past its lower limit* (−0.09 … −0.79 rad) — which does prove the
  fingers collide with the table. The lift policy's hover scatters ±4 cm in height (its success box),
  wider than the plate is tall, so the pads land in the table or above the plate. Running a gentle scripted
  grasp (≤ 0.75 cm/step) to read the finger angle at closure.
- 18:45 (Claude) gentle scripted grasp also ended in the table (the IK+PD arm is not compliant; the fingers
  fold out of the way) and the plate never moved in any test. Training evidence is decisive on its own:
  `lifting` exactly 0 over two lift runs (>250 k episodes) — the grasp is not discoverable by exploration
  as designed. Added to lift/stack: `fine_reaching` (std 2 cm, w 2) to stop the ±4 cm hover scatter, and
  `grasp_ready` (w 5: gripper closing while the TCP is within 1.5 cm of the grasp point and aligned).
  Diagnostic value: grasp_ready high with lifting still 0 ⇒ the pads provably do not hold the plate.
  Lift relaunched (3rd time) from the align checkpoint.

## Ladder run started Sun 20 Sep 2026 06:07:01 PM PDT

- 18:07 container up, packages installed, calibration done (see scene.py constants)
- 18:07 reach: skipped (done by the earlier driver, success 0.967 (earlier driver))
- 18:07 align: skipped (done by the earlier driver, success nan (earlier driver))
- 18:07 train lift: 1000 iterations, 512 envs (warm start from align) 
- 20:20 (Claude) **Grasp physics understood, with pictures** (`results/gripper_*.png`):
  1. the inner-finger links DO collide with the plate (drop test: plate bounced off a pad);
  2. Martin's converted linkage lost its loop-closure joints, so the pads swung into a "V" and the
     tips met *above* the plate (`gripper_closes_above_plate_19-25.png`, `gripper_tips_inside_plate_19-40.png`);
  3. driving all finger joints with the URDF mimic ratios (`mdp/mimic_gripper.py`) makes the pads parallel
     and vertical (`gripper_parallel_pads_on_plate_top_20-05.png`) — but with parallel pads the pad bottoms
     sit at the TCP, so at the old grasp height they pinched the plate's *top edges* and squirted it up 7 cm;
  4. hence GRASP_POINT z = −8 mm (pads straddle the whole side, 5 mm above the table), closing speed halved,
     plate depenetration capped at 0.2 m/s, soft finger drives (4 N·m), robot depenetration capped.
  Only a policy trained on the new point can test the pinch, so lift is relaunched (4th time) from the
  align checkpoint with the full set. If `grasp_ready` rises and `lifting` follows, the ladder continues.

## Ladder run started Sun 20 Sep 2026 07:30:08 PM PDT

- 19:30 container up, packages installed, calibration done (see scene.py constants)
- 19:30 reach: skipped (done by the earlier driver, success 0.967 (earlier driver))
- 19:30 align: skipped (done by the earlier driver, success nan (earlier driver))
- 19:30 train lift: 1000 iterations, 512 envs (warm start from align) 
- 20:55 (Claude) lift (4th run): hover moved to the new lower point (fine_reaching 1.06) but grasp_ready ≈ 0
  (previous run 0.47 at the same point in training): with the halved, soft finger drive the joint needs
  sustained close commands to pass 0.15 rad and an exploring policy flickers the binary action. grasp_ready
  now also credits a *commanded* close at the right place. Lift relaunched (5th) from the align checkpoint.

## Ladder run started Sun 20 Sep 2026 07:52:31 PM PDT

- 19:52 container up, packages installed, calibration done (see scene.py constants)
- 19:52 reach: skipped (done by the earlier driver, success 0.967 (earlier driver))
- 19:52 align: skipped (done by the earlier driver, success nan (earlier driver))
- 19:52 train lift: 1000 iterations, 512 envs (warm start from align) 
- 20:07 (Claude) laptop suspended (lid?) at ~20:00; the lift run hung after resume (no iteration for 150 s, GPU 0 %). Killed and relaunched from the align checkpoint (6th lift run). GNOME auto-suspend is off; the lid switch needs HandleLidSwitch=ignore in logind.conf (sudo) or the lid kept open.

## Ladder run started Sun 20 Sep 2026 08:07:23 PM PDT

- 20:07 container up, packages installed, calibration done (see scene.py constants)
- 20:07 reach: skipped (done by the earlier driver, success 0.967 (earlier driver))
- 20:07 align: skipped (done by the earlier driver, success nan (earlier driver))
- 20:07 train lift: 1000 iterations, 512 envs (warm start from align) 
- 20:50 (Claude) lift (6th run) +200: grasp_ready 0.41, lifting 0. Recording with its checkpoint
  (`results/gripper_low_point_pads_in_table_20-45.png`): hover precise (8 mm) but the close command does
  nothing — finger at −0.05 rad, pushed outward by the table (5 mm pad clearance < hover scatter), the arm
  jams. Changes: grasp point −8 → −3 mm (10 mm clearance, 16/26 mm of the plate side covered), finger drive
  back to 8 N·m / stiffness 200 / full speed. Lift relaunched (7th).

## Ladder run started Sun 20 Sep 2026 08:53:04 PM PDT

- 20:53 container up, packages installed, calibration done (see scene.py constants)
- 20:53 reach: skipped (done by the earlier driver, success 0.967 (earlier driver))
- 20:53 align: skipped (done by the earlier driver, success nan (earlier driver))
- 20:53 train lift: 1000 iterations, 512 envs (warm start from align) 
- 21:45 (Claude) lift (7th run) +200: grasp_ready 0.35, lifting 0. Close-up with its checkpoint
  (`results/gripper_pads_across_long_side_21-40.png`): parallel pads straddle the plate — across its LONG
  side (8 mm clearance per side; the plate's physics frame is yawed 90° vs the USD prim frame) — with the
  pad bottoms on the table (the box collider bottoms are 7 mm below the TCP). Close stalled at 0.24 rad
  on the table; lift jammed. Fix: closing axis → body-local x (short side, 30 mm clearance per side),
  grasp point → +4 mm (pads 10 mm above the table). Lift relaunched (8th).

## Ladder run started Sun 20 Sep 2026 09:37:52 PM PDT

- 21:37 container up, packages installed, calibration done (see scene.py constants)
- 21:37 reach: skipped (done by the earlier driver, success 0.967 (earlier driver))
- 21:37 align: skipped (done by the earlier driver, success nan (earlier driver))
- 21:37 train lift: 1000 iterations, 512 envs (warm start from align) 

## Where things stand at 22:45 (for the morning)

- Reach 96.7 % and align 96 % are real (corrected frame). Lift: 0 % across eight runs; each run removed a
  verified defect (see the 09-20 entries above and `results/gripper_*.png`). The last configuration
  hovers precisely, closes at the plate most of the time (`grasp_ready` 0.68) and never lifts it in hand.
- The ladder keeps running unattended tonight: lift (1000 it.) → its retry → stack → place, so the
  pipeline is exercised end to end; stack/place cannot succeed without a grasp, and that's expected.
- **Decision for Dewei:** (a) a GUI session watching one grasp attempt with this gripper (10 min), or
  (b) swap the gripper for Isaac Lab's built-in Robotiq 2F-85 asset (known-good linkage and colliders;
  ~1 h of scene work) and re-run lift. My recommendation: (b), with (a) as the check on Martin's asset.
- 22:50 (Claude) final close-up of lift run 8 (`results/gripper_short_side_tips_on_top_22-50.png`): the
  pads now straddle the SHORT side (alignment fix worked) but, mid-close (0.53 rad), their tips press into
  the plate's TOP face at both ends and the pads tilt into a V again — the tips rise along the closing arc,
  and the 8 N·m drives can't hold the inner-finger joints parallel against contact. The grasp height keeps
  chasing an arc. This is the gripper asset, not the policy: recommendation stands — use Isaac Lab's
  built-in parallel-jaw Robotiq 2F-85 for the RL work, and give Martin this frame.
- 23:53 lift: success=0.000 (gate 0.4)
- 23:53 lift below gate → retry once with loosened tolerances: env.terminations.success.params.min_level=0.985 env.terminations.success.params.min_height=1.073
- 23:53 train lift: 1000 iterations, 512 envs (warm start from lift) env.terminations.success.params.min_level=0.985 env.terminations.success.params.min_height=1.073
- 02:12 lift (loosened): success=0.000
- 02:20 recorded lift → results/2026-09-21_lift
- 02:20 train stack: 1500 iterations, 512 envs (warm start from lift) 
- 05:43 stack: success=0.000 (gate 0.2)
- 05:43 stack below gate → retry once with loosened tolerances: env.terminations.success.params.xy_tol=0.02 env.terminations.success.params.z_tol=0.01 env.terminations.success.params.min_level=0.985
- 05:43 train stack: 1500 iterations, 512 envs (warm start from stack) env.terminations.success.params.xy_tol=0.02 env.terminations.success.params.z_tol=0.01 env.terminations.success.params.min_level=0.985
- 09:10 (Claude) ladder stopped during the stack retry (foregone 0 % without a grasp) to free the GPU for presentation videos before the 08:15 meeting.

## 2026-09-26 — PLAN v3, Part A: fixing the grasp (Round-2026-09-22)

Plain-language summary, kept live. Plan: `PLAN.md` v3.

- **Why lift failed (on paper, being checked now):** (1) the 2F-140 fingertips travel ~18 mm toward the
  table while closing from full open to the plate's 85 mm sides, so pads started 10 mm above the table hit
  it first (or closed over the plate top when higher); (2) our gripper code held the pad joints at 0, but in
  NVIDIA's gripper file those joints close the finger linkage and must turn with the fingers (+q) — the drives
  fought the linkage and the pads bent into a V.
- **Code (uncommitted until the probes are read):** gripper variants selected with `WELLPLATE_GRIPPER`:
  G0 = 09-20 setup (control), G1 = pad joints +q, pre-open 0.2 rad (~112 mm), new grasp height,
  G2 = G1 + Isaac Lab's reference 2F-140 drives with NVIDIA's gripper as shipped. Stack "released" and lift/stack
  "closing" thresholds now follow the pre-open.
- Note found while preparing the probe: the 96 % align number was measured with the old (wrong) TCP frame; the
  corrected-frame align run (`2026-09-20_21-49-34_align`) ended at 4 % under the old success-as-terminal flaw.
  Tonight's align re-run gives the real number. That checkpoint still hovers aligned at the grasp point, so it
  positions the arm in the grasp probe.

### 2026-09-26 afternoon — Part A results: the grasp works (gate passed 16/16)

Evidence: `results/2026-09-26_gripper_fix/` (README there). In plain language, what was wrong and what fixed it:

1. **The pads bent into a V** (our code drove the pad joint to 0; it must follow +q). Measured in the air: 12° V at the
   plate's width with the 09-20 setup, 0.0° with the fix (F2, V1). The pads also travel 18.4 mm toward the table while
   closing from full open (predicted 18.3 mm) — the fix pre-opens to 112 mm and grasps 3 mm above the table (F1).
2. **The gripper was closing across the wrong side of the plate** since 09-20 21:45 (the 128 mm side). Measured from the
   plate geometry: body x = 127.6 mm, y = 85.4 mm. `CLOSING_AXIS_INDEX` back to 1 (the 85 mm side).
3. **The pads sank through the plate when both squeezed it** (a single pad pushing it worked). Cause: contact settings.
   Isaac Lab's own UR + 2F-140 settings fix it (robot max depenetration 5, contact impulse unlimited, 5 mm contact
   offset; plate 32 solver iterations).
4. **Driving all eight finger joints hard spins the plate out**; Isaac Lab's gripper drives (main finger joint only,
   mimic kept, NVIDIA's colliders as shipped = variant G2) hold it. **G2: 16/16 plates held, lifted 10 cm, tilt 0.6°.**
   Now the default (`scene.py`). The 09-20 "no colliders" diagnosis was wrong; our extra pad boxes were also misplaced
   (finger link frames are rotated) — both unused in G2.

Findings that matter for training (for Dewei):
- **The arm cannot hold small position corrections under relative IK.** With robot gravity ON (our training setting)
  a scripted controller stalled ~0.3 m short and the gripper tilted; with gravity OFF it still plateaued 1–5 cm off.
  Joint gains are soft and overdamped (400/80 on every joint) vs Isaac Lab's UR (1320/73 shoulder, 600/35 elbow,
  216/29 wrist) and Isaac Lab disables robot gravity (a real UR compensates gravity itself). This is likely why reach/
  align needed 4 cm tolerances on 09-20. The probe used its own joint-space controller (accumulating the pose error
  into joint targets), which reaches the grasp pose with 0 mm error.
- Isaac Lab's IK action corrects the Jacobian for the TCP offset with the offset in the gripper frame instead of the
  root frame (task_space_actions.py `_compute_frame_jacobian`); with the gripper pointing down the correction has the
  wrong sign. In our test it slowed convergence (1–7 cm vs 1–6 mm after 100 steps) but was not the cause of the plateau.
- The "align 96 %" number (09-20) was measured with the old TCP frame; tonight's align re-run gives the real number.

### 2026-09-26 evening — arm check, smoke test, launch

- Dewei: robot gravity **off** for now, current arm gains kept; realistic arm (gravity on + compensation) later.
- Arm check through the task's own action (`scripts/probe_arm_tracking.py`, 16 envs, target 8 cm above the grasp point):
  gravity off → 0.0–0.2 mm median error after 300 steps with any of three scripted controllers; gravity on (the 09-20
  setting) → ~410 mm and 35–50° off, none converge. Logs: `results/2026-09-26_gripper_fix/arm_tracking_gravity_*.log`.
- A4 smoke test (align, lift, stack; 64 envs × 5 it., G2, video): no errors, videos written (`results/logs/smoke_*_0926.log`).
- Overnight ladder v3 launched: align 300 → lift 1000 → stack 1500, gripper G2, robot gravity off, 512 envs.

## Ladder v3 started Sat 26 Sep 2026 12:42:25 PM PDT — gripper G2, 512 envs

- 12:42 train align: 300 iterations, 512 envs, gripper G2 (warm start from 2026-09-20_21-49-34_align) 
- 12:53 align: training success 0.846 (gate 0.8)
- 12:54 eval align (train_criteria): [eval] Wellplate-Align-v0 train_criteria: success 0.820 over 128 episodes; ends {'time_out': 0.1797, 'plate_dropped': 0.0, 'arm_unstable': 0.0, 'success': 0.8203}
- 12:54 eval align (strict): [eval] Wellplate-Align-v0 strict: success 0.000 over 128 episodes; ends {'time_out': 1.0, 'plate_dropped': 0.0, 'arm_unstable': 0.0, 'success': 0.0}
- 12:56 recorded align → results/2026-09-26_align
- 12:56 train lift: 1000 iterations, 512 envs, gripper G2 (warm start from 2026-09-26_19-42-36_align) 
- 13:13 (Claude) lift at ~480/1000 it.: grasp_ready 0.05–0.44, lifting occasionally > 0 (0.03–0.12), success 0, plate knocked off 4–10 %. Unlike 09-20 (lifting exactly 0) the grasp is physically possible now; letting the stage and its retry run. Training clips are over-exposed (their own camera settings) — evaluation videos are fine.
- 13:29 lift: training success 0.000 (gate 0.4)
- 13:29 lift below gate → retry once, warm start from this run, loosened: env.terminations.success.params.min_level=0.985 env.terminations.success.params.min_height=1.073
- 13:29 train lift: 1000 iterations, 512 envs, gripper G2 (warm start from 2026-09-26_19-56-25_lift) env.terminations.success.params.min_level=0.985 env.terminations.success.params.min_height=1.073
- 14:02 lift (retry): training success 0.199
- 14:03 eval lift (train_criteria): [eval] Wellplate-Lift-v0 train_criteria: success 0.875 over 128 episodes; ends {'time_out': 0.1016, 'plate_dropped': 0.0234, 'arm_unstable': 0.0, 'success': 0.875}
- 14:03 eval lift (strict): [eval] Wellplate-Lift-v0 strict: success 0.148 over 128 episodes; ends {'time_out': 0.8125, 'plate_dropped': 0.0391, 'arm_unstable': 0.0, 'success': 0.1484}
- 14:05 recorded lift → results/2026-09-26_lift
- 14:05 LADDER STOPPED at lift: success 0.199 below gate 0.4 after the retry — waiting for diagnosis (PLAN v3 §1)
- 14:10 (Claude) **Diagnosis of the stop — the gate, not the task.** Lift's deterministic eval: **87.5 %** (lifted 6 cm,
  level within 10°, 128 episodes; 2.3 % plates knocked off); strict (10 cm, 5°): 14.8 % — the retry was trained to 6 cm.
  Videos show real lifts, plate level between the pads. The 19.9 % that stopped the ladder is the *training* success,
  which includes exploration noise; with a binary gripper that noise flips the grip open mid-lift. Fix (driver only, no
  task change): the gate now reads the deterministic eval. Lift passes (0.875 ≥ 0.4). Relaunched from stack, warm start
  from the lift retry checkpoint `2026-09-26_20-29-26_lift`. Rewards unchanged (a dense lift term is drafted, not applied).

## Ladder v3 started Sat 26 Sep 2026 02:06:15 PM PDT — gripper G2, 512 envs, START_STAGE=stack

- 14:06 align: skipped (START_STAGE=stack)
- 14:06 lift: skipped (START_STAGE=stack)
- 14:06 train stack: 1500 iterations, 512 envs, gripper G2 (warm start from 2026-09-26_20-29-26_lift) 
- 15:05 (Claude) **Stack collapsed mid-run; stopped at ~800/1500 it.** It started well (carried the plate toward the
  target: goal_coarse 5.9, goal_fine 0.62 at ~400 it.), then every term fell and episodes shrank 400 → 120 steps.
  Cause: the policy's action noise grew stage after stage under entropy_coef 0.01 — std ≈ 1.0 after align, up to 1.9
  after lift, 2.8 after the lift retry, 3.7 in stack (gripper dim highest). Actions are clipped to ±1, so a wide std
  costs nothing, and the binary gripper then flips open at random. (This is also why lift's *training* success read
  19.9 % while the deterministic policy lifts 87.5 %.) Fix: entropy_coef 0.01 → 0.001 (agents/rsl_rl_ppo_cfg.py) and a
  warm start with the std reset to 0.5 — `scripts/reset_action_std.py` wrote `logs/.../2026-09-26_21-59-59_lift` (a copy
  of the lift retry's model_3295.pt; the policy's mean actions are unchanged, README inside). Stack relaunched from it.

## Ladder v3 started Sat 26 Sep 2026 02:39:06 PM PDT — gripper G2, 512 envs, START_STAGE=stack

- 14:39 align: skipped (START_STAGE=stack)
- 14:39 lift: skipped (START_STAGE=stack)
- 14:39 train stack: 1500 iterations, 512 envs, gripper G2 (warm start from 2026-09-26_21-59-59_lift) 
- 15:05 (Claude) **Stack stalled after the noise fix (std stable at 0.5): lifting 2.7 → 1.1, goal_coarse 1.4 → 0.6,
  goal_fine 0, success 0 at ~570/1500 it.** Cause: a reward bug. The goal terms were gated on "lifted" (rest + 4 cm =
  1.053 m) but a plate stacked on the target has its root at 1.041 m, so the goal reward switched off exactly at the goal,
  and releasing also lost grasp_ready + lifting: hovering beat placing. Fix (shaping only — the success criterion is
  unchanged): goal terms count whenever the plate is off the table (rest + 1 cm); new `placed` reward (+10/step while the
  plate rests on the goal within 2 cm / 1 cm / ~10°, gripper open); grasp_ready 5 → 1 (was being farmed). Released at the
  goal now pays ≈ 33/step vs ≈ 27 for hovering. Build check passed; stack relaunched from the std-reset lift checkpoint.

## Ladder v3 started Sat 26 Sep 2026 03:02:43 PM PDT — gripper G2, 512 envs, START_STAGE=stack

- 15:02 align: skipped (START_STAGE=stack)
- 15:02 lift: skipped (START_STAGE=stack)
- 15:02 train stack: 1500 iterations, 512 envs, gripper G2 (warm start from 2026-09-26_21-59-59_lift) 
- 15:54 eval stack (train_criteria): [eval] Wellplate-Stack-v0 train_criteria: success 0.016 over 128 episodes; ends {'time_out': 0.8828, 'plate_dropped': 0.1016, 'arm_unstable': 0.0, 'success': 0.0156}
- 15:54 stack: training success 0.004, deterministic eval 0.016 (gate 0.3 on the eval)
- 15:54 stack below gate → retry once, warm start from this run, loosened: env.terminations.success.params.xy_tol=0.03 env.terminations.success.params.z_tol=0.015 env.terminations.success.params.min_level=0.98
- 15:54 train stack: 1500 iterations, 512 envs, gripper G2 (warm start from 2026-09-26_22-02-53_stack) env.terminations.success.params.xy_tol=0.03 env.terminations.success.params.z_tol=0.015 env.terminations.success.params.min_level=0.98
- 16:44 eval stack (train_criteria): [eval] Wellplate-Stack-v0 train_criteria: success 0.008 over 128 episodes; ends {'time_out': 0.8672, 'plate_dropped': 0.125, 'arm_unstable': 0.0, 'success': 0.0078}
- 16:44 stack (retry): training success 0.004, deterministic eval 0.008
- 16:45 eval stack (strict): [eval] Wellplate-Stack-v0 strict: success 0.000 over 128 episodes; ends {'time_out': 0.875, 'plate_dropped': 0.125, 'arm_unstable': 0.0, 'success': 0.0}
- 16:47 recorded stack → results/2026-09-26_stack
- 16:47 LADDER STOPPED at stack: eval success 0.008 below gate 0.3 after the retry — waiting for diagnosis (PLAN v3 §1)
- 16:55 (Claude) **Stack stopped: carried to the target, never placed.** Retry eval 0.8 % (12.5 % dropped); video: the
  plate is picked, carried to the target plate and held just above/beside it. Reward trace: `placed` exactly 0 all run.
  Cause: `lifting` was still gated at rest + 4 cm while the stacked plate sits at rest + 2.6 cm, so lowering onto the
  target cost 5/step — hover ≈ 27 > lowered ≈ 24 < released ≈ 33, a dip PPO did not cross. Fix: `lifting` gated at
  rest + 1 cm in stack (hover ≈ 27 → lowered ≈ 29 → released ≈ 38). Relaunched stack warm-started from its own last run
  (`STACK_FROM=stack`), which already carries to the goal. (Note: the dark plate near the table edge is the stack target;
  the yellow plate at the back is the out-of-reach third plate — the 09-20 note "yellow = target" was wrong.)

## Ladder v3 started Sat 26 Sep 2026 04:48:01 PM PDT — gripper G2, 512 envs, START_STAGE=stack

- 16:48 align: skipped (START_STAGE=stack)
- 16:48 lift: skipped (START_STAGE=stack)
- 16:48 train stack: 1500 iterations, 512 envs, gripper G2 (warm start from 2026-09-26_22-54-56_stack) 
- 17:38 eval stack (train_criteria): [eval] Wellplate-Stack-v0 train_criteria: success 0.281 over 128 episodes; ends {'time_out': 0.6328, 'plate_dropped': 0.0859, 'arm_unstable': 0.0, 'success': 0.2812}
- 17:38 stack: training success 0.151, deterministic eval 0.281 (gate 0.3 on the eval)
- 17:38 stack below gate → retry once, warm start from this run, loosened: env.terminations.success.params.xy_tol=0.03 env.terminations.success.params.z_tol=0.015 env.terminations.success.params.min_level=0.98
- 17:38 train stack: 1500 iterations, 512 envs, gripper G2 (warm start from 2026-09-26_23-48-12_stack) env.terminations.success.params.xy_tol=0.03 env.terminations.success.params.z_tol=0.015 env.terminations.success.params.min_level=0.98
- 18:30 eval stack (train_criteria): [eval] Wellplate-Stack-v0 train_criteria: success 0.289 over 128 episodes; ends {'time_out': 0.625, 'plate_dropped': 0.0859, 'arm_unstable': 0.0, 'success': 0.2891}
- 18:30 stack (retry): training success 0.137, deterministic eval 0.289
- 18:32 eval stack (strict): [eval] Wellplate-Stack-v0 strict: success 0.039 over 128 episodes; ends {'time_out': 0.8125, 'plate_dropped': 0.1484, 'arm_unstable': 0.0, 'success': 0.0391}
- 18:33 recorded stack → results/2026-09-26_stack
- 18:33 LADDER STOPPED at stack: eval success 0.289 below gate 0.3 after the retry — waiting for diagnosis (PLAN v3 §1)
- 18:50 (Claude) **Stack stopped at 28.9 % (3 cm / 1.5 cm / 11°, deterministic; strict 1 cm / 5 mm / 5°: 3.9 %) — the plate
  is placed but not released.** Close-up video: the white plate rests on the dark target plate. Timeout diagnostic
  (`eval_policy.py --diag_stack`, 80 timed-out episodes): 59 % have the plate ON the goal (median 9 mm xy, 0.7 mm z, 0.9°
  tilt) with the gripper still closed; the rest mostly never picked it up. The policy's gripper command there is −3.0
  (range −8.1…−1.2; close < 0) while the gripper std is 0.5, so an exploratory release essentially never happens and the
  +10/step `placed` reward is never found. Fix (exploration only, no reward/task change): warm start from the last stack
  checkpoint with the GRIPPER action std widened to 2.0 (arm dims 0.5–0.6) — `2026-09-27_01-59-59_stack` (README inside).
  Relaunched stack (STACK_FROM=stack).

## Ladder v3 started Sat 26 Sep 2026 06:37:23 PM PDT — gripper G2, 512 envs, START_STAGE=stack

- 18:37 align: skipped (START_STAGE=stack)
- 18:37 lift: skipped (START_STAGE=stack)
- 18:37 train stack: 1500 iterations, 512 envs, gripper G2 (warm start from 2026-09-27_01-59-59_stack) 
- 19:29 eval stack (train_criteria): [eval] Wellplate-Stack-v0 train_criteria: success 0.234 over 128 episodes; ends {'time_out': 0.625, 'plate_dropped': 0.1406, 'arm_unstable': 0.0, 'success': 0.2344}
- 19:29 stack: training success 0.132, deterministic eval 0.234 (gate 0.3 on the eval)
- 19:29 stack below gate → retry once, warm start from this run, loosened: env.terminations.success.params.xy_tol=0.03 env.terminations.success.params.z_tol=0.015 env.terminations.success.params.min_level=0.98
- 19:29 train stack: 1500 iterations, 512 envs, gripper G2 (warm start from 2026-09-27_01-59-59_stack) env.terminations.success.params.xy_tol=0.03 env.terminations.success.params.z_tol=0.015 env.terminations.success.params.min_level=0.98
- 20:22 eval stack (train_criteria): [eval] Wellplate-Stack-v0 train_criteria: success 0.508 over 128 episodes; ends {'time_out': 0.3672, 'plate_dropped': 0.125, 'arm_unstable': 0.0, 'success': 0.5078}
- 20:22 stack (retry): training success 0.273, deterministic eval 0.508
- 20:23 eval stack (strict): [eval] Wellplate-Stack-v0 strict: success 0.227 over 128 episodes; ends {'time_out': 0.6016, 'plate_dropped': 0.1719, 'arm_unstable': 0.0, 'success': 0.2266}
- 20:24 recorded stack → results/2026-09-26_stack

## Ladder v3 summary Sat 26 Sep 2026 08:24:59 PM PDT

| stage | success |
|---|---|
| align | not run (earlier run) |
| lift | not run (earlier run) |
| stack | eval 0.508 (training 0.273) |
- 20:24 ladder v3 finished
- 20:24 stack (gripper-exploration run + retry): deterministic eval **50.8 %** (3 cm / 1.5 cm / 11°), strict 22.7 %,
  12.5 % dropped — gate passed, ladder finished. Checked by video: labelled recording of 8 consecutive episodes in a
  close-up on the target (`record_labelled.py`): 4 success, 3 timeout, 1 dropped; successes show the plate lowered onto
  the target plate and released. (Two recording mistakes of mine caught on the way: an ad-hoc command sorted checkpoint
  paths on the wrong field and evaluated `model_9900` instead of the final `model_10790` (10.9 % vs 50.8 %); the first
  recorder froze each clip on the post-reset frame. Both fixed; the ladder's own checkpoint selection was always right.)

## Morning read — 2026-09-26 (Round-2026-09-22)

**The robot picks up a well plate and stacks it on a second plate.** Deterministic evaluation, 128 episodes each:

| Stage | Training tolerance | Strict tolerance |
|---|---|---|
| Align | 82.0 % (4 cm, 20°) | 0.0 % (2 cm, 15°/10°) |
| Lift | 87.5 % (6 cm up, tilt < 10°) | 14.8 % (10 cm up, tilt < 5°) |
| Stack, 2 plates | 50.8 % (3 cm / 1.5 cm / 11°) | 22.7 % (1 cm / 5 mm / 5°) |

On 09-20/21 lift and stack were 0 %. Videos and charts: `results/2026-09-26_summary/` (README there).

What it took, in order (each confirmed by a measurement before the fix):
1. Gripper: pad joint +q, pre-open 112 mm, grasp height from the measured pad travel, closing axis back to the 85 mm
   side, Isaac Lab's 2F-140 drives + contact settings (grasp probe 16/16).
2. Robot gravity off (Dewei): the arm now reaches IK targets to 0.2 mm (410 mm off with gravity on).
3. Driver gated on the noisy training success → gate on the deterministic eval (lift 0.199 noisy vs 0.875 deterministic).
4. Action noise grew stage after stage (std 1 → 3.7) and collapsed stack → entropy 0.01 → 0.001, std reset to 0.5.
5. Stack reward: goal terms and `lifting` switched off at the goal height, so placing lost reward → gated at 1 cm off the
   table, `placed` reward added, grasp_ready 5 → 1.
6. The policy placed but never let go (gripper command −3, noise 0.5) → gripper exploration std 2.0 → releases learned.

Open / next (for Dewei):
- Strict precision: lift to 10 cm and stack to 1 cm are the weak numbers (14.8 %, 22.7 %). Candidates: continue training
  at the strict tolerances, or a precision curriculum.
- 12.5 % of stack episodes drop the plate; 37 % time out (the diagnostic splits these into "never picked up" and
  "placed but held").
- Realistic arm (gravity on + compensation), loose bottom plate, 3 plates, other libraries — PLAN v3 §6.

## 2026-09-26 night — PLAN v4: centred 2-plate stack (C0 done, curriculum launched)

- **C0 measurements:** both plates are the same mesh (127.6 × 85.4 × 26 mm), centred on their frames. The target plate's
  mesh is rotated **+48.97°** inside its frame (`scripts/probe_plate_axes.py`), so its long axis is body x rotated 48.97°
  — the twist measure uses that (`TARGET_LONG_AXIS_LOCAL`, scene.py). Using body x would have "aligned" plates 49° apart.
- **C0 code:** twist (yaw) between the plates' long axes modulo 180°; `Wellplate-Centered-v0` with centred success
  (centring, twist, tilt, released, settled) and rewards xy_fine / yaw_align / yaw_fine / placed; `run_centered.sh`
  (C1 1.5 cm / 10° / 5°, C2 1 cm / 5° / 3°, C3 5 mm / 3° / 3°, gate 0.4 on the deterministic eval).
- **Independent code review before launch (6 agents, findings verified by a skeptic):** one high-severity bug — the
  success bonus never paid in ANY stage: Isaac Lab's `is_terminated_term` masks truncations and every success here is a
  truncation (logs: success_bonus 0.0000 beside success 0.27). New `success_reward` reads the term directly; all stages
  switched. Also: success now needs the plate settled; the fine-twist kernel widens with the stage tolerance; diagnostic
  "held" = fingers closed AND plate at the TCP; success wins over a same-step time-out in labels; driver stops on a failed
  eval instead of counting it as a gate miss.
- **Baseline:** the 09-26 stack policy at C1's centred criteria: **0 %** — centring is already good (median 4.9 mm,
  tilt 1.2°) but it places with a median **twist of 72°**; 85 % of its time-outs hold the plate on the goal. C1 must teach
  turning the plate ~70° during the carry. Warm start keeps its gripper exploration std (2.02).

## Centred ladder started Sat 26 Sep 2026 10:28:58 PM PDT — START_STAGE=C1, 512 envs, 1500 it./stage

- 22:28 train centered: 1500 it., 512 envs, warm start 2026-09-27_02-29-31_stack/model_10790.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=10.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=10.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=10.0
- 23:05 (Claude) **C1 stopped at ~500/1500 it.: the plate is not being turned.** yaw_align flat at ≈ 0.75 (mean twist
  ≈ 60° while carried), yaw_fine 0, success 0; centring improved (xy_fine 0.86 → 1.6), drops 7–9 %. Turning the plate
  needs a sustained wrist-yaw command over ~20 steps of the carry; with yaw_align at 3/step next to ≈ 40/step of other
  terms and yaw-action noise 0.66 the policy did not find it. Fix (weights and exploration only): yaw_align 3 → 8; warm
  start from C1's model_11300 with the yaw-rotation action noise (dim 5, rotation about world z) raised to 1.0 —
  `2026-09-27_07-59-59_centered` (README inside). C1 relaunched from it (C1_FROM_CENTERED=1).

## Centred ladder started Sat 26 Sep 2026 10:50:32 PM PDT — START_STAGE=C1, 512 envs, 1500 it./stage

- 22:50 train centered: 1500 it., 512 envs, warm start 2026-09-27_07-59-59_centered/model_11300.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=10.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=10.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=10.0
- 23:55 (Claude) **C1 relaunch (yaw_align 8, yaw noise 1.0) also flat: mean twist while carried still ≈ 60°.** Probe
  (`scripts/rsl_rl/probe_yaw_rotation.py`: policy lifts the plate, then a full yaw command for 40 steps): the wrist turned
  only 16° (0.4°/step, commanded 2.9°/step) and 2/5 plates dropped. Cause: the arm joints are overdamped (400/80, 0.2 s
  time constant) and the relative IK re-targets from the current pose each step, so only ~15 % of each command is
  realised — translation copes (large commands), a 60° turn would take ~150 steps. Arm gains stay as Dewei decided; fix
  inside the task: yaw command scale 0.05 → 0.1 (centered_env_cfg.py). 0.2 turned 1.7°/step but disrupted the policy
  (actions clipped before scaling); 0.1 turns 0.9°/step, 5/5 plates held while turning, twist 45° → 9° in 40 steps, and
  the warm-started policy behaves as before (its yaw output halved, `reset_action_std.py --mean_dim 5 --mean_factor 0.5`;
  yaw noise 0.7) — `2026-09-27_05-50-44_centered`. C1 relaunched from it.
- **Correction (driver bug, found 23:30):** derived warm-start folders were named so they sorted AFTER the next training
  run, and the drivers take the latest run by name. Effect on the 09-26 stack stage: its first-pass eval (23.4 %) scored
  the derived pre-training checkpoint, and its retry warm-started from that checkpoint instead of the first pass. The
  reported 50.8 % is the retry run's own checkpoint and stands; the first pass's 1500 iterations were discarded. Fixed:
  derived folders are renamed/named source-time + 1 s (they sort before any later run); rule written into
  reset_action_std.py's README text.

## Centred ladder started Sat 26 Sep 2026 11:16:59 PM PDT — START_STAGE=C1, 512 envs, 1500 it./stage

- 23:16 train centered: 1500 it., 512 envs, warm start 2026-09-27_05-50-44_centered/model_11900.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=10.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=10.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=10.0
- 00:25 (Claude) **C1 with the yaw scale fix: centring excellent, still no turning, no release.** Deterministic diagnostic
  (`eval_..._C1_midrun_diag.json`, 128 episodes): 80 % time out with the plate ON the goal — centring 4.7 mm, height
  0.2 mm, tilt 0.4° (medians) — but twist 47° (= what random twists average) and still held (gripper command −21.7);
  20 % dropped. Two gaps: (1) the policy cannot easily tell which way to turn — it only sees the two quaternions, and
  the twist is a nonlinear function of them plus the target mesh's 49° offset and the 180° symmetry; random wrist noise
  over a carry nets only ~±4°, too weak a signal to learn that mapping; (2) release unreachable again (command −21.7,
  noise 2.0). Fixes: (1) new observation `plate_twist` = (sin 2Δ, cos 2Δ) of the signed twist (centred task only,
  appended last); the warm-start checkpoint is widened 205 → 215 inputs with zero weights for the new inputs (policy
  unchanged at the start), normalizers and Adam moments extended (`scripts/widen_obs_checkpoint.py`); (2) gripper mean
  output ×0.15 (binary: decisions unchanged, exploratory releases possible, −21.7 → −3.3 vs noise 2.0). Warm start
  `2026-09-27_06-17-10_centered` (from C1's model_12600). Build check passed. C1 relaunched.

## Centred ladder started Sat 26 Sep 2026 11:47:12 PM PDT — START_STAGE=C1, 512 envs, 1500 it./stage

- 23:47 train centered: 1500 it., 512 envs, warm start 2026-09-27_06-17-10_centered/model_12600.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=10.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=10.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=10.0
- 00:50 (Claude) **C1 with the twist observation: still no turning after ~600 it. — cause: the learning rate.** The
  adaptive schedule (desired_kl 0.01) sat at its 1e-5 floor in every recent run (align, lift, stack, C1; C1 median
  2.3e-5, TensorBoard Loss/learning_rate): the per-update KL exceeded 2 × 0.01 even at 1e-5 (likely the running
  observation normalizer shifting between rollout and update, with raw gripper outputs of ±20 fed back as observations),
  so the policy could polish existing behaviour but not learn a new one. Fix: fixed learning rate 1e-4 for the centred
  runner (PPO ratio clipping still bounds each step); warm start from C1's model_13300 with the optimizer lr reset
  5e-5 → 1e-4 (`scripts/set_checkpoint_lr.py`, `2026-09-27_06-47-24_centered`). Watching value loss and success for
  instability. C1 relaunched.

## Centred ladder started Sun 27 Sep 2026 12:14:29 AM PDT — START_STAGE=C1, 512 envs, 1500 it./stage

- 00:14 train centered: 1500 it., 512 envs, warm start 2026-09-27_06-47-24_centered/model_13300.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=10.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=10.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=10.0
- 01:00 (Claude) **Fixed LR 1e-4: stable (value loss 25–40), twist at time-out 47° → 40°, still no success.** Two
  checks: (a) diagnostic — the twist at time-out is narrow (p25–p75 38–44°) and all need the same correction; (b) probe
  (`probe_yaw_rotation.py --at_goal`, ± `--lift_first 0.02`): a +35° wrist turn takes the twist 42° → 5.7° whether the
  plate rests on the target or is lifted — friction on the target is NOT the problem (hypothesis refuted). So turning is
  physically easy, but success/placed only pay below 10° twist and nothing the policy tries gets there; the small
  yaw_align gradient alone does not teach it. Fix (tolerances between stages, per PLAN v4 §D3): twist curriculum inside
  C1 — C1a 45°, C1b 30°, C1c 20° (700 it. each), then C1 10° (1000 it.), C2, C3; centring 1.5 cm, tilt 5° until C1. At 45°
  the current placements already succeed, so the (now working) success bonus and `placed` reward release and then each
  further 10° of turning. Warm start: the fixed-LR C1 run `2026-09-27_07-14-40_centered/model_13800`.

## Centred ladder started Sun 27 Sep 2026 12:35:37 AM PDT — START_STAGE=C1a, 512 envs, 1500 it./stage

- 00:35 train centered: 700 it., 512 envs, warm start 2026-09-27_07-14-40_centered/model_13800.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=45.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=45.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=45.0
- 01:02 eval C1a_stage (2026-09-27_07-35-48_centered/model_14499.pt): [eval] Wellplate-Centered-v0 C1a_stage: success 0.016 over 128 episodes; ends {'time_out': 0.8359, 'plate_dropped': 0.1484, 'arm_unstable': 0.0, 'success': 0.0156}
- 01:02 C1a (0.015 m / 45° / 5°): training success 0.072, deterministic eval 0.016 (gate 0.4)
- 01:02 C1a below gate → retry once (continue 700 it., same tolerances)
- 01:02 train centered: 700 it., 512 envs, warm start 2026-09-27_07-35-48_centered/model_14499.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=45.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=45.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=45.0

### 01:10 — C1a failed its gate: the policy places but does not let go (fix: success bonus 50 → 600)
- C1a (45° twist tolerance) finished 700 iterations: training success peaked ~14 %, deterministic eval **1.6 %** (128 episodes). I stopped the automatic retry to diagnose instead.
- Diagnosis (`results/2026-09-27_centered/eval_C1a_diag.log`, per episode): 84 % time out, 15 % drop. In the time-outs the plate is **on the goal** — centring median 4 mm, tilt 2.7°, twist 22° (inside 45°) — but **67 % of all episodes end with the plate still held**. Gripper action median −18 (firmly closed). So turning improved (twist 40° → 22°) and the blocker is now *releasing*.
- Why: success is a truncation with value bootstrapping, so the one-off success bonus is the only net gain from opening. At weight 50 it pays 50 × 1/30 s ≈ 1.7 once, while the critic's error is about ±5–7 (value loss 25–48). The release signal is buried in noise. The added centring/twist rewards made the held state more valuable than in the 09-26 stack task, where the same bonus was enough.
- Fix (one change, so it can be attributed): centred task's `success_bonus` weight 50 → 600 (≈ 20 per success). Restart C1a from its end checkpoint (`2026-09-27_07-35-48_centered/model_14499`).
- This is a new failure (release), not a fourth turning fix; the twist curriculum measurably helped (40° → 22°, successes appeared).

## Centred ladder started Sun 27 Sep 2026 01:06:31 AM PDT — START_STAGE=C1a, 512 envs, 1500 it./stage

- 01:06 train centered: 700 it., 512 envs, warm start 2026-09-27_07-35-48_centered/model_14499.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=45.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=45.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=45.0
- 01:33 eval C1a_stage (2026-09-27_08-06-42_centered/model_15198.pt): [eval] Wellplate-Centered-v0 C1a_stage: success 0.672 over 128 episodes; ends {'time_out': 0.25, 'plate_dropped': 0.0781, 'arm_unstable': 0.0, 'success': 0.6719}
- 01:33 C1a (0.015 m / 45° / 5°): training success 0.407, deterministic eval 0.672 (gate 0.4)
- 01:33 train centered: 700 it., 512 envs, warm start 2026-09-27_08-06-42_centered/model_15198.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=30.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=30.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=30.0
- 02:00 eval C1b_stage (2026-09-27_08-33-50_centered/model_15897.pt): [eval] Wellplate-Centered-v0 C1b_stage: success 0.672 over 128 episodes; ends {'time_out': 0.2422, 'plate_dropped': 0.0859, 'arm_unstable': 0.0, 'success': 0.6719}
- 02:00 C1b (0.015 m / 30° / 5°): training success 0.670, deterministic eval 0.672 (gate 0.4)
- 02:00 train centered: 700 it., 512 envs, warm start 2026-09-27_08-33-50_centered/model_15897.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=20.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=20.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=20.0
- 02:28 eval C1c_stage (2026-09-27_09-01-03_centered/model_16596.pt): [eval] Wellplate-Centered-v0 C1c_stage: success 0.734 over 128 episodes; ends {'time_out': 0.1719, 'plate_dropped': 0.0938, 'arm_unstable': 0.0, 'success': 0.7344}
- 02:28 C1c (0.015 m / 20° / 5°): training success 0.777, deterministic eval 0.734 (gate 0.4)
- 02:28 train centered: 1000 it., 512 envs, warm start 2026-09-27_02-29-31_stack/model_10790.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=10.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=10.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=10.0

### 02:35 — C1a/C1b/C1c passed; C1 restarted from the right checkpoint
- After the success-bonus fix the twist curriculum ran through: **C1a (45°) 67.2 %, C1b (30°) 67.2 %, C1c (20°) 73.4 %** deterministic (gate 40 %).
- Driver bug: C1 always warm-started from the 09-26 stack policy (meant only for a fresh C1 launch), so at 02:28 it threw away C1a–C1c. Stopped within a minute (no checkpoint written); the driver now uses the 09-26 policy for C1 only when C1 is the launch's first stage. Relaunched `START_STAGE=C1 C1_FROM_CENTERED=1` → C1 continues from C1c (`2026-09-27_09-01-03_centered/model_16596`).

## Centred ladder started Sun 27 Sep 2026 02:28:59 AM PDT — START_STAGE=C1, 512 envs, 1500 it./stage

- 02:28 C1a: skipped (START_STAGE=C1)
- 02:28 C1b: skipped (START_STAGE=C1)
- 02:28 C1c: skipped (START_STAGE=C1)
- 02:28 train centered: 1000 it., 512 envs, warm start 2026-09-27_09-01-03_centered/model_16596.pt, env.terminations.success.params.xy_tol=0.0150 env.terminations.success.params.yaw_tol_deg=10.0 env.terminations.success.params.min_level=0.996195 env.rewards.placed.params.xy_tol=0.0150 env.rewards.placed.params.yaw_tol_deg=10.0 env.rewards.placed.params.min_level=0.996195 env.rewards.yaw_fine.params.std_deg=10.0
- 03:05 eval C1_stage (2026-09-27_09-29-10_centered/model_17595.pt): [eval] Wellplate-Centered-v0 C1_stage: success 0.852 over 128 episodes; ends {'time_out': 0.1016, 'plate_dropped': 0.0469, 'arm_unstable': 0.0, 'success': 0.8516}
- 03:05 C1 (0.015 m / 10° / 5°): training success 0.488, deterministic eval 0.852 (gate 0.4)
- 03:05 train centered: 1500 it., 512 envs, warm start 2026-09-27_09-29-10_centered/model_17595.pt, env.terminations.success.params.xy_tol=0.0100 env.terminations.success.params.yaw_tol_deg=5.0 env.terminations.success.params.min_level=0.998630 env.rewards.placed.params.xy_tol=0.0100 env.rewards.placed.params.yaw_tol_deg=5.0 env.rewards.placed.params.min_level=0.998630 env.rewards.yaw_fine.params.std_deg=5.0
- 03:59 eval C2_stage (2026-09-27_10-06-03_centered/model_19094.pt): [eval] Wellplate-Centered-v0 C2_stage: success 0.875 over 128 episodes; ends {'time_out': 0.0625, 'plate_dropped': 0.0625, 'arm_unstable': 0.0, 'success': 0.875}
- 03:59 C2 (0.010 m / 5° / 3°): training success 0.303, deterministic eval 0.875 (gate 0.4)
- 03:59 train centered: 1500 it., 512 envs, warm start 2026-09-27_10-06-03_centered/model_19094.pt, env.terminations.success.params.xy_tol=0.0050 env.terminations.success.params.yaw_tol_deg=3.0 env.terminations.success.params.min_level=0.998630 env.rewards.placed.params.xy_tol=0.0050 env.rewards.placed.params.yaw_tol_deg=3.0 env.rewards.placed.params.min_level=0.998630 env.rewards.yaw_fine.params.std_deg=3.0
- 04:53 eval C3_stage (2026-09-27_10-59-14_centered/model_20593.pt): [eval] Wellplate-Centered-v0 C3_stage: success 0.906 over 128 episodes; ends {'time_out': 0.0781, 'plate_dropped': 0.0156, 'arm_unstable': 0.0, 'success': 0.9062}
- 04:53 C3 (0.005 m / 3° / 3°): training success 0.219, deterministic eval 0.906 (gate 0.4)
- 04:54 eval final_C3 (2026-09-27_10-59-14_centered/model_20593.pt): [eval] Wellplate-Centered-v0 final_C3: success 0.906 over 128 episodes; ends {'time_out': 0.0781, 'plate_dropped': 0.0156, 'arm_unstable': 0.0, 'success': 0.9062}
- 04:54 eval before_C3 (2026-09-27_02-29-31_stack/model_10790.pt): no result — see 2026-09-27_centered/eval_before_C3.log
- 04:54 eval final_0926criteria (2026-09-27_10-59-14_centered/model_20593.pt): no result — see 2026-09-27_centered/eval_final_0926criteria.log
- 04:55 recorded labelled episodes (final): [rec] wrote centered_viewS_8episodes_labelled.mp4: 8/8 successes
- 04:55 recorded labelled episodes (before): 
- 04:56 centred ladder finished

### 04:56–05:15 — curriculum finished; final evaluations, videos, charts
- C1 85.2 %, C2 87.5 %, **C3 90.6 %** deterministic (final criteria 5 mm / 3° / 3°, released and at rest).
- Two driver final evals failed on input size (the 09-26 policy has 205 inputs, the centred task 215; the reverse for
  the new policy in the 09-26 stack task). Redone by hand: 09-26 policy through a zero-weight widened copy
  (`2026-09-27_02-29-31_stack_widened`, named so no driver picks it up) → **0.0 %**; new policy at the 09-26 criteria
  in the centred task → 85.9 %.
- Video captions ran past the frame edge → two-line captions (`record_labelled.py`), side-by-side stacks its own
  caption above the frame (`side_by_side.py --band`); both labelled videos re-recorded.

## Morning read — 2026-09-27 (Round-2026-09-22, PLAN v4)

**The robot now stacks one well plate centred and aligned on the other: 90.6 % of 128 deterministic episodes** meet
all four conditions at once — centring ≤ 5 mm, twist ≤ 3°, tilt ≤ 3°, released with the plate at rest (target ≥ 40 %).
The 09-26 stack policy: 0.0 % at the same criteria (it centres to ~5 mm but leaves the plate twisted ~73° and holds it).
Successful episodes end at a median 2.4 mm off centre, 0.9° twist, 0.0° tilt.

| Stage | Centring / twist / tilt | Deterministic success |
|---|---|---|
| C1a | 15 mm / 45° / 5° | 67.2 % |
| C1b | 15 mm / 30° / 5° | 67.2 % |
| C1c | 15 mm / 20° / 5° | 73.4 % |
| C1 | 15 mm / 10° / 5° | 85.2 % |
| C2 | 10 mm / 5° / 3° | 87.5 % |
| C3 | 5 mm / 3° / 3° | **90.6 %** |

Evidence: `results/2026-09-27_centered/` — README, F5 (per-episode errors, before vs after), F6 (stages), V5 (before/after
video, captioned per episode). Final policy `2026-09-27_10-59-14_centered/model_20593.pt`.

What it took, in order (each confirmed by a measurement before the fix):
1. Twist measured on the plates' long edges (target mesh is rotated 49° inside its prim), 0°/180° equal.
2. The policy could not tell which way to turn → a twist observation (sin 2Δ, cos 2Δ), checkpoint widened with zero weights.
3. Adaptive learning rate stuck at its 1e-5 floor → fixed 1e-4. Wrist-yaw command scaled up (only ~15 % of each
   command is realized per step).
4. With success only below 10° twist nothing was ever rewarded → twist curriculum 45° → 30° → 20° → 10°.
5. The policy placed the plate but never let go: the success bonus paid ~1.7 once, below the critic's noise →
   bonus 50 → 600 (C1a 1.6 % → 67.2 %).
6. Driver bug: C1 restarted from the 09-26 policy after C1a–C1c → fixed within a minute, no training lost.

Not asked of Dewei: nothing blocked; no stop condition was hit.

Open / next (PLAN v4 §D4, unchanged order): 3 plates ((ii) hand-off, then (i)); loose bottom plate (currently fixed /
kinematic); realistic arm (gravity on + compensation); other RL libraries. Remaining failures at C3: 7.8 % time out
(plate not placed — mostly not picked up cleanly) and 1.6 % drops.

## 2026-09-27 — PLAN v5 (Dewei: "go ahead to the end of the plan")

- Definitions of done written for the remaining D4 steps (PLAN.md, top): E1 3 plates with hand-off, E2 3 plates all
  loose, E3 loose bottom plate, E4 realistic arm (gravity on + compensation), E5 other libraries.
- Measured first: all three of Martin's plates are the same mesh; the third plate's frame matches the object plate's; it
  sits out of reach today. skrl, rl_games and Stable-Baselines3 are already installed — no installs needed.

### E0 — three-plate code and checks (no training)
- Third plate dynamic at spawn; role stand-ins `mover` / `base` / `lower` let every existing term follow "the plate being
  moved" and "what it goes on"; phase switch on the first placement. Tasks `Wellplate-Stack3Handoff/Loose/LooseBottom-v0`.
- `scripts/probe_multi_plate.py` (16 envs each): observation 215 as before; in phase 1 the stand-ins equal the real
  plates exactly; a plate pre-placed on the bottom plate sits at 26.0 mm, 0.00 mm drift; forced first placements
  switched 9/9 with the placed pose carried over (≤ 1 mm incl. settling), plate back in the pick area, observation
  follows; twist via the base stand-in equals the plate's own frame (0.0001°); both loose plates rest on the table in
  areas A/B; the arm reaches plate 3's grasp point in area B (sub-mm); a loose bottom plate stays put (0.00 mm).
- Baseline, C3 policy on the 3-plate hand-off task without training: **0 %**. It completes the first placement in
  71 % of episodes, then aims the second plate at the old goal height (one plate too low) and knocks the first plate
  off (median 85 mm); 29 % drops, 9 % arm unstable. Expected — the policy never saw a goal that moves.
- Next: `run_stack3.sh` trains E1 (hand-off) from C3, then E2 and E3, gated on the sequential deterministic eval.

## 3-plate driver started Sun 27 Sep 2026 06:54:20 AM PDT — START_STAGE=E1, 512 envs, 1500 it./stage

- 06:54 train Wellplate-Stack3Handoff-v0: 1500 it., 512 envs, warm start 2026-09-27_10-59-14_centered/model_20593.pt

### E1 run 1 stopped after ~250 iterations — cause found in my role code (fix: canonical base orientation)
- First placements fell from 15 % of episodes to 0 within 200 iterations; time-outs 85 %.
- Cause: a plate is 180°-symmetric, so a plate placed either way round is the same plate — but its quaternion, as an
  observation input, differs by ~1 per component (and q vs −q likewise). The goal-orientation inputs never varied during
  C3 training (the bottom plate never moves), so the input normaliser divides them by ~0.01: a flipped base plate became
  a ~100σ input, and as the normaliser adapted, the phase-1 inputs shifted too — the policy lost the first placement.
- Fix: the base stand-in reports the representation closest to the bottom plate's quaternion (either end, either sign).
  Probe: phase-2 base orientation now within 0.0125 per component of the bottom plate's (a flip was ~1). All E0 checks
  still pass. Run 1 folder renamed `2026-09-27_13-54-28_stack3_ABANDONED`. E1 restarted from C3.
- Meanwhile (no GPU): E4 realistic-arm action written and checked — IK tracking with gravity on + compensation equals
  gravity off (0.0 mm at step 250; without compensation 434 mm off); E5 library configs, copied train/play scripts,
  shared episode counter and `run_libs.sh` written.

## 3-plate driver started Sun 27 Sep 2026 07:04:54 AM PDT — START_STAGE=E1, 512 envs, 1500 it./stage

- 07:04 train Wellplate-Stack3Handoff-v0: 1500 it., 512 envs, warm start 2026-09-27_10-59-14_centered/model_20593.pt

### E1 run 2 stopped too (same collapse) — the C3 skill was overwritten by training, now protected
- Run 2 (with the orientation fix) collapsed the same way: first placements 30 % → 3 % of episodes in 250 iterations.
- The collapsed checkpoint scores **0.8 %** on the plain 2-plate C3 task (C3: 90.6 %): plates still released on the goal,
  but centring 12 mm / twist 7° instead of 2.4 mm / 0.9°.
- Which part changed? Swap test (`scripts/swap_normalizer.py`): C3 weights + the collapsed run's input normaliser →
  **93.0 %**; collapsed weights + C3's normaliser → **3.9 %**. So the policy weights were overwritten, not the inputs.
- Why: half the envs started with a stack the policy kept crashing into, and every first placement continued into that
  failing second placement. Near the goal both look almost the same to the network (it never had to use the goal
  inputs), so the crash gradients overwrote the precise placing behaviour.
- Fix: TRAINING = single placements, 15 s as in C3 — a first-placement start ends at the placement exactly like the C3
  task; a stacked start practises the second placement. EVALUATION = the full sequence (both plates, 30 s). New log
  line `Episode_Termination/success_first` = first placements, to watch the C3 skill directly.
- Check: C3 on the new training task places 48/55 first-placement starts (87 %) and 1/73 stacked starts. Run 2 folder
  renamed `_ABANDONED`. E1 relaunched from C3.

## 3-plate driver started Sun 27 Sep 2026 07:24:03 AM PDT — START_STAGE=E1, 512 envs, 1500 it./stage

- 07:24 train Wellplate-Stack3Handoff-v0: 1500 it., 512 envs, warm start 2026-09-27_10-59-14_centered/model_20593.pt
- 15:3x (Claude) E1 run 3 check at iteration 20800 (where run 2 had collapsed): deterministic C3 skill **84.4 %** on the
  2-plate task (run 2: 0.8 %), centring 3.4 mm / twist 1.3°. The falling training success (0.37 → 0.14) is the usual
  exploration-noise effect seen in every stage since C1, not a collapse. Continuing.

### E1 run 3 stopped at ~21700 — single placements delayed the collapse but did not prevent it; fix 3: two skills
- At 20800 the C3 skill was intact (84.4 %); by 21700 it was down to **10.2 %** with a new failure: the policy stopped
  grasping (gripper near open, 37 % of plates ever leave the table, plate ends ~26 cm from the goal).
- Why (C3 on stacked starts, per episode): C3 carries the plate at a height that clears ONE plate. With a 2-plate stack
  it hits the stack's side, knocks the middle plate off (median 34 mm) and the carried plate often ends on its side.
  There was almost no successful second placement to learn from, and the crash / drop outcomes taught the shared policy
  not to grasp at all — in both phases, since it can hardly tell them apart.
- Fix 3 (the pattern that worked in C1–C3: separate what interferes, make the new part learnable in steps):
  1. **Two skills.** Policy A = C3, unchanged, does the first placement. Policy B, fine-tuned from C3, does only the
     second (run name `stack3b`). The evaluator switches per env by phase (`--checkpoint2`).
  2. **B curriculum.** B1: middle plate kinematic (cannot be knocked over; `Wellplate-Stack3HandoffKin-v0`). B2: middle
     plate dynamic. Gate after B2 = the E1 definition (both plates in sequence, A + B, deterministic, ≥ 40 %).
- Checks: C3 on the B1 task already stacks **4.7 %** (6/128; ~1 % with a dynamic middle plate) and most time-outs end
  with the plate ON the stack but off-centre — a learnable signal. The two-policy path works (A = B = C3 → 0 %, as the
  single-policy result). Run 3 folder renamed `_ABANDONED`.
- If fix 3 also brings no measurable improvement, that is stop condition 3 and I ask Dewei.

## Skills driver (E1 fix 3) started Sun 27 Sep 2026 08:15:02 AM PDT — START_STAGE=B1

- 08:15 train Wellplate-Stack3HandoffKin-v0 (run stack3b): 1000 it., 512 envs, warm start 2026-09-27_10-59-14_centered/model_20593.pt 
- 08:52 eval B1_stage (2026-09-27_15-15-09_stack3b/model_21592.pt): [eval] Wellplate-Stack3HandoffKin-v0 B1_stage: success 0.008 over 128 episodes; ends {'time_out': 0.8594, 'plate_dropped': 0.1328, 'arm_unstable': 0.0, 'success': 0.0078, 'success_first': 0.0}
- 08:52 B1: training success 0.001, deterministic eval 0.008 (gate 0.4)
- 08:52 B1 below gate → retry once (1000 it.)
- 08:52 train Wellplate-Stack3HandoffKin-v0 (run stack3b): 1000 it., 512 envs, warm start 2026-09-27_15-15-09_stack3b/model_21592.pt 

### E1 fix 3 result: B1 (kinematic stack at full height) failed — 4.7 % → 0.8 %; fix 4: a rising stack
- B1 (1000 it. from C3, middle plate kinematic): deterministic **0.8 %**, training success → 0.1 %. The middle plate
  stayed put (1.3 mm), so the kinematic stack worked — but the carried plate was released askew next to or on the stack
  (median 74 mm off, many on their side against it; 34 % of time-outs with the plate back on the table). The policy
  lowers to the old height, hits the stack and never finds "carry and release 26 mm higher".
- Count for stop condition 3: fix 2 was a measurable improvement (84 % vs 0.8 % retained), so fix 3 is the first
  failure since — not yet three in a row.
- Fix 4, from what worked in C1a–C1 (a tolerance raised in steps): a **rising stack**. Kinematic bodies do not collide
  with each other, so the kinematic middle plate can start INSIDE the bottom plate — at 0 mm the task is geometrically
  C3's — and rise 6.5 / 13 / 19.5 / 26 mm stage by stage; then B2 with a dynamic middle plate and the E1 gate.
  Check: C3 at 0 mm = **64 %** (above the 40 % gate; below 90.6 % because the plate lands on two overlapping tops ±2 mm).
- B1 folders renamed `_B1fail` / `_ABANDONED`.

## Skills driver (E1 fix 3) started Sun 27 Sep 2026 08:55:47 AM PDT — START_STAGE=B1h00

- 08:55 train Wellplate-Stack3HandoffKin-v0 (run stack3b): 300 it., 512 envs, warm start 2026-09-27_10-59-14_centered/model_20593.pt env.events.reset_multi.params.stack_height=0.0 env.terminations.success.params.check_lower=False
- 09:07 eval B1h00_stage (2026-09-27_15-55-54_stack3b/model_20892.pt): [eval] Wellplate-Stack3HandoffKin-v0 B1h00_stage: success 0.805 over 128 episodes; ends {'time_out': 0.1016, 'plate_dropped': 0.0938, 'arm_unstable': 0.0, 'success': 0.8047, 'success_first': 0.0}
- 09:07 B1h00: training success 0.500, deterministic eval 0.805 (gate 0.4)
- 09:07 train Wellplate-Stack3HandoffKin-v0 (run stack3b): 500 it., 512 envs, warm start 2026-09-27_15-55-54_stack3b/model_20892.pt env.events.reset_multi.params.stack_height=0.0065 env.terminations.success.params.check_lower=False
- 09:27 eval B1h07_stage (2026-09-27_16-08-01_stack3b/model_21391.pt): [eval] Wellplate-Stack3HandoffKin-v0 B1h07_stage: success 0.703 over 128 episodes; ends {'time_out': 0.2422, 'plate_dropped': 0.0547, 'arm_unstable': 0.0, 'success': 0.7031, 'success_first': 0.0}
- 09:27 B1h07: training success 0.358, deterministic eval 0.703 (gate 0.4)
- 09:27 train Wellplate-Stack3HandoffKin-v0 (run stack3b): 500 it., 512 envs, warm start 2026-09-27_16-08-01_stack3b/model_21391.pt env.events.reset_multi.params.stack_height=0.013 env.terminations.success.params.check_lower=False
- 09:46 eval B1h13_stage (2026-09-27_16-27-19_stack3b/model_21890.pt): [eval] Wellplate-Stack3HandoffKin-v0 B1h13_stage: success 0.828 over 128 episodes; ends {'time_out': 0.125, 'plate_dropped': 0.0469, 'arm_unstable': 0.0, 'success': 0.8281, 'success_first': 0.0}
- 09:46 B1h13: training success 0.477, deterministic eval 0.828 (gate 0.4)
- 09:46 train Wellplate-Stack3HandoffKin-v0 (run stack3b): 500 it., 512 envs, warm start 2026-09-27_16-27-19_stack3b/model_21890.pt env.events.reset_multi.params.stack_height=0.0195 env.terminations.success.params.check_lower=False
- 10:05 eval B1h20_stage (2026-09-27_16-46-12_stack3b/model_22389.pt): [eval] Wellplate-Stack3HandoffKin-v0 B1h20_stage: success 0.922 over 128 episodes; ends {'time_out': 0.0781, 'plate_dropped': 0.0, 'arm_unstable': 0.0, 'success': 0.9219, 'success_first': 0.0}
- 10:05 B1h20: training success 0.628, deterministic eval 0.922 (gate 0.4)
- 10:05 train Wellplate-Stack3HandoffKin-v0 (run stack3b): 500 it., 512 envs, warm start 2026-09-27_16-46-12_stack3b/model_22389.pt env.events.reset_multi.params.stack_height=0.027 env.terminations.success.params.check_lower=False
- 10:24 eval B1h26_stage (2026-09-27_17-05-30_stack3b/model_22888.pt): [eval] Wellplate-Stack3HandoffKin-v0 B1h26_stage: success 0.914 over 128 episodes; ends {'time_out': 0.0703, 'plate_dropped': 0.0156, 'arm_unstable': 0.0, 'success': 0.9141, 'success_first': 0.0}
- 10:24 B1h26: training success 0.689, deterministic eval 0.914 (gate 0.4)
- 10:24 train Wellplate-Stack3Handoff-v0 (run stack3b): 1500 it., 512 envs, warm start 2026-09-27_17-05-30_stack3b/model_22888.pt env.events.reset_multi.params.phase2_prob=1.0

### Rising stack worked; the hand-off was the next blocker (fix 5: start from recorded hand-offs)
- Rising-stack curriculum (kinematic middle plate), deterministic, second placement alone: **0 mm 80.5 %, 6.5 mm 70.3 %,
  13 mm 82.8 %, 19.5 mm 92.2 %, 26 mm (full) 91.4 %** — vs 0.8 % when trained at full height directly (fix 4 worked).
- But the full sequence with a dynamic middle plate (C3 + that policy): **1.6 %**. C3 still places the first plate in
  84 % of episodes; the second placement fails with the placed plate knocked a median 47 mm.
- Measured at the hand-off (`--track_switch`): within 5 control steps (0.17 s) of the switch the placed plate has moved
  > 5 mm in 61 % of envs (median 11 mm). The second skill was trained from the home pose; at the real hand-off the arm
  is at the stack with the gripper open around the plate just placed, and its first move drags it.
- Fix 5 (skill chaining): recorded 2000 real hand-offs (C3's releases: robot joint state + placed plate pose relative
  to the bottom plate, `data/handoff_bank.pt`); half of B2's starts come from them; plus a dense penalty while the
  placed plate sits displaced (−10 × displacement / 2 cm, capped, phase 2 only). Baseline on bank starts: 0 % (placed
  plate knocked 62 mm) — reproduces the hand-off failure. B2 retrains from the 26 mm kinematic stage.
- The first B2 run (home-pose starts only) was stopped at the diagnosis (`_B2homestart`).

## Skills driver (E1 fix 3) started Sun 27 Sep 2026 10:38:24 AM PDT — START_STAGE=B2

- 10:38 B1h00: skipped (START_STAGE=B2)
- 10:38 B1h07: skipped (START_STAGE=B2)
- 10:38 B1h13: skipped (START_STAGE=B2)
- 10:38 B1h20: skipped (START_STAGE=B2)
- 10:38 B1h26: skipped (START_STAGE=B2)
- 10:38 train Wellplate-Stack3Handoff-v0 (run stack3b): 1500 it., 512 envs, warm start 2026-09-27_17-05-30_stack3b/model_22888.pt env.events.reset_multi.params.phase2_prob=1.0 env.events.reset_multi.params.bank_prob=0.5
- 11:39 eval B2_stage (2026-09-27_10-59-14_centered/model_20593.pt + phase 2: 2026-09-27_17-38-32_stack3b/model_24387.pt): [eval] Wellplate-Stack3Handoff-v0 B2_stage: success 0.523 over 128 episodes; ends {'time_out': 0.2891, 'plate_dropped': 0.1875, 'arm_unstable': 0.0, 'success': 0.5234, 'success_first': 0.0}
- 11:39 B2: training success 0.640, deterministic eval 0.523 (gate 0.4)
- 11:39 skills driver finished: E1 (3 plates, hand-off) passed

### E1 passed — three plates stacked (hand-off): 52.3 %
- B2 (dynamic middle plate, half the starts from recorded hand-offs, displacement penalty), 1500 it.: training success
  1 % → 64 %; the **full sequence (C3 places the first plate, B2 the second) = 52.3 %** of 128 deterministic episodes at
  5 mm / 3° / 3°, both released, lower plate in place (gate 40 %). Ends: 28.9 % time-out, 18.8 % dropped.
- E2 baseline (all loose, plate 3 in pick area B), C3 + B2 without further training: **26.6 %**; first placement 84 %,
  second fails by drops (30) and time-outs (44). E2 stage added to the skills driver: B continues on loose-mode starts.

## Skills driver (E1 fix 3) started Sun 27 Sep 2026 11:43:04 AM PDT — START_STAGE=E2

- 11:43 B1h00: skipped (START_STAGE=E2)
- 11:43 B1h07: skipped (START_STAGE=E2)
- 11:43 B1h13: skipped (START_STAGE=E2)
- 11:43 B1h20: skipped (START_STAGE=E2)
- 11:43 B1h26: skipped (START_STAGE=E2)
- 11:43 B2: skipped (START_STAGE=E2)
- 11:43 train Wellplate-Stack3Loose-v0 (run stack3b): 1500 it., 512 envs, warm start 2026-09-27_17-38-32_stack3b/model_24387.pt env.events.reset_multi.params.phase2_prob=1.0 env.events.reset_multi.params.bank_prob=0.5
- 12:41 eval E2_stage (2026-09-27_10-59-14_centered/model_20593.pt + phase 2: 2026-09-27_18-43-12_stack3b/model_25886.pt): [eval] Wellplate-Stack3Loose-v0 E2_stage: success 0.461 over 128 episodes; ends {'time_out': 0.3359, 'plate_dropped': 0.2031, 'arm_unstable': 0.0, 'success': 0.4609, 'success_first': 0.0}
- 12:41 E2: training success 0.763, deterministic eval 0.461 (gate 0.4)
- 12:41 skills driver finished

### E2 passed — three plates, all loose: 46.1 %
- The second skill continued from B2 on all-loose starts (plate 3 in pick area B, half from recorded hand-offs), 1500 it.:
  full sequence (C3 + E2 policy) **46.1 %** of 128 deterministic episodes (baseline 26.6 %; gate 40 %). Ends: 33.6 %
  time-out, 20.3 % dropped. Policy: `2026-09-27_18-43-12_stack3b/model_25886.pt`.
- Next: E3 (loose bottom plate) with `run_e3.sh`: E3a fine-tunes the first skill from C3 on the loose bottom plate
  (run name stack3a), E3b the second skill from the E2 policy; gate = the full all-loose sequence with the loose bottom
  plate (moved ≤ 1 cm) by both fine-tuned skills.

## E3 driver started Sun 27 Sep 2026 12:41:51 PM PDT — START_STAGE=E3a

- 12:41 train Wellplate-Stack3LooseBottom-v0 (run stack3a): 1000 it., 512 envs, warm start 2026-09-27_10-59-14_centered/model_20593.pt env.events.reset_multi.params.phase2_prob=0.0

### E3 (loose bottom plate), attempt 1 stopped: the first skill collapsed into not grasping
- E3a run 1 (C3 fine-tuned on first placements onto the loose 50 g bottom plate): training success 8 % → 0 within ~10
  iterations, 22 % drops, lifting reward → 0 — the same learned avoidance as E1 runs 1–3.
- Baselines (C3, first placement onto a loose bottom plate): 2 kg **29.7 %**, 50 g **11.7 %**; in failed episodes the
  bottom plate is shoved 25 mm (2 kg) / 45 mm (50 g) — C3 presses down on its goal, which never mattered while the
  bottom plate was fixed.
- Fix (the recipe that worked twice today: difficulty in steps + penalise the damage directly): dense penalty while the
  bottom plate sits displaced (−10 × shift / 1 cm, capped, both phases), and a MASS curriculum for the bottom plate:
  20 kg → 2 kg → 0.5 kg → 0.15 kg → 0.05 kg (real), each stage gated; then the second skill on the real mass and the
  full-sequence gate. Run-1 folder renamed `_E3afail`.

## E3 driver started Sun 27 Sep 2026 01:16:27 PM PDT — START_STAGE=B1

- 13:16 train Wellplate-Stack3LooseBottom-v0 (run stack3a): 300 it., 512 envs, warm start 2026-09-27_10-59-14_centered/model_20593.pt env.events.reset_multi.params.phase2_prob=0.0 env.scene.table.spawn.target_mass=20.0
- 13:28 eval E3a_m20000_stage (2026-09-27_20-16-34_stack3a/model_20892.pt): [eval] Wellplate-Stack3LooseBottom-v0 E3a_m20000_stage: success 0.828 over 128 episodes; ends {'time_out': 0.0938, 'plate_dropped': 0.0781, 'arm_unstable': 0.0, 'success': 0.8281, 'success_first': 0.8281}
- 13:28 E3a_m20000: training success 0.398, deterministic eval 0.828 (gate 0.4)
- 13:28 train Wellplate-Stack3LooseBottom-v0 (run stack3a): 400 it., 512 envs, warm start 2026-09-27_20-16-34_stack3a/model_20892.pt env.events.reset_multi.params.phase2_prob=0.0 env.scene.table.spawn.target_mass=2.0
- 13:44 eval E3a_m2000_stage (2026-09-27_20-28-32_stack3a/model_21291.pt): [eval] Wellplate-Stack3LooseBottom-v0 E3a_m2000_stage: success 0.336 over 128 episodes; ends {'time_out': 0.5938, 'plate_dropped': 0.0625, 'arm_unstable': 0.0078, 'success': 0.3359, 'success_first': 0.3359}
- 13:44 E3a_m2000: training success 0.126, deterministic eval 0.336 (gate 0.4)
- 13:44 E3a_m2000 below gate → retry once (400 it.)
- 13:44 train Wellplate-Stack3LooseBottom-v0 (run stack3a): 400 it., 512 envs, warm start 2026-09-27_20-28-32_stack3a/model_21291.pt env.events.reset_multi.params.phase2_prob=0.0 env.scene.table.spawn.target_mass=2.0
- 14:01 eval E3a_m2000_retry (2026-09-27_20-44-47_stack3a/model_21690.pt): [eval] Wellplate-Stack3LooseBottom-v0 E3a_m2000_retry: success 0.602 over 128 episodes; ends {'time_out': 0.3203, 'plate_dropped': 0.0781, 'arm_unstable': 0.0, 'success': 0.6016, 'success_first': 0.6016}
- 14:01 E3a_m2000 (retry): training success 0.397, deterministic eval 0.602
- 14:01 train Wellplate-Stack3LooseBottom-v0 (run stack3a): 400 it., 512 envs, warm start 2026-09-27_20-44-47_stack3a/model_21690.pt env.events.reset_multi.params.phase2_prob=0.0 env.scene.table.spawn.target_mass=0.5
- 14:16 eval E3a_m500_stage (2026-09-27_21-01-06_stack3a/model_22089.pt): [eval] Wellplate-Stack3LooseBottom-v0 E3a_m500_stage: success 0.508 over 128 episodes; ends {'time_out': 0.4375, 'plate_dropped': 0.0547, 'arm_unstable': 0.0, 'success': 0.5078, 'success_first': 0.5078}
- 14:16 E3a_m500: training success 0.263, deterministic eval 0.508 (gate 0.4)
- 14:16 train Wellplate-Stack3LooseBottom-v0 (run stack3a): 400 it., 512 envs, warm start 2026-09-27_21-01-06_stack3a/model_22089.pt env.events.reset_multi.params.phase2_prob=0.0 env.scene.table.spawn.target_mass=0.15
- 14:31 eval E3a_m150_stage (2026-09-27_21-16-20_stack3a/model_22488.pt): [eval] Wellplate-Stack3LooseBottom-v0 E3a_m150_stage: success 0.375 over 128 episodes; ends {'time_out': 0.5469, 'plate_dropped': 0.0703, 'arm_unstable': 0.0078, 'success': 0.375, 'success_first': 0.375}
- 14:31 E3a_m150: training success 0.156, deterministic eval 0.375 (gate 0.4)
- 14:31 E3a_m150 below gate → retry once (400 it.)
- 14:31 train Wellplate-Stack3LooseBottom-v0 (run stack3a): 400 it., 512 envs, warm start 2026-09-27_21-16-20_stack3a/model_22488.pt env.events.reset_multi.params.phase2_prob=0.0 env.scene.table.spawn.target_mass=0.15
- 14:46 eval E3a_m150_retry (2026-09-27_21-31-25_stack3a/model_22887.pt): [eval] Wellplate-Stack3LooseBottom-v0 E3a_m150_retry: success 0.492 over 128 episodes; ends {'time_out': 0.375, 'plate_dropped': 0.1328, 'arm_unstable': 0.0, 'success': 0.4922, 'success_first': 0.4922}
- 14:46 E3a_m150 (retry): training success 0.288, deterministic eval 0.492
- 14:46 train Wellplate-Stack3LooseBottom-v0 (run stack3a): 600 it., 512 envs, warm start 2026-09-27_21-31-25_stack3a/model_22887.pt env.events.reset_multi.params.phase2_prob=0.0
- 15:08 eval E3a_stage (2026-09-27_21-46-39_stack3a/model_23486.pt): [eval] Wellplate-Stack3LooseBottom-v0 E3a_stage: success 0.617 over 128 episodes; ends {'time_out': 0.3203, 'plate_dropped': 0.0625, 'arm_unstable': 0.0, 'success': 0.6172, 'success_first': 0.6172}
- 15:08 E3a: training success 0.250, deterministic eval 0.617 (gate 0.4)
- 15:08 train Wellplate-Stack3LooseBottom-v0 (run stack3b): 1500 it., 512 envs, warm start 2026-09-27_18-43-12_stack3b/model_25886.pt env.events.reset_multi.params.phase2_prob=1.0 env.events.reset_multi.params.bank_prob=0.5
- 16:06 eval E3b_stage (2026-09-27_21-46-39_stack3a/model_23486.pt + phase 2: 2026-09-27_22-08-55_stack3b/model_27385.pt): [eval] Wellplate-Stack3LooseBottom-v0 E3b_stage: success 0.492 over 128 episodes; ends {'time_out': 0.4062, 'plate_dropped': 0.0938, 'arm_unstable': 0.0078, 'success': 0.4922, 'success_first': 0.0}
- 16:06 E3b: training success 0.779, deterministic eval 0.492 (gate 0.4)
- 16:06 E3 driver finished

### E3 passed (loose bottom plate) and E4 passed (realistic arm, no retraining needed)
- E3a mass curriculum, first skill, deterministic first placements onto the loose bottom plate: 20 kg 82.8 %, 2 kg 60.2 %
  (retry), 0.5 kg 50.8 %, 0.15 kg 49.2 % (retry), **50 g (real) 61.7 %** (C3 untrained: 11.7 %).
- E3b, second skill from the E2 policy on the loose bottom plate (half hand-off starts), 1500 it.: full sequence with
  both fine-tuned skills = **49.2 %** (all three plates loose, bottom plate moved ≤ 1 cm; gate 40 %).
- E4: the same two E3 policies with the realistic arm (robot gravity ON + gravity-compensation torques), no retraining:
  **54.7 %** — the compensated arm behaves like the gravity-off arm (tracking probe: identical to 0.1 mm), so the skills
  transfer unchanged. E4 done (tracking ≈ gravity off; E3 task ≥ 40 % with gravity on).
- Final policies: first placement `2026-09-27_21-46-39_stack3a/model_23486.pt`, second placement
  `2026-09-27_22-08-55_stack3b/model_27385.pt`. Next: videos, then E5 (other libraries).
- 16:19 E5 train rsl_rl on Wellplate-Reach-v0: 500 iterations-equivalent (6144000 env steps), 512 envs, from scratch
- 16:33 E5 rsl_rl Reach: 14 min, deterministic success 1.000
- 16:33 E5 train skrl_ppo on Wellplate-Reach-v0: 500 iterations-equivalent (6144000 env steps), 512 envs, from scratch
- 16:45 E5 skrl_ppo Reach: 11 min, deterministic success 1.000
- 16:45 E5 train skrl_sac on Wellplate-Reach-v0: 500 iterations-equivalent (6144000 env steps), 512 envs, from scratch
- 16:45 E5 skrl_sac Reach: training failed (exit 1, checkpoint 'none') — see 2026-09-27_libs/logs/train_Reach_skrl_sac.log
- 16:45 E5 train rl_games on Wellplate-Reach-v0: 500 iterations-equivalent (6144000 env steps), 512 envs, from scratch
- 16:57 E5 rl_games Reach: 13 min, deterministic success 1.000
- 16:57 E5 train sb3 on Wellplate-Reach-v0: 500 iterations-equivalent (6144000 env steps), 512 envs, from scratch
- 17:07 E5 sb3 Reach: 9 min, deterministic success 0.000
- 17:07 E5 train rsl_rl on Wellplate-Align-v0: 1000 iterations-equivalent (12288000 env steps), 512 envs, from scratch
- (Claude) E5 notes so far: Reach from scratch, 6.1 M env steps, deterministic: rsl_rl PPO 100 % (14 min), skrl PPO
  100 % (11 min), rl_games PPO 100 % (13 min), SB3 PPO **0 %** (9 min). SB3 is a real result for its settings, not an
  evaluation fault (its observation normalisation loaded; in training every episode ran the full 300 steps, reward
  0.17 → 0.24): SB3 has no KL-adaptive learning rate, and its KL early stop (target 0.01, measured 0.015) ends most
  updates after about one epoch. skrl SAC failed at start on skrl 2.1 field names (`actor_learning_rate`) — config
  fixed; Align uses the fix and Reach is re-run at the end.
- 17:34 E5 rsl_rl Align: 26 min, deterministic success 0.039
- 17:34 E5 train skrl_ppo on Wellplate-Align-v0: 1000 iterations-equivalent (12288000 env steps), 512 envs, from scratch
- 17:58 E5 skrl_ppo Align: 24 min, deterministic success 0.984
- 17:58 E5 train skrl_sac on Wellplate-Align-v0: 1000 iterations-equivalent (12288000 env steps), 512 envs, from scratch
- (Claude) E5 Align from scratch (12.3 M env steps): rsl_rl PPO **3.9 %**, skrl PPO **98.4 %** — same network, rollout,
  epochs, minibatches, entropy, KL target. Learning-rate traces (TensorBoard) explain it: rsl_rl's KL-adaptive schedule
  adjusts after every minibatch and sits at its 1e-5 floor from the first logged iteration (median 7.6e-5 over the run);
  skrl's adjusts once per update and stays at 8.5e-5–7.8e-4 (median 1.4e-4, starting ~6e-4). Same cause as the C-stage
  finding (09-27: rsl_rl's adaptive rate pinned at 1e-5 → fixed 1e-4 for the centred runner). Single seed per library:
  a direction, not a measured variance.
- 18:35 E5 skrl_sac Align: 37 min, deterministic success 0.000
- 18:35 E5 train rl_games on Wellplate-Align-v0: 1000 iterations-equivalent (12288000 env steps), 512 envs, from scratch
- 18:56 E5 rl_games Align: 20 min, deterministic success 0.000
- 18:56 E5 train sb3 on Wellplate-Align-v0: 1000 iterations-equivalent (12288000 env steps), 512 envs, from scratch
- 19:15 E5 sb3 Align: 19 min, deterministic success 0.000
- 19:15 E5 finished — table in results/2026-09-27_libs/libs.md
- 19:15 E5 train skrl_sac on Wellplate-Reach-v0: 500 iterations-equivalent (6144000 env steps), 512 envs, from scratch
- 19:32 E5 skrl_sac Reach: 17 min, deterministic success 0.000
- 19:32 E5 finished — table in results/2026-09-27_libs/libs.md
- 19:32 E5 train rsl_rl_fixed on Wellplate-Reach-v0: 500 iterations-equivalent (6144000 env steps), 512 envs, from scratch
- 19:46 E5 rsl_rl_fixed Reach: 14 min, deterministic success 1.000
- 19:46 E5 train rsl_rl_fixed on Wellplate-Align-v0: 1000 iterations-equivalent (12288000 env steps), 512 envs, from scratch
- 20:12 E5 rsl_rl_fixed Align: 25 min, deterministic success 0.000
- 20:12 E5 finished — table in results/2026-09-27_libs/libs.md
- (Claude) **Correction** to the entry above: the learning-rate traces do NOT explain the rsl_rl / skrl gap on Align. The
  test — rsl_rl with a FIXED learning rate 1e-4 (≈ skrl's median) — scored **0 %** on Align (100 % on Reach). Still
  untested differences: skrl normalises the value targets (value preprocessor; rsl_rl does not), skrl starts at a
  higher rate (~6e-4); and with one seed each, seed luck is possible. The gap is open, not explained.

## Morning read — 2026-09-27 evening (PLAN v5 done)

**All of PLAN v4 §D4 is done.** The robot stacks all three of Martin's plates — each within 5 mm / 3° twist / 3° tilt
of the one below, released, lower plate in place — with every plate starting loose, the bottom plate loose (moved
≤ 1 cm) and the realistic arm (gravity on + compensation): **54.7 %** of 128 deterministic episodes.

| Step | Result | Evidence |
|---|---|---|
| E1 3 plates, hand-off | 52.3 % | `results/2026-09-27_stack3/` |
| E2 3 plates, all loose | 46.1 % | same |
| E3 + loose bottom plate | 49.2 % | same |
| E4 + realistic arm | 54.7 % (no retraining) | same; videos V6 (overview), V7 (close-up) |
| E5 other libraries | comparison, no gate | `results/2026-09-27_libs/` (README, F9) |

E5 in one line: on Reach rsl_rl / skrl / rl_games PPO all 100 %; on Align from scratch only skrl PPO learned it
(98.4 %; rsl_rl 3.9 %, fixed-lr rsl_rl 0 %, rl_games 0 %, SB3 0 %, skrl SAC 0 %) — one seed each, cause of the skrl gap
open (value normalisation is the first thing to test).

What made the three-plate work possible (details above, 09-27 entries): two skills instead of one policy; a rising
stack for the second placement; start states recorded at real hand-offs; a mass curriculum for the loose bottom plate;
displacement penalties; gravity compensation. No stop condition was hit; nothing needs Dewei's decision to continue.

Open / next (for Dewei): single seeds everywhere; the ~36 % three-plate time-outs; one policy for both placements
(not needed for the result, but more elegant); camera-based plate detection (not in D4); whether to test skrl PPO
further (value normalisation, 3 seeds, warm-started along the ladder).

## 2026-09-28 — wrap-up for the weekly meeting

- Meeting materials (in `RL_DT_docs/_docs_legion/`): `presentations/2026-09-28-weekly/` (offline HTML slides with the
  videos, a Marp copy for PowerPoint export, hand-out), `reports/wellplate-round-2026-09-28.md` (detailed,
  with evidence paths), `guides/SHOWING_PROGRESS.md` (recordings with timestamps, TensorBoard), `learn/` (learning
  package: text + slides).
- New here: `results/2026-09-28_presentation/` (storyboard stills, training-curve chart T1 + CSVs),
  `scripts/make_presentation_assets.py`, `scripts/plot_training_curves.py`. TensorBoard bundle (not in git):
  `RL_Twin/_exports/tensorboard_wellplate_2026-09-28.tar.gz`.
- Correction made while writing: the black bottom plate is not explained by the `96WellPlate_thin.fbx` warnings (those
  are separate decor prims; the bottom plate uses the same mesh as the others) — cause not checked.
- 2026-09-28 (Dewei) **Training output no longer tracked.** Checkpoints, training-time videos and Hydra `outputs/`
  are git-ignored (see `.gitignore`, block dated 2026-09-28); run `params/*.yaml`, SB3 normalisers and the hand-off
  bank are tracked. The 83 unpushed commits of this round were rewritten to drop those files (backup branch
  `backup/pre-cleanup-2026-09-28`); files on disk untouched (4.6 GB in `WellPlate_RL/logs/`). Cited checkpoints stay
  on this laptop. Push size 4 GB → 176 MB.
