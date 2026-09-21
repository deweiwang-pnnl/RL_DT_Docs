# Round-2026-08-17 — TorchTD3-v0: write it, test it, match the Keras baseline

**Goal:** install the agent harness, reorganize the docs, then write a PyTorch TD3 agent in
`jlab_opt_control/agents/` and show it matches `KerasTD3-v0` on real Gymnasium environments.
**Done =** `--agent TorchTD3-v0` trains through the unmodified driver and reaches roughly the same
reward as `--agent KerasTD3-v0` under the same cfg values, with unit tests behind the claim.
**Real purpose:** understand this toolkit well enough to apply it to the Isaac Lab digital twin task.
Understanding over speed.

**Status:** done — a fifth environment (`AdroitHandDoor-v1`) is still running; its numbers get
appended when it finishes.

## Where the work happens

| Repo | Branch | Contents |
|---|---|---|
| `<PROJECT_ROOT>/SciOptControlToolkit` | `develop-dw` | **toolkit code** — base `48e624f`, HEAD `a085ad9` |
| `<PROJECT_ROOT>/RL_DT` | `develop` | **notes and logs** |

No notes in the toolkit repo, no toolkit code in RL_DT. Never `git push` in either — commit only.

## Plan

- [x] Install the five slash commands to `~/.claude/commands/`
- [x] Reorganize documentation into `_docs/`, grouped by lifetime
- [x] `models/actor_fcnn_torch.py` + `models/critic_fcnn_torch.py` + `core/torch_model_core.py` + cfgs
- [x] `cfgs/torch_td3.cfg` + `agents/torch_td3.py` registered as `TorchTD3-v0`
- [x] Verify the driver's `tf.convert_to_tensor(state)` coercion works in the torch agent
- [x] Run on `Pendulum-v1` and compare against `KerasTD3-v0`
- [x] Three more environments: `Hopper-v5`, `MountainCarContinuous-v0`, `FetchReachDense-Flat-v0`
- [x] Unit tests for the actor (22), the critic and the agent (47), the flattened envs (13)
- [x] Confirm the tests discriminate, by injecting defects
- [ ] `AdroitHandDoor-v1` — in flight
- [ ] ≥3 seeds per arm (single seed only so far)

## Log

### 2026-08-17

**Harness and docs.** Five commands copied to `~/.claude/commands/`, verified byte-identical.
Documentation reorganized into `_docs/` grouped by lifetime; `_notes/` no longer exists. Details in
the WORKLOG entry — the substance of the round starts below.

**`ee4ced6` 12:40 — the actor and the shared model base.** `models/actor_fcnn_torch.py` (160 lines),
`core/torch_model_core.py` (58), `cfgs/actor_fcnn_torch.cfg`, `cfgs/critic_fcnn_torch.cfg`,
registration, and `utests/test_torch_models.py` (250 lines, 22 tests).

The translation, concretely:

| Keras / TF | PyTorch |
|---|---|
| `tf.GradientTape` | `zero_grad` / `backward` / `step` |
| `get_weights` / `set_weights` | `load_state_dict` |
| shape inference on first call | explicit `nn.Linear(in_features, out_features)` |
| `tf.constant` for the action scale | `register_buffer` |
| `call(self, x, training=False)` | `forward(self, x)` |

One non-obvious hazard: Keras `Dense` initializes Glorot-uniform, PyTorch `Linear` Kaiming-uniform.
For a 256×256 layer the bounds are `sqrt(6/512) = 0.1083` and `1/sqrt(256) = 0.0625`, a factor of
1.7. Left at framework defaults, a Torch-vs-Keras reward curve is partly an *initialization*
comparison. Exposed as a cfg key `weight_init`, set to Glorot, and asserted in a test that fails if
the torch default creeps back.

**`61646af` 12:57 — the agent.** `agents/torch_td3.py` (437 lines), `cfgs/torch_td3.cfg` (19 lines),
`models/critic_fcnn_torch.py` (119), registration as `TorchTD3-v0`.

