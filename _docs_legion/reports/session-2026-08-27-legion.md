# Connecting the RL toolkit to the digital twin — session report

**Machine:** `trossen-ai` (Legion, RTX 5090) · **Dates:** 2026-08-27 → 2026-08-29
**Repo:** `github.com/Dewei-Wang-xx/RL4DT-Toolkit` · **Detail:** [`WORKLOG_legion.md`](../WORKLOG_legion.md)

---

## Summary

The RL toolkit now drives the digital twin, through **two independent stacks**, on the GPU. Getting
there required fixing a bug that prevented the toolkit from running on this hardware at all — and
that fix incidentally cleared a blocker the project had already documented as standing in the way of
container-based Isaac work.

**Six things that were not true three days ago:**

1. The toolkit runs on Blackwell GPUs (it segfaulted; now trains, and actually uses the GPU rather
   than silently falling back to CPU).
2. The toolkit imports in a torch-only container — the blocker recorded in
   [`strategy.md`](../_docs/strategy.md) Part 2.
3. The toolkit drives Martin's door task through **Isaac Lab**, scaling to 128 parallel robots.
4. The toolkit drives the same task through **bare Isaac Sim**, with no Isaac Lab and no Docker.
5. The adapter is demonstrably general — it drove four Isaac Lab built-in tasks unchanged.
6. Isaac Sim is installed two ways, including a working GUI for exploring the twin visually.

