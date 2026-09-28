# Publication materials — work on `trossen-ai` (the Legion machine)

Companion to [`PUBLICATION_MATERIALS.md`](../_docs/PUBLICATION_MATERIALS.md), which is **not modified**.
Same rule applies within this file: a measured number or a code defect lives here once, and other
`_legion` documents link to it.

All results 2026-08-27 → 2026-08-29, RTX 5090 Laptop (Blackwell, `sm_120`), torch 2.13.0+cu130.
R7–R11, D12–D17 and M3–M6: 2026-09-22 → 09-28, well-plate task in Isaac Lab 2.3.2 / Isaac Sim 5.1, rsl_rl 5.0.1,
512 envs, deterministic evaluation over 128 episodes, one training seed per run.

---

## Findings index

**Results**
- [R1 — Gymnasium environments re-tested on GPU](#r1)
- [R2 — Toolkit drives four Isaac Lab built-in environments](#r2)
- [R3 — Digital twin via Isaac Lab, scaling 1→128 environments](#r3)
- [R4 — Digital twin via bare Isaac Sim](#r4)
- [R5 — Route comparison](#r5)
- [R6 — Multi-hour learning runs: neither route learns the task](#r6)
- [R7 — Well-plate ladder after the grasp fix](#r7)
- [R8 — Centred 2-plate stack, 90.6 %](#r8)
- [R9 — Three plates, loose bottom plate](#r9)
- [R10 — Gravity compensation removes the "robot gravity off" caveat](#r10)
- [R11 — RL library comparison on the same task](#r11)

**Code defects**
- [D1 — TensorFlow/Triton native-library conflict (segfault)](#d1)
- [D2 — `setup.py` omits every subpackage](#d2)
- [D3 — Three subpackages missing `__init__.py`](#d3)
- [D4 — `gymnasium-robotics` missing from requirements](#d4)
- [D5 — `test_torch_td3.py` assumes CPU tensors](#d5)
- [D6 — FetchReach incompatible with installed MuJoCo](#d6)
- [D7 — Door scene referenced by bare filename](#d7)
- [D8 — Stale absolute Windows path inside the USD](#d8)
- [D9 — Replay-buffer sampling is O(n) in buffer size](#d9)
- [D10 — Door handle is unreachable with the actions Martin's task exposes](#d10)
- [D11 — Fingertip prims do not resolve their own transforms](#d11)
- [D12 — 2F-140 loop-closing pad joint driven to 0](#d12)
- [D13 — Gripper closing axis wrong since 09-20](#d13)
- [D14 — Isaac Lab's `is_terminated_term` excludes truncations](#d14)
- [D15 — rsl_rl's KL-adaptive learning rate sits at its floor on these tasks](#d15)
- [D16 — Martin's GRIPPERFIX layer does not compose with our robot file](#d16)
- [D17 — The bottom plate's mesh is rotated 48.97° inside its prim](#d17)

**Method notes**
- [M1 — Why these numbers are not comparable to the published ones](#m1)
- [M2 — Isaac Sim cannot recreate environments in one process](#m2)
- [M3 — Report deterministic evaluation, not training success](#m3)
- [M4 — With success as a truncation, the success bonus is the only gain from finishing](#m4)
- [M5 — Fine-tuning a precise skill on a harder variant overwrites it](#m5)
- [M6 — Inputs that never varied in training break a warm start](#m6)

---

## Results

### R1 — Gymnasium environments re-tested on GPU {#r1}

`TorchTD3-v0`, each environment at its originally published episode/step counts, after [D1](#d1) made
the GPU usable. All reported `Device: cuda`.

| Environment | Episodes × steps | Final avg-20 | Wall time |
|---|---|---|---|
| `Pendulum-v1` | 100 × 200 | **−160.30** | 111 s |
| `MountainCarContinuous-v0` | 100 × 999 | **−1.02** | 477 s |
| `Hopper-v5` | 300 × 1000 | **187.10** | 71 s |
| `AdroitHandDoor-v1` | 20 × 200 | **−42.31** | 23 s |
| `FetchReachDense-Flat-v0` | 500 × 50 | **did not start** — [D6](#d6) | — |

A separate 100-episode `Pendulum-v1` run measured the learning curve: crosses avg-20 of −200 at
**episode 61**, ends at **−132.3** in 5 m 20 s. Curve every 10 episodes: −1226, −1221, −1320, −1325,
−727, −253, −233, −152, −128, −150.

For context only, from the published (CPU, different machine) results: the Keras baseline crosses at
episode 47 and ends at −163.0. **See [M1](#m1) before comparing.**

Evidence: `_toolkits/toolkit-isaaclab/results/<env>/index090_*`.

### R2 — Toolkit drives four Isaac Lab built-in environments {#r2}

Same `isaac_vec_adapter.py` used for Martin's door task, no per-task code, `--num_envs 16 --steps 30`.

| Task | Obs | Actions | Throughput |
|---|---|---|---|
| `Isaac-Cartpole-v0` | 4 | 1 | 659 env-steps/s |
| `Isaac-Ant-v0` | 60 | 8 | 440 env-steps/s |
| `Isaac-Reach-Franka-v0` | 32 | 7 | 257 env-steps/s |
| `Isaac-Open-Drawer-Franka-v0` | 31 | 8 | 364 env-steps/s |

**4/4 passed.** Observation dimension spans 4→60 and actions 1→8. This is the evidence that the
adapter is a general toolkit↔Isaac Lab bridge rather than something shaped around one scene.

Rewards are recorded in `isaac_integration/builtin_results.txt` but are **not** performance figures —
30 steps of a barely-initialised policy. They show only that the reward path is live.

`Isaac-Open-Drawer-Franka-v0` is NVIDIA's cabinet task: articulated object, grasp a handle, pull it
open — structurally the same problem as Martin's door, and probably what it was modelled on.

### R3 — Digital twin via Isaac Lab, scaling 1→128 environments {#r3}

`Isaac-UR5e-DoorOpen-v0`, obs 43, actions 7, 2 episodes × 40 steps per configuration.

| `--num_envs` | Env-steps/s (ep 0, ep 1) | Speed-up |
|---|---|---|
| 1 | 15, 17 | baseline |
| 16 | 191, 180 | ~11× |
| 64 | 419, 134 | ~9–25× |
| 128 | 271, 181 | ~12–17× |

Throughput climbs steeply to 16 environments then flattens. The plateau is explained: the simulator
steps N environments together on the GPU, but **action selection is one forward pass per environment
in a Python loop**, so past some N that loop dominates rather than the physics.

Per-episode variance is large (419 then 134 at 64 envs). Two episodes per configuration is not enough
to average out first-touch shader compilation. Treat as order-of-magnitude.

**The more important consequence than speed:** `cfgs/torch_td3.cfg` sets `warmup_size: 2500`. TD3
takes random actions until 2500 transitions are buffered. At 1 environment a 40-step episode
contributes 40 transitions; at 128 it contributes 5120. **The single-environment configuration cannot
practically reach the point where learning begins.** Parallelism here is a correctness requirement,
not only a speed optimisation.

### R4 — Digital twin via bare Isaac Sim {#r4}

No Isaac Lab, no Docker. `door_env_direct.py`, 345 lines written from scratch.

| | |
|---|---|
| Observation dim | 35 (assembled here; **not** the same as Isaac Lab's 43) |
| Action dim | 7 (6 UR5e arm joints + gripper) |
| Device | `cuda` |
| Throughput | 130–200 steps/s, single environment |

Verified against real physics rather than assumed:
- All 8 prim paths from Martin's config resolve
- Robot articulation exposes 15 DOF with the expected joint names
- `/World/OpenTronsFlex` is itself a 2-DOF articulation containing `Door_RevoluteJoint`
- Commanding the hinge to −30°, −90°, −170° reads back −29.5°, −88.3°, −167.9° — so observation,
  reward and success test are wired to live state

Evidence: `_toolkits/toolkit-isaacsim/_isaacsim_notes/`.

**Scope limit:** the reward here is three terms (approach / opening / effort). Martin's task encodes
roughly ten shaped terms across 1140 lines, tuned together. This is a structurally equivalent task,
**not** a reproduction.

### R5 — Route comparison {#r5}

Matched: 1 environment, 2 episodes × 40 steps.

| | Bare Isaac Sim | Isaac Lab + Docker |
|---|---|---|
| Throughput, 1 env | **148–151 steps/s** | 15–17 steps/s |
| Best measured | 148–151 (1 env only) | **~419** (64 envs) |
| Parallel environments | 1 | 1→128 tested |
| Code written | 345 lines | 248 lines |
| Task definition reused | none | **1140 lines** (Martin's) |
| Disk | 18 GB | 34.7 GB image + 23 GB base |
| Runs without Docker | **yes** | no |
| GUI | **yes, verified** | awkward from container |

The single-environment gap flatters the direct route: that overhead is Isaac Lab doing the work that
makes many environments possible. See [`comparison-isaacsim-vs-isaaclab.md`](reports/comparison-isaacsim-vs-isaaclab.md).

**Neither route has been shown to learn the door task.** All runs were minutes long with essentially
untrained policies. Nothing here supports a claim about learning performance, and the two routes do
not even use the same reward.

### R6 — Multi-hour learning runs: neither route learns the task {#r6}

Full write-up: [`long-run-learning-2026-08-30.md`](reports/long-run-learning-2026-08-30.md).

| | Bare Isaac Sim (base actuated, 10 actions) | Isaac Lab (Martin's config, 7 actions) |
|---|---|---|
| Episodes | ~1,610 | ~210 x 64 envs |
| avg-20 reward | 105.8 -> **334.3** (peak 338.4) | 5.85 -> **9.38** |
| Plateaued | ~episode 400 | immediately |
| Door opened | 2/162 sampled episodes (1.2%) | **never** |

**The trained policy, replayed deterministically without exploration noise, never moves the door -
6 episodes out of 6.** The 1.2% of training episodes where the door moved were exploration noise
shoving it, not learned behaviour; the peak of exactly 3.1416 rad is the hinge's -180 deg limit,
the signature of the door being knocked to its stop.

So the tripled reward is real optimisation of the approach and alignment terms, and **not** progress
on the task. Reported as such: claiming "learned to open the door" would have been wrong, and wrong
in the specific way the brief's no-brute-force-pushing requirement exists to prevent.

The Isaac Lab route's flat 9.38 is the *correct* outcome given [D10](#d10), not a training failure.

### R7 — Well-plate ladder after the grasp fix {#r7}

Well-plate task (Martin's Ridgeback + UR7e + Robotiq 2F-140, Martin's `WellPlates.usd`), PPO (rsl_rl), 512 envs.
Deterministic evaluation, 128 episodes per number, 2026-09-26.

| Stage | Training tolerance | Result | Strict tolerance | Result |
|---|---|---|---|---|
| Align | 4 cm / 20° | **82.0 %** | 2 cm / 15° / 10° | 0.0 % |
| Lift | 6 cm up, tilt < 10° | **87.5 %** | 10 cm up, tilt < 5° | 14.8 % |
| Stack, 2 plates | 3 cm / 1.5 cm / 11° | **50.8 %** | 1 cm / 5 mm / 5° | 22.7 % |

On 09-20/21 lift and stack were 0 % (no plate ever lifted). Preconditions: [D12](#d12), [D13](#d13) fixed; the grasp
held 16/16 in a scripted gate before training. Evidence: [`results/2026-09-26_summary/`](evidence/wellplate/results/2026-09-26_summary/)
(F4, V3, V4). **Why it matters:** the first plate lifted and stacked in this twin.

### R8 — Centred 2-plate stack, 90.6 % {#r8}

Success = centring ≤ 5 mm, twist ≤ 3° (long edges; 0° and 180° equal), tilt ≤ 3°, gripper open, plate at rest.
Curriculum, each stage warm-started from the previous, deterministic, 128 episodes:

| C1a 15 mm / 45° / 5° | C1b 30° | C1c 20° | C1 10° | C2 10 mm / 5° / 3° | C3 5 mm / 3° / 3° |
|---|---|---|---|---|---|
| 67.2 % | 67.2 % | 73.4 % | 85.2 % | 87.5 % | **90.6 %** |

Successful episodes: median 2.4 mm centring, 0.9° twist, 0.0° tilt. The 09-26 stack policy scores **0 %** at C3
criteria (median twist 73°). Made learnable by a twist observation, the curriculum and [M4](#m4). Evidence:
[`results/2026-09-27_centered/`](evidence/wellplate/results/2026-09-27_centered/) (F5 per-episode errors, F6, V5). **Why it matters:** precision placement, not only
contact — the tolerances of a real plate stack.

### R9 — Three plates, loose bottom plate {#r9}

Each placed plate within 5 mm / 3° / 3° of the one below, both released, the lower plate still in place;
deterministic, 128 episodes. Two policies (first / second placement, [M5](#m5)).

| Step | Setting | Result | Baseline |
|---|---|---|---|
| E1 | next plate handed off into the pick area | **52.3 %** | C3 alone 0 % |
| E2 | all plates start loose | **46.1 %** | 26.6 % |
| E3 | + loose 50 g bottom plate, moved ≤ 1 cm | **49.2 %** | — |
| E4 | + realistic arm ([R10](#r10)) | **54.7 %** | — |

Curricula: second placement with a kinematic middle plate rising 0 / 6.5 / 13 / 19.5 / 26 mm: 80.5 / 70.3 / 82.8 /
92.2 / **91.4 %** (trained at full height directly: **0.8 %**). First placement onto a loose bottom plate, mass
20 kg → 2 → 0.5 → 0.15 kg → 50 g: 82.8 / 60.2 / 50.8 / 49.2 / **61.7 %** (untrained at 50 g: 11.7 %). Final setting
failures: 36 % time-outs, 9 % drops. Evidence: [`results/2026-09-27_stack3/`](evidence/wellplate/results/2026-09-27_stack3/) (F7, F8, V6, V7, `stages.md`).
**Why it matters:** sequential multi-object manipulation with loose objects, and a measured account of what made
each hard part learnable.

### R10 — Gravity compensation removes the "robot gravity off" caveat {#r10}

IK tracking through the task's own action, 16 envs, P controller, error after 300 steps: gravity off **0.0 mm**;
gravity on, no compensation **434 mm**; gravity on + G(q) from PhysX inverse dynamics every physics step **0.0 mm**
(`scripts/probe_arm_tracking.py --arm {default,on,comp}`). The E3 policies, unchanged, on the gravity-on arm:
**54.7 %** vs 49.2 % gravity off (within sampling noise). **Why it matters:** policies trained with gravity off
transfer to a compensated arm, as on a real UR controller.

### R11 — RL library comparison on the same task {#r11}

From scratch, 512 envs, same env-step budget, one shared deterministic evaluation, one seed each:

| Stage | rsl_rl PPO | rsl_rl PPO fixed lr 1e-4 | skrl PPO | skrl SAC | rl_games PPO | SB3 PPO |
|---|---|---|---|---|---|---|
| Reach (6.1 M steps) | 100 % | 100 % | 100 % | 0 % | 100 % | 0 % |
| Align (12.3 M steps) | 3.9 % | 0 % | **98.4 %** | 0 % | 0 % | 0 % |

The skrl PPO advantage on Align is **unexplained** ([D15](#d15) was tested and rejected as the cause). SB3 PPO (fixed
rate + KL early stop) and skrl SAC (one gradient step per 512 env steps) look under-configured — not a verdict.
Evidence: [`results/2026-09-27_libs/`](evidence/wellplate/results/2026-09-27_libs/) (README, F9, `libs.md`). **Why it matters:** the library changed the outcome on
an identical task; worth a controlled follow-up (value normalisation, 3 seeds) before choosing one.

---

## Code defects

### D1 — TensorFlow/Triton native-library conflict {#d1}

**Severity: blocking.** `TorchTD3-v0` segfaulted before a single training step.

TensorFlow and Triton (PyTorch's GPU compiler, loaded lazily when an optimizer is constructed) ship
conflicting native libraries. **Whichever loads second segfaults.** The toolkit's import order loaded
TF first — via the Keras agents, and via `torch.utils.tensorboard`, which imports TF — so Triton lost.

Two-line reproduction:

```python
import tensorflow          # then
import triton._C.libtriton  # -> SIGSEGV
```

Reverse the order: both load fine.

Second symptom, independent of the crash: importing TF installs CUDA stub libraries, after which
`torch.cuda.is_available()` returns `False` with *"Error 302: Error loading CUDA libraries"*. The
torch agents therefore ran on **CPU while reporting no error**, even on a GPU machine.

Fix: 5 files, 191 lines, in `_patches/toolkit-tf-triton-fix.patch`. The core is pre-loading
`triton._C.libtriton` at package import, guarded by `if 'tensorflow' not in sys.modules` — if the
caller already imported TF, forcing Triton in afterwards is the crashing order.

Side effect: the lazy-import work cleared the blocker recorded in [`strategy.md`](../_docs/strategy.md) Part 2
("the package will not import in a torch-only container"). The Isaac Lab container ships PyTorch but
no TensorFlow, so this is what made the digital-twin wiring possible at all.

### D2 — `setup.py` omits every subpackage {#d2}

`packages=['jlab_opt_control']` lists no subpackages. A strict editable install (`pip install -e .`)
therefore exposes only the top-level package, and `import jlab_opt_control.buffers` fails with
`ModuleNotFoundError`. Unnoticed upstream because running from the repo root picks the subpackages up
via the current directory instead. Fixed with `find_packages()` plus `package_data` for `cfgs/*.cfg`.

### D3 — Three subpackages missing `__init__.py` {#d3}

`buffers/`, `drivers/` and `utils/` have no `__init__.py`, so they are implicit namespace packages
and `find_packages()` skips them even after [D2](#d2) is fixed. Added.

### D4 — `gymnasium-robotics` missing from requirements {#d4}

Required by `envs/robotics_flat.py` and by `utests/test_registry.py::test_env`, but in neither
`requirements.txt` nor `env.yaml`. Same category as the `pysindy` / `scikit-learn` gap already noted
in [`environment.md`](../_docs/environment.md). Installed here as 1.4.2 — but see [D6](#d6) before pinning.

### D5 — `test_torch_td3.py` assumes CPU tensors {#d5}

With [D1](#d1) fixed, 12 tests fail with *"Expected all tensors to be on the same device, but found
cuda:0 and cpu"*. The tests build plain CPU tensors (`torch.randn(...)`, no device) while the agent's
networks now correctly live on the GPU. Before the fix, TF broke CUDA detection so the agent silently
fell back to CPU and everything accidentally matched.

**Not a regression:** on the unmodified toolkit these same tests *segfault* — they could not run here
at all. And forcing `"device": "cpu"` in `cfgs/torch_td3.cfg` makes **all 47 pass**, confirming the
diagnosis. The agent is correct; the tests are not GPU-aware, having been written on a CPU-only
laptop.

Deliberately **not** fixed here — it is a design choice for Malachi: make the tests device-aware
(keeps GPU coverage, more edits) or pin them to CPU (smaller, leaves the GPU path untested).

Full suite after the fix: **281 passed, 13 failed** (12 of these + [D6](#d6)), 10 skipped, 39 min.

### D6 — FetchReach incompatible with installed MuJoCo {#d6}

```
gymnasium_robotics/utils/mujoco_utils.py:142 in set_joint_qpos
    assert joint_type in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE)
AssertionError
```

Fails inside gymnasium-robotics' own Fetch setup, before the toolkit is involved — the environment
cannot be constructed. Versions: `gymnasium-robotics 1.4.2`, `mujoco 3.12.0`, `gymnasium 1.3.0`.

Fetch-specific: `AdroitHandDoor-v1` constructs and trains on the same install, so
`envs/robotics_flat.py` is not implicated. Untested fixes: pin an older `gymnasium-robotics`, or an
older `mujoco`. Worth resolving if the published FetchReach numbers need reproducing.

### D7 — Door scene referenced by bare filename {#d7}

`ur5e_door_open_env_cfg.py` had `USD_PATH = "TrainingScene_flattened.usd"` while the file lives in a
sibling directory, so Isaac Lab failed with `FileNotFoundError`. Changed to
`"../ENV_OT_UR_door/TrainingScene_flattened.usd"`. The line sits under a comment reading
"User-editable paths", so per-setup adjustment appears expected rather than a defect. **Reapply if
Martin's repo is ever re-synced.**

### D8 — Stale absolute Windows path inside the USD {#d8}

`TrainingScene_flattened.usd` carries a payload reference to
`file:/C:/Users/prat615/Documents/ClonedProjects/digital_twin_models_1/Labware/OpentronsDoorAdapter/OpentronsDoorAdapter_large.usdc`,
which produces an alarming warning on every load.

**It is a red herring.** The prim
`/World/OpenTronsFlex/OpentronsDoorAdapter_large/LooRoll/Handle` — the exact path the task's reward
depends on — is present and valid, with its mesh and revolute joint, because the geometry was baked
in when the scene was flattened. Cosmetic only, but worth documenting so it does not cause a false
alarm later (it caused one here).

### D9 — Replay-buffer sampling is O(n) in buffer size {#d9}

**Severity: throttles every long run.** `er.py` sampled with
`np.random.choice(max_index, size=256, replace=False)`. NumPy implements that by building and
permuting an array of the whole buffer per call:

| buffer | `choice(replace=False)` | `randint` | penalty |
|---|---|---|---|
| 1,000 | 0.40 ms | 0.03 ms | 12x |
| 50,000 | 4.80 ms | 0.04 ms | 112x |
| 200,000 | 19.88 ms | 0.04 ms | 460x |

Observed live: the direct route fell from 150 to 10.8 steps/s at buffer 56k, the Isaac Lab route
from 195 to 21 env-steps/s, **with the GPU at 3% and the CPU pegged**. Fixed by switching to
`np.random.randint` - sampling with replacement, as SB3, CleanRL and the reference TD3
implementation all do. Measured 5-6 ms -> 0.050 ms at 60k entries.

**Not Isaac-specific**: affects every long run in the toolkit, including the published Gymnasium
results. Short runs never fill the buffer enough to see it.

### D10 — Door handle is unreachable with the actions Martin's task exposes {#d10}

**Severity: the task cannot be solved as configured.**

```
handle -> arm base distance                    0.834 m   (UR5e reach ~0.85 m)
closest gripper->handle, 300 random arm poses  0.207 m
closest, 400 poses WITH base translation       0.137 m
```

`ActionsCfg` exposes `arm_action` and `gripper_action` only - the Ridgeback's three base DOF are not
actuated - and `EventCfg` sets `position_range: (0.0, 0.0)`, so every episode starts from the same
out-of-reach pose. No policy can open the door.

This is the explanation for [R6](#r6)'s flat Isaac Lab curve. **A question for Martin**: is the base
meant to be actuated, or the robot meant to be parked within reach? The direct route was given the
base joints (action dim 7 -> 10) to work around it.

### D11 — Fingertip prims do not resolve their own transforms {#d11}

`left_inner_finger` and `right_inner_finger` report the **same world transform as `wrist_3_link`** -
verified via `XFormPrim`, `RigidPrim` and USD's `ComputeLocalToWorldTransform`, and confirmed to
move with the arm but never to separate from the wrist.

Martin's grasp test is `lfinger_z > handle_z AND rfinger_z < handle_z`, which with identical values
is `x > h AND x < h`: false always. In the ported reward this zeroed two terms outright, and because
the three opening terms are gated on the grasp state, **every door-opening term was permanently zero
as well** - there was no gradient toward opening the door. Substituted a TCP-height proxy.

Whether the same issue affects Isaac Lab's `FrameTransformer`-based version of these terms was not
tested, and is worth checking - if it does, Martin's own reward has dead terms too.

### D12 — 2F-140 loop-closing pad joint driven to 0 {#d12}

Our gripper action drove `*_inner_finger_pad_joint` to 0 — a ratio copied from the URDF, where the joint of that name
is a fixed pad mount. In NVIDIA's USD (`Robotiq_2F_140_physics_edit`) that joint closes the four-bar loop
(inner_finger → inner_knuckle) and must follow +q, as Isaac Lab's `set_finger_joint_pos_robotiq_2f140` does. Effect:
the drives fought the linkage and the pads tilted into a V — 12° at the 85 mm contact, 24° closed; with +q, 0.0°.
Evidence: [`results/2026-09-26_gripper_fix/`](evidence/wellplate/results/2026-09-26_gripper_fix/) (F2, V1). Ours, not the asset's; it blocked every lift since 09-20.

### D13 — Gripper closing axis wrong since 09-20 {#d13}

The plate's body frame is 127.6 mm (x) × 85.4 mm (y) × 26.0 mm, measured from the USD geometry relative to the plate
prim. `CLOSING_AXIS_INDEX` had been 0 since a 09-20 change based on a misread frame, so the fingers closed across the
128 mm side. Fixed to 1. Evidence: round file 09-26, grasp probe stills.

### D14 — Isaac Lab's `is_terminated_term` excludes truncations {#d14}

`isaaclab.envs.mdp.is_terminated_term` returns the named term only where it is a *termination*, masking time-out
(truncation) terms. Every success term here is `time_out=True` (so success bootstraps the value — see [M4](#m4)), so
the success bonus paid **0 in every stage until 09-26**; logs showed `success_bonus 0.0000` beside success 0.27. Fix:
a reward term reading `termination_manager.get_term(name)` directly (`mdp/wellplate_mdp.py: success_reward`). Easy to
miss for anyone combining success-as-truncation with a success bonus.

### D15 — rsl_rl's KL-adaptive learning rate sits at its floor on these tasks {#d15}

rsl_rl divides the rate by 1.5 per *minibatch* whenever KL > 2 × `desired_kl` (floor 1e-5). On the well-plate stages
it sat near the floor: median 2.3e-5 in the centred C-stages, 7.6e-5 on E5 Align (skrl's per-update schedule: median
1.4e-4). In the centred stages a fixed 1e-4 was part of what let the policy learn to turn. **Not** the cause of the
E5 gap: rsl_rl with a fixed 1e-4 also scored 0 % on Align ([R11](#r11)). Behaviour, not a bug — reported because the
default schedule silently limits learning here.

### D16 — Martin's GRIPPERFIX layer does not compose with our robot file {#d16}

`Ridgeback_UR7e_2f140_reworked.GRIPPERFIX.usd` (09-22) is a 12 KB assembly layer. Against our
`RidgebackWithURGripper/Ridgeback_UR7e.usd` every gripper prim composes as an undefined `over` (it expects `ur7e`
under `RidgebackWithBasicJoints`; ours has it beside `RidgebackWithStructure`), so the weld target is missing and the
gripper sits 0.86 m from the wrist. Not used; the fix was on our side ([D12](#d12)). Worth telling Martin so the two
robot files converge.

### D17 — The bottom plate's mesh is rotated 48.97° inside its prim {#d17}

In `WellPlates.usd` the target plate's mesh (`WellPlateSimple`) is rotated +48.97° about z relative to its prim; the
other two plates' meshes are aligned with their prims (long side = body x). Measuring twist from body axes is
therefore wrong by 49° for the bottom plate; we use its long axis `(cos 48.97°, sin 48.97°, 0)` in its body frame.
Evidence: `scripts/probe_plate_axes.py`, `probe_third_plate.py`. A data characteristic anyone measuring plate
alignment in this scene needs.

---

## Method notes

### M1 — Why these numbers are not comparable to the published ones {#m1}

Three independent reasons, any one of which is sufficient:

1. **The published runs were CPU runs on a different machine** (Dewei's laptop). Additionally, before
   [D1](#d1) was fixed, *any* torch run silently fell back to CPU regardless of hardware.
2. **The driver seeds from wall-clock time** (`run_continuous.py`), so no run is reproducible — old
   or new. Single seed per arm, as the roadmap already flags.
3. **Library versions differ.** Specifically, gymnasium-robotics warns that `AdroitHandDoor`'s reward
   function changed in 1.2.1 **without an environment version bump**, so the −42.31 in [R1](#r1) may
   be measuring a different reward than the published figure.

Read [R1](#r1) as *"the toolkit trains correctly on this machine"*, not as a benchmark comparison.

### M2 — Isaac Sim cannot recreate environments in one process {#m2}

A test that looped over four tasks in a single process — `env.close()` then `gym.make()` for the next
— **hung for 7 hours 40 minutes**: GPU pinned at 0% utilisation with 2.5 GB VRAM held, process
sleeping, no output after the first task.

Isaac Sim does not reliably support tearing down an environment and creating another within one
session. The loop must live in the shell: one process per task, with a `timeout` on each. Restructured
that way, the same four tasks finish in minutes.

Two operational lessons: never loop over Isaac Sim environment creation in-process, and always put a
timeout on a long-running background job — the 7h40m was invisible precisely because nothing would
ever have stopped it.

### M3 — Report deterministic evaluation, not training success {#m3}

Training logs measure success **with exploration noise**; with a binary gripper, noise crossing zero opens the grip
at random. Lift: training 19.9 %, deterministic 87.5 %. Within the centred and three-plate stages training success
often falls while the deterministic evaluation rises (chart [`results/2026-09-28_presentation/T1_training_curves.png`](evidence/wellplate/results/2026-09-28_presentation/T1_training_curves.png)).
Every number and gate in [R7](#r7)–[R11](#r11) is a separate deterministic evaluation over 128 episodes (one standard
deviation ≈ 4.4 points at 50 %).

### M4 — With success as a truncation, the success bonus is the only gain from finishing {#m4}

Success ends the episode as a truncation, so the value of the next state is bootstrapped and finishing does not
forfeit future shaping reward — but then "release now" vs "hold one more step" differ by little more than the bonus.
Isaac Lab scales rewards by the step (dt = 1/30 s): a bonus of weight 50 pays **1.7**, against a critic error of about
±5–7 (value loss 25–48). The centred policy placed the plate and held it: C1a **1.6 %**. Weight 600 (≈ 20 per success):
**67.2 %**. Size a one-off bonus against the critic's noise, not against the per-step rewards.

### M5 — Fine-tuning a precise skill on a harder variant overwrites it {#m5}

Training one policy for both placements destroyed the first-placement skill within ~200 iterations (2-plate task
90.6 % → 0.8 %). Swap test: C3 weights + the new input normaliser **93.0 %**; new weights + C3's normaliser **3.9 %** —
the weights, not the inputs. Training single placements delayed but did not prevent it: the policy then learned not
to grasp at all, because every carry toward the 2-plate stack crashed. What worked: keep the working skill as its own
policy; make the new part learnable in steps ([R9](#r9) curricula); train the second skill from **start states
recorded at the real hand-off** — from the home pose its first move dragged the plate just placed (> 5 mm within
0.17 s in 61 % of envs).

### M6 — Inputs that never varied in training break a warm start {#m6}

rsl_rl normalises inputs as `(x − mean) / (std + 0.01)`. The goal-pose inputs never varied during the 2-plate
training (fixed bottom plate, locked base), so their std was ≈ 0. With three plates, a base plate lying the other way
round — physically the same plate — gave a quaternion differing by ~1 per component: a ~100σ input, and first
placements fell from 15 % to 0 within 200 iterations. Fix: report symmetric quantities in a canonical form (the
representation closest to the bottom plate's, either end, either sign).