Config, not code: 17 keys against `keras_td3.cfg`'s 11. The 11 shared keys are byte-identical —
`warmup_size` 2500, `batch_size` 256, both learning rates 3e-4, `tau` 0.005, `discount` 0.99,
`buffer_type` ER-v0, `exploration_noise_fraction` 0.1. Of the six extra, four promote Keras
*hardcoded literals* to keys **at their existing values** (`actor_update_freq` 2,
`critic_update_freq` 2, `target_noise_clip` 0.5 which was a literal at `keras_td3.py:148`,
`target_policy_noise` 0.2 at line 218), and two have no Keras counterpart at all: `seed` and
`device`.

`seed` is a genuine improvement rather than a port artefact. The Keras agent seeds from
`time.time_ns()`, so no Keras run is repeatable; the torch agent seeds `random`, `numpy`, `torch`,
CUDA and the action space before any model is constructed, so network initialization is part of what
is reproducible.

**The driver was not touched.** `run_continuous.py` calls `agent.action(tf.convert_to_tensor(state))`,
so the torch agent coerces with `torch.as_tensor(np.asarray(x))` on its own side rather than asking
the driver to change. Verified by a test that passes a plain Python list and gets the same action as
the equivalent array.

**Pendulum-v1, 100 episodes, and it matches.** Torch final avg-20 **−149.29**
(`results/Pendulum/index010_..._20260817-125718`) against Keras **−157.63** and **−162.98** on two
seeds. Shape of the curve differs from the endpoint: Keras crosses −200 at episodes 47 and 48, Torch
not until 57. Slower to take off, better at the end.

**Hopper-v5, 300 episodes.** Torch **180.12** vs Keras **168.29**. Hopper is the only one of the four
environments that terminates early — 20 of 20 random-action episodes ended in `terminated`, mean
length 27.5 steps — which makes it the only environment that exercises the `(1 - dones)` factor in
the Bellman target at all. That observation is what later motivated a unit test for it.

### 2026-08-18

**MountainCarContinuous-v0, 100 episodes — both agents fail, identically.** Torch −1.05, Keras −1.01.
Both drop from roughly −33 to −1.0 by episode 3 and reach the goal in **0 of 100 episodes**. This is
TD3's canonical hard-exploration failure: Gaussian noise at 10% of the action range never carries the
car to the flag, so the policy converges on "spend no energy". Kept deliberately. A tie on a failure
case is stronger evidence of a faithful port than a win would be.

Two incidental findings while monitoring these runs:

- TensorBoard silently showed nothing for `index031`. The data was there (7 tags, confirmed with
  `EventAccumulator`); each run directory held two event files and TensorBoard polls only one unless
  `--reload_multifile=true` is passed. It had latched onto the empty 78-byte file because both were
  created in the same second.
- The Keras agent makes its own `tf.summary` writer the process default, so the *driver's* scalars
  land in the agent's event file. The torch agent uses `torch.utils.tensorboard.SummaryWriter` and
  leaves TF's global default alone. Both end up in `metrics/` and TensorBoard merges them, so the
  cross-framework overlay works.

**`a085ad9` 22:05 — the robotics flatten adapter.** `envs/robotics_flat.py` (108 lines),
registration, `utests/test_robotics_envs.py` (169 lines, 13 tests).

The blocker was one line. `run_continuous.py:191` is
`num_states = env.observation_space.shape[0]`. Every goal-conditioned environment in
gymnasium-robotics — all the Fetch, Maze, Hand and Kitchen tasks, 217 registered ids — publishes a
`Dict` space of `achieved_goal` / `desired_goal` / `observation` whose `.shape` is `None`, so that
line raises `TypeError` and none of them can be run.

`make_flat_env` wraps in `FlattenObservation` **only** when the space is a `Dict`, and is registered
through the toolkit's own registry, which accepts a callable entry point. `AdroitHandDoor-v1` already
has a `Box` space and is passed through untouched — asserted by a test that walks the wrapper chain.