**What is now known, and was an open question when this was first written:** multi-hour runs were
subsequently done on both routes. **Neither learns to open the door**, and the reason is measured -
the handle is out of reach with the actions the task exposes. That is arguably the most useful
result of the whole exercise. See [`long-run-learning-2026-08-30.md`](long-run-learning-2026-08-30.md)
and [Limits](#what-this-does-not-show).

---

## 1. The blocker: the toolkit could not run on this machine

`TorchTD3-v0` segfaulted a few milliseconds after starting, before a single training step.

**Root cause:** TensorFlow and Triton (PyTorch's GPU compiler, loaded lazily when an optimizer is
built) ship conflicting native libraries. **Whichever loads second crashes.** Two lines reproduce it:

```python
import tensorflow          # then
import triton._C.libtriton  # -> SIGSEGV
```

Reverse the order and both load fine. The toolkit's import order loaded TensorFlow first — through
the Keras agents, and through `torch.utils.tensorboard`, which imports TF — so Triton lost.

**A second symptom is arguably worse, because it is silent.** Importing TensorFlow installs CUDA stub
libraries, after which `torch.cuda.is_available()` returns `False`. Any torch agent in a process that
has imported TF has been **running on CPU while reporting nothing wrong** — including, presumably, on
machines where the segfault never occurs.

**Fix:** 5 files, 191 lines. Pre-load Triton at package import, guarded so it does nothing when TF is
already present; make the Keras agents, models and the TF-backed `Model` base class import lazily.
Additive — the Keras agents were regression-tested and still train. Standalone patch and full
write-up in [`../_patches/README.md`](../_patches/README.md).

**The side effect was worth more than the fix itself.** The lazy imports mean the package now imports
where TensorFlow is not installed at all — which is exactly the Isaac Lab container. Everything in
sections 3–6 depends on this.

> **An honest note on how this was found.** The crash was first diagnosed as a known upstream
> PyTorch/Blackwell bug and written up as unfixable locally. That was wrong. It was corrected only
> because Dewei pointed out the same code runs fine on other machines, which prompted a proper
> bisect. Recorded because the wrong turn is instructive.

**Three further toolkit bugs** surfaced along the way, all pre-existing and all with fixes ready:
`setup.py` omits every subpackage so `pip install -e .` is broken; three subpackages lack
`__init__.py`; `gymnasium-robotics` is required but undeclared. Write-ups for Malachi in
[`team-discussion_legion.md`](../team-discussion_legion.md).

---

## 2. Environments re-tested on GPU

Four of five published environments reproduced, all reporting `Device: cuda`.

| Environment | Episodes × steps | Final avg-20 | Wall time |
|---|---|---|---|
| `Pendulum-v1` | 100 × 200 | −160.30 | 111 s |
| `MountainCarContinuous-v0` | 100 × 999 | −1.02 | 477 s |
| `Hopper-v5` | 300 × 1000 | 187.10 | 71 s |
| `AdroitHandDoor-v1` | 20 × 200 | −42.31 | 23 s |
| `FetchReachDense-Flat-v0` | 500 × 50 | **could not start** | — |

A dedicated Pendulum run crosses avg-20 of −200 at **episode 61** and ends at **−132.3**.

**Two caveats that matter more than the numbers.** `FetchReach` fails inside gymnasium-robotics' own
setup code against `mujoco 3.12.0` — before the toolkit is involved, and Fetch-specific. And
`AdroitHandDoor`'s reward function changed in gymnasium-robotics 1.2.1 *without an environment
version bump*, so that figure is not comparable to the published one. More generally these results
are **not** comparable to the published ones: those were CPU runs on a different machine, and the
driver seeds from wall-clock time, so nothing is reproducible either way.

---

## 3. Isaac Sim installed two ways, deliberately

| | Purpose | Status |
|---|---|---|
| **Docker container** (Isaac Lab 2.3.2 + Isaac Sim 5.1.0) | Training | Built locally, 34.7 GB, GPU passthrough verified |
| **Workstation install** (Isaac Sim 5.1.0) | Looking at the twin | GUI reaches "app ready" in ~16 s, no errors |

Version 5.1.0 in both, per Alvika's warning — the download page defaults to 6.0.1, and Martin's assets
were authored in 5.1. A 5.0.0 build had been fetched from a PNNL machine first; 5.1.0 turned out to
download directly here without an NGC login, so no transfer was needed.

Two guides written: [`ISAAC_SIM_UI_GUIDE.md`](../guides/ISAAC_SIM_UI_GUIDE.md) for exploring the twin visually,
and [`DIGITAL_TWIN_HOWTO.md`](../guides/DIGITAL_TWIN_HOWTO.md) for the Docker route. Both mark which steps were
verified and which were not.

---

## 4. Route A — digital twin via Isaac Lab + Docker

Martin's task as written, driven by the toolkit's TD3 through a vectorised adapter.

| `--num_envs` | Env-steps/s | Speed-up |
|---|---|---|
| 1 | 15–17 | baseline |
| 16 | 180–191 | ~11× |
| 64 | 134–419 | ~9–25× |
| 128 | 181–271 | ~12–17× |

Throughput climbs steeply to 16 environments then flattens, because action selection is still **one
forward pass per environment** in a Python loop while the simulator steps them all together on the
GPU.

**Why parallelism is a correctness issue here, not just speed.** `warmup_size` is 2500 — TD3 takes
random actions until 2500 transitions are buffered. At one environment a 40-step episode contributes
40 transitions; at 128 it contributes 5120. **A single-environment configuration cannot practically
reach the point where learning begins.**

---

## 5. Route B — digital twin via bare Isaac Sim

No Isaac Lab, no Docker. `door_env_direct.py` (345 lines) reimplements what Isaac Lab was providing:
scene loading, observation assembly, action application, reward, termination, reset.

Works: **35 observations, 7 actions, on `cuda`, 130–200 steps/s.**

Verified against physics rather than inferred from absence of errors — all eight prim paths resolve,
the articulation exposes 15 DOF with expected names, and commanding the door hinge to −30°/−90°/−170°
reads back within 2°. **That check caught a real bug:** the door opens in the *negative* direction, so
the first implementation scored a fully-opened door as zero reward.

**Scope, stated plainly:** the reward here is three terms (approach / opening / effort) against
Martin's roughly ten tuned terms across 1140 lines. A structurally equivalent task, **not** a
reproduction.

---

## 6. The adapter generalises

Four Isaac Lab built-in tasks, same adapter, **no per-task code**:

| Task | Obs | Actions | Throughput |
|---|---|---|---|
| `Isaac-Cartpole-v0` | 4 | 1 | 659 env-steps/s |
| `Isaac-Ant-v0` | 60 | 8 | 440 env-steps/s |
| `Isaac-Reach-Franka-v0` | 32 | 7 | 257 env-steps/s |
| `Isaac-Open-Drawer-Franka-v0` | 31 | 8 | 364 env-steps/s |

Observation dimensions from 4 to 60. This is what shows the adapter is a genuine toolkit↔Isaac Lab
bridge rather than something shaped around one scene. `Open-Drawer-Franka` is NVIDIA's cabinet task —
structurally the same problem as Martin's door, and probably what it was modelled on.

---

## 7. Comparing the two routes

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
makes many environments possible, and the direct route cannot scale without reimplementing it.

**Recommendation — keep both, for different jobs.** Isaac Lab for training: it has the parallelism,
Martin's real task, and a reproducible pinned environment, and it is the only route that can reach
TD3's warmup threshold. Bare Isaac Sim for GUI exploration, for learning how the twin is put
together, and as the natural starting point if the real Ridgeback + UR5e becomes the target — its
plain step loop maps onto one physical robot far more directly than a vectorised manager-based
framework does.

---

## What this does not show

Worth stating before any of this is presented, because it is easy to lose:

- **Neither route learns the door task.** Multi-hour runs settled this: the direct route's reward
  tripled and converged, but the trained policy replayed deterministically moves the door in 0 of 6
  episodes. The Isaac Lab route never moved the door at all. The task is not solvable with the
  actions currently exposed - the handle is 0.834 m from an arm with ~0.85 m of reach, and the base
  is not actuated. Full account in
  [`long-run-learning-2026-08-30.md`](long-run-learning-2026-08-30.md).
- **The two routes do not use the same reward**, so they cannot be compared on learning at all.
- **Throughput figures are order-of-magnitude.** Two episodes per configuration, with large
  per-episode variance (419 then 134 env-steps/s at 64 environments).
- **Nothing is reproducible run to run** — the driver seeds from wall-clock time.

The natural next question — *does TD3 actually learn to open the door, and how does it compare to the
existing rl_games PPO baseline?* — is unanswered, and needs long runs on the Isaac Lab route.

---

## Next steps

1. **Resolve the reachability question with Martin.** Nothing else matters until the gripper can
   reach the handle: either actuate the base in his task, or park the robot closer. This is the
   blocker, and it is measured rather than suspected.
2. **`batch_action` on the agent.** The highest-value toolkit change: one batched forward pass for N
   states instead of N separate passes. It is what caps throughput, and unlike the adapters it is a
   change to Malachi's code, so it needs his view.
3. **Fix the O(n) replay-buffer sampling upstream** — it throttles every long run in the toolkit,
   not just the Isaac ones.
3. **Send the three toolkit bugs upstream** — write-ups ready in
   [`team-discussion_legion.md`](../team-discussion_legion.md).
4. **Decide `test_torch_td3.py`'s device handling** (Malachi's call — 12 tests assume CPU tensors).
5. **Revisit the kernel pin** when Ubuntu ships a matching NVIDIA module, so the machine resumes
   kernel security updates.

---

## Where everything is

| | |
|---|---|
| Session detail, day by day | [`rounds/Round-2026-08-27-legion-gpu-fix-and-dt-integration.md`](rounds/Round-2026-08-27-legion-gpu-fix-and-dt-integration.md) |
| Every number and code defect | [`PUBLICATION_MATERIALS_legion.md`](../PUBLICATION_MATERIALS_legion.md) |
| Machine setup and its limits | [`environment_legion.md`](../environment_legion.md) |
| Decisions and their reasoning | [`decisions_legion.md`](../decisions_legion.md) |
| Items for Malachi, Martin, Alvika | [`team-discussion_legion.md`](../team-discussion_legion.md) |
| The toolkit fix, standalone | [`../_patches/README.md`](../_patches/README.md) |
| Isaac Lab route code | `../_toolkits/toolkit-isaaclab/isaac_integration/` |
| Bare Isaac Sim route code | `../_toolkits/toolkit-isaacsim/` |

**A note on how this work was produced:** the investigation, code and documents in this round were
produced with an AI coding agent working under direction, over three days. Worth deciding how you
want that described before the material is presented onward.
