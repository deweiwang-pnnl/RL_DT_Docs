# Team discussion — items arising from the Legion machine work

Companion to [`team-discussion.md`](../_docs/team-discussion.md), which is **not modified**. Grouped by who
can act on each item. Every number cited lives in
[`PUBLICATION_MATERIALS_legion.md`](PUBLICATION_MATERIALS_legion.md).

---

## For Malachi — three toolkit bugs and one proposal

### 1. TensorFlow and Triton conflict, and it segfaults the torch agents

The most consequential finding. `TorchTD3-v0` could not run at all on this machine — a segfault
before the first training step. Root cause is a native-library load-order conflict between
TensorFlow and Triton (which torch pulls in when constructing an optimizer): **whichever loads second
crashes**. Full write-up and the two-line reproduction:
[D1](PUBLICATION_MATERIALS_legion.md#d1).

A second symptom is arguably worse than the crash, because it is silent: importing TensorFlow
installs CUDA stubs that make `torch.cuda.is_available()` return `False`. **Any torch agent in a
process that has imported TF has been running on CPU while reporting nothing wrong** — including,
presumably, on other machines where the segfault does not occur.

The fix is 5 files / 191 lines, standalone in `_patches/toolkit-tf-triton-fix.patch`, and is
additive: the Keras agents were regression-tested and still train. It also clears the blocker
recorded in [`strategy.md`](../_docs/strategy.md) Part 2 — the package now imports in a torch-only container,
which is what made the Isaac Lab work possible.

**Ask:** is this worth upstreaming, and if so does the guarded pre-load approach look right to you?

### 2. `pip install -e .` does not work — packaging omits every subpackage

`setup.py` declares `packages=['jlab_opt_control']` with no subpackages, and `buffers/`, `drivers/`
and `utils/` have no `__init__.py`. A strict editable install therefore exposes only the top-level
package and `import jlab_opt_control.buffers` fails. It goes unnoticed because running from the repo
root finds the subpackages via the current directory. [D2](PUBLICATION_MATERIALS_legion.md#d2),
[D3](PUBLICATION_MATERIALS_legion.md#d3). Small, safe fix — `find_packages()` plus three
`__init__.py` files.

### 3. `gymnasium-robotics` is required but not declared

`envs/robotics_flat.py` needs it, and `utests/test_registry.py::test_env` fails without it, but it is
in neither `requirements.txt` nor `env.yaml`. Same category as the `pysindy` / `scikit-learn` gap
already noted in `environment.md`. [D4](PUBLICATION_MATERIALS_legion.md#d4) — though see
[D6](PUBLICATION_MATERIALS_legion.md#d6) before choosing a version to pin.

### 3b. Replay-buffer sampling is O(n) — this affects your published results too

`er.py` samples with `np.random.choice(max_index, size=256, replace=False)`. NumPy implements that
by permuting an array of the entire buffer on every call:

| buffer | `choice(replace=False)` | `randint` | penalty |
|---|---|---|---|
| 50,000 | 4.80 ms | 0.04 ms | 112x |
| 200,000 | 19.88 ms | 0.04 ms | 460x |

We hit it live: throughput collapsed from 150 to 10.8 steps/s with the **GPU idling at 3%** while
the CPU pegged - the sampling was the bottleneck, not the physics or the network. One-line fix to
`np.random.randint` (sampling with replacement, as SB3, CleanRL and the reference TD3 implementation
all do): 5-6 ms -> 0.050 ms at 60k entries.

This is not Isaac-specific. Any run long enough to fill a buffer is affected, including the
published Gymnasium results - short runs simply never reach the buffer sizes where it bites.
[D9](PUBLICATION_MATERIALS_legion.md#d9).

### 4. Proposal — a `batch_action` method on the agent

**The highest-value next change for either integration route.** Action selection is currently one
forward pass per environment, in a Python loop. That is why throughput plateaus past ~16 environments
([R3](PUBLICATION_MATERIALS_legion.md#r3)) despite the simulator stepping all of them together on the
GPU. One batched forward pass for N states would remove it. Unlike everything else done here, this is
a change to the agent itself rather than to a wrapper, so it needs your view on the interface.

### 5. Decision needed — `test_torch_td3.py` and the GPU

With the TF/Triton fix in place, 12 tests fail with a CPU/CUDA device mismatch: they build plain CPU
tensors while the agent's networks now correctly live on the GPU. **Not a regression** — on the
unmodified toolkit those tests *segfault* on this machine, and forcing `"device": "cpu"` makes all 47
pass. Deliberately left unfixed, because there are two defensible options and it is your test suite:
make the tests device-aware (keeps GPU coverage) or pin them to CPU (smaller change, GPU path goes
untested). [D5](PUBLICATION_MATERIALS_legion.md#d5).

---

## For Martin — a blocking question about the task, then two asset issues

### 0. The handle may not be reachable in your task either — worth checking

The most important item here. Measured on the door scene:

```
handle -> arm base distance                    0.834 m   (UR5e reach ~0.85 m)
closest gripper->handle, 300 random arm poses  0.207 m
closest, 400 poses WITH base translation       0.137 m
```

`ActionsCfg` exposes `arm_action` and `gripper_action` only, so the Ridgeback's three base DOF are
never actuated, and `EventCfg` sets `position_range: (0.0, 0.0)` so every episode starts from the
same pose. On our runs the gripper never got within 20 cm of the handle and the door never moved -
across 210 episodes x 64 environments.

**Question: is the base meant to be actuated, or the robot meant to be parked closer?** Either
resolves it. We added the base joints on our bare-Isaac-Sim variant to work around it, but that is a
divergence from your config rather than a fix to it. Worth checking whether your own `rl_games` PPO
runs ever open the door - if they do, something in our setup differs and we would like to know what.

### 0b. Do your fingertip reward terms fire?

`left_inner_finger` and `right_inner_finger` report the same world transform as `wrist_3_link` when
read through `XFormPrim`, `RigidPrim`, or USD's `ComputeLocalToWorldTransform`. Your
`align_grasp_around_handle` and `approach_gripper_handle` test whether the two fingertips straddle
the handle in z, which with identical values can never be true - and the three opening terms are
gated on that grasp state.

Your version goes through Isaac Lab's `FrameTransformer` rather than raw prims, so it may resolve
correctly where ours did not - **we did not test that**. But if it does not, several of your reward
terms are dead and the opening terms with them. [D11](PUBLICATION_MATERIALS_legion.md#d11).

## Martin — two asset issues, one trivial and one cosmetic

### 1. The door scene is referenced by bare filename

`RL_CloudTesting/ur5e_door_open_env_cfg.py` had `USD_PATH = "TrainingScene_flattened.usd"`, but the
file lives in `ENV_OT_UR_door/`, one directory across. Isaac Lab fails with `FileNotFoundError` until
it is changed to `"../ENV_OT_UR_door/TrainingScene_flattened.usd"`. The line sits under a
"User-editable paths" comment, so this may be intentional per-setup configuration rather than a bug —
worth confirming which. [D7](PUBLICATION_MATERIALS_legion.md#d7).

### 2. A stale absolute Windows path inside the flattened USD

Every load prints a warning about not finding
`C:/Users/prat615/.../OpentronsDoorAdapter_large.usdc`. **It is harmless** — the handle geometry was
baked in when the scene was flattened, and the prim the reward depends on
(`/World/OpenTronsFlex/OpentronsDoorAdapter_large/LooRoll/Handle`) is present and valid, mesh and
revolute joint included. It caused a false alarm here before being checked properly. Worth clearing
from the asset if it is easy, purely so it stops looking alarming.
[D8](PUBLICATION_MATERIALS_legion.md#d8).

### 3. Question — is the door meant to open negatively?

The hinge's USD limits are `lowerLimit=-180°, upperLimit=0°`, so the door swings negative as it
opens. Martin's own config carries the same fact as `DOOR_OPEN_DIR`, so this looks intended — but it
is the kind of sign convention worth stating explicitly somewhere, since getting it backwards scores
a correctly-opened door as zero reward (which happened here on the first attempt).

---

## For Alvika — container and version notes

### 1. The 5.1.0 warning was well placed, and worth making louder

The Isaac Sim download page defaults to 6.0.1; a 5.0.0 build was downloaded here by mistake before
the version was checked. Worth stating the required version in the `isaaclab_dt-main` README itself
rather than only in conversation, since `.env.base` already pins `ISAACSIM_VERSION=5.1.0` and the two
should visibly agree.

**Also useful to know:** Isaac Sim 5.1.0 downloads directly from
`download.isaacsim.omniverse.nvidia.com` with no NGC login, as does the container base image from
`nvcr.io`. Neither needed credentials, which matters for machines that cannot reach GitLab.

### 2. `envs_builtin/` does not exist in this copy

The README documents baking small scenes into the image via `envs_builtin/`, but the directory is
absent from the copy here, so nothing is baked in. Mounting Martin's assets externally worked fine
and is probably the better fit at 2 GB — but the README and the repo currently disagree.

### 3. `.env.base` ships with another machine's paths

`EXTERNAL_USD_PATH` and `EXTERNAL_PROJECT_PATH` pointed at `/home/aienabledrobotics2/Desktop/...`.
Expected for a per-machine setting, but a placeholder value plus a line in the README ("set these two
before first start") would save the next person a confusing empty mount.

---

## Team-wide — what these results do and do not show

Worth being explicit before any of this is presented, because the distinction is easy to lose:

**Established:** the toolkit can drive Martin's digital twin, through two independent routes; the
adapter generalises across four Isaac Lab built-in tasks with observation dimensions from 4 to 60;
parallelism scales to at least 128 environments.

**Not established:** that any of this *learns the door task*. Every run was minutes long with an
essentially untrained policy. The two routes do not even use the same reward function — the direct
route uses a simplified three-term reward written here, not Martin's ten tuned terms. No claim about
learning performance is supported by any number in these documents.

The natural next question — *does TD3 actually learn to open the door, and how does it compare to the
existing rl_games PPO baseline?* — is unanswered and would need long runs on the Isaac Lab route,
which is the only one that can currently reach TD3's warmup threshold at all.