`FlattenObservation` concatenates in **sorted key order**, so a Fetch observation becomes
`achieved_goal(3) | desired_goal(3) | observation(10)` = `Box(16)`. The agents' input layout depends
on that ordering, so it is pinned by a test that rebuilds the expected vector from the *unwrapped*
env at seed 1234 rather than trusting the documented behaviour.

Recorded in the module docstring, because it will be asked: flattening alone does not make every
goal-conditioned task learnable. FetchPush, FetchSlide and FetchPickAndPlace need Hindsight
Experience Replay, which this toolkit does not have (only `ER-v0` and `PER-v0`).

**FetchReachDense-Flat-v0, 500 episodes.** Torch −1.51 final / **−1.07 best** avg-20 in 6 m 00 s;
Keras −1.22 / −1.22 in 10 m 13 s. Keras converged slightly better, Torch ran **40% faster** in wall
clock on identical episode counts.

### 2026-08-19

**Closed the biggest hole in the port: the critic and the agent had no unit tests.** 22 tests existed
and all 22 tested `ActorFCNNTorch`. `CriticFCNNTorch` (119 lines) and `TorchTD3` (437 lines, 13
methods) had none — **556 of the 716 ported lines**, including every line of the Bellman target,
verified only by "the reward curve went up". A reward curve is a weak oracle: swap `min` for `max` in
the clipped double-Q step and Pendulum still learns, just worse.

`utests/test_torch_td3.py`, 47 tests, 53 seconds. It runs against a 3-state / 2-action stub
environment built from real `gymnasium.spaces.Box` objects, so no MuJoCo is loaded, and a
`tempfile.mkdtemp()` logdir, so nothing is written into the repository. The key assertions are
hand-computed rather than golden-valued:

- Target critics stubbed at 5 and 3, reward 1, γ = 0.99 → `minimum` gives 3 → target 3.97 → critic
  loss exactly 15.7609. Asserted both orderings, so a `maximum` is caught either way.
- Same batch with `dones = 1` → the bootstrap term vanishes → target 1.0, loss 1.0.
- Importance weights of 2 exactly double the loss (the `PER-v0` path, which no run has used).
- Actor loss with a constant critic at 4.0 is exactly −4.0, and the critic's parameters do not move.
- `soft_update` at tau 0.0 / 0.25 / 0.5 / 1.0, including the direction (target toward source, not
  the reverse) and that *buffers* are copied outright rather than blended.
- Delayed policy updates over 10 `train()` calls: critic 10, actor 5.
- `save`/`load` round trip into a fresh agent, all six state dicts compared element-wise, plus a
  guard test proving a fresh unloaded agent differs — otherwise the round trip could pass trivially.

**One constraint discovered while writing them:** unlike the models, the agent's cfg path has no
`isabs` handling — it is always `os.path.join(dirname(__file__), "../cfgs/", cfg)` — so a test cannot
point at a temporary cfg file. The tests use the real `torch_td3.cfg` and mutate attributes
afterwards.

**Then tested the tests.** A suite that passes on the first run is weak information. Three defects
injected into `torch_td3.py`, one at a time, file restored after each:

| Injected defect | Tests that failed |
|---|---|
| `torch.minimum` → `torch.maximum` | 3 |
| `(1.0 - dones)` → `dones` | 5 |
| `tp.mul_(1 - tau).add_(sp, alpha=tau)` → tau swapped | 1 |

Only one test catches the tau swap, and that is correct rather than thin: the tau = 0.5 midpoint case
is symmetric under the swap and *should* still pass. The dedicated direction test at tau = 0.25 is
what catches it.

**A defect in the toolkit's own test suite, found by accident.** Timing `pytest utests/` file by file
left 11 real training-run directories in `results/`, indistinguishable from experiments in a
TensorBoard listing. `test_baselines.py` and `test_agents.py` train actual agents, and logdir
resolves relative to the working directory. Deleted. Also worth knowing: `pytest utests/` as a whole
exceeds ten minutes because `test_baselines.py` alone takes over three, so it is run one file at a
time.

