# Publication materials — work on `trossen-ai` (the Legion machine)

Companion to [`PUBLICATION_MATERIALS.md`](../_docs/PUBLICATION_MATERIALS.md), which is **not modified**.
Same rule applies within this file: a measured number or a code defect lives here once, and other
`_legion` documents link to it.

All results 2026-08-27 → 2026-08-29, RTX 5090 Laptop (Blackwell, `sm_120`), torch 2.13.0+cu130.

---

## Findings index

**Results**
- [R1 — Gymnasium environments re-tested on GPU](#r1)
- [R2 — Toolkit drives four Isaac Lab built-in environments](#r2)
- [R3 — Digital twin via Isaac Lab, scaling 1→128 environments](#r3)
- [R4 — Digital twin via bare Isaac Sim](#r4)
- [R5 — Route comparison](#r5)
- [R6 — Multi-hour learning runs: neither route learns the task](#r6)

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

**Method notes**
- [M1 — Why these numbers are not comparable to the published ones](#m1)
- [M2 — Isaac Sim cannot recreate environments in one process](#m2)

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
makes many environments possible. See [`comparison-isaacsim-vs-isaaclab.md`](comparison-isaacsim-vs-isaaclab.md).

**Neither route has been shown to learn the door task.** All runs were minutes long with essentially
untrained policies. Nothing here supports a claim about learning performance, and the two routes do
not even use the same reward.

### R6 — Multi-hour learning runs: neither route learns the task {#r6}

Full write-up: [`long-run-learning-2026-08-30.md`](long-run-learning-2026-08-30.md).

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