**AdroitHandDoor-v1 started.** A 20-episode probe first, to measure rather than guess: 3 m 45 s total
of which only **38 seconds** was the episodes — the other 3 m 07 s is fixed startup (TF and MuJoCo
import, plus allocating a 1M-row buffer for a 39-D state). Steady state **3.3 s/episode** once past
the 2500-step warmup. avg-20 −42.58 against a −45.58 random-action baseline.

Full run launched 00:44, 1000 episodes per arm, sequential, with `--bsize 200000`. That cap loses
nothing — 1000 episodes generates exactly 200k steps — and cuts each `buffer.npy` write from about
860 MB to 170 MB, which matters because `results/` lives inside OneDrive.

## Tests run

| What | Command | Result |
|---|---|---|
| Actor unit tests | `pytest utests/test_torch_models.py` | 22 passed |
| Critic + agent unit tests | `pytest utests/test_torch_td3.py` | **47 passed**, 53 s |
| Flattened env tests | `pytest utests/test_robotics_envs.py` | 13 passed, 7 s |
| Mutation check | 3 defects injected into `torch_td3.py` | all 3 caught (3 / 5 / 1 tests) |
| `Pendulum-v1`, 100 ep | `--agent TorchTD3-v0 --env Pendulum-v1` | **−149.29** vs Keras −157.63 / −162.98 |
| `Hopper-v5`, 300 ep | `--agent TorchTD3-v0 --env Hopper-v5` | **180.12** vs Keras 168.29 |
| `MountainCarContinuous-v0`, 100 ep | `--agent TorchTD3-v0 --env MountainCarContinuous-v0` | −1.05 vs Keras −1.01; both fail, 0/100 reach the goal |
| `FetchReachDense-Flat-v0`, 500 ep | `--agent TorchTD3-v0 --env FetchReachDense-Flat-v0` | −1.51 (best −1.07), 6 m 00 s vs Keras **−1.22**, 10 m 13 s |
| `AdroitHandDoor-v1`, 20 ep probe | `--nepisodes 20` | −42.58 avg-20, 3.3 s/ep, clean |
| `AdroitHandDoor-v1`, 1000 ep × 2 arms | `--nepisodes 1000 --bsize 200000` | **in flight** — at ep 145 the Torch arm is −36.77 avg-20, best single −28.1 |

Every reward figure is a single seed. The Keras arm cannot be re-seeded at all, since that agent
seeds from wall clock.

## Decisions

Copied to [`../decisions.md`](../decisions.md).

- **Additive-only changes to the toolkit.** `git diff --stat 48e624f..HEAD` is 1376 insertions and
  **zero deletions**. Rules out the cleaner 3-line driver fix for `Dict` observation spaces; that
  becomes an upstream proposal for Malachi to decide on.
- **`seed` and `device` are cfg keys with no Keras counterpart.** Deliberately breaks byte-identical
  cfg parity, in exchange for reproducibility the Keras agent cannot offer.
- **Four Keras hardcoded literals promoted to cfg keys at their existing values.** Removes magic
  numbers without changing behaviour, so the framework comparison stays controlled.

## Carried over

- **`AdroitHandDoor-v1` 1000-episode runs**, both arms. Estimate on the trend at episode 145: both
  plateau around −25 to −32 avg-20 and **do not open the door**. 200k steps is one to two orders of
  magnitude below the 1–5M published Adroit results use, and the dense reward pays for approach
  rather than success. Replace this paragraph with the measured result.
- **≥3 seeds per arm.** Every comparison in this round is single-seed. This is the largest remaining
  weakness in the evidence, not a missing feature.
- **The upstream proposal** — the 3-line driver `FlattenObservation` patch, plus the two driver
  defects found in Round-08-12 (the sign-inverted checkpoint threshold and the `nepisode_avg` unit
  mismatch). To be written here, not applied to the toolkit.
- **`PER-v0` and `--inference True` are unit-tested but never run end-to-end.** Neither is known
  broken; neither has been exercised by a real run.
- **Q1 (architecture A/B/C) and Q2 (what the ported TD3 is ultimately for)** still need Malachi.
- **`pysindy` not installed**; three of the four notebooks need it.
