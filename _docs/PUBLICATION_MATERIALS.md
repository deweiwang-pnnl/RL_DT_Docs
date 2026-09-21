# PUBLICATION_MATERIALS

Things learned that could end up in a paper, a report, or a group presentation. Distinct from
[`WORKLOG.md`](WORKLOG.md) — that records *what was done*, this records *what is worth telling
someone else*.

**This is the canonical home for every measured number and every code defect in the project.** Other
files link here rather than restating. Every entry attaches its **evidence** — logdir, commit SHA,
command line — because an unattributed claim cannot go in a paper.

## Findings index

Scan this; read only the entries you need. Sixteen entries.

| Date | The claim | |
|---|---|---|
| 08-18 | `TorchTD3-v0` reproduces the Keras baseline across four Gymnasium environments — ahead on two, behind on one, tied on one | [→](#2026-08-18--torchtd3-v0-reproduces-the-keras-baseline-on-four-gymnasium-environments) |
| 08-12 | Keras TD3 solves `Pendulum-v1` on stock cfg — the number the port had to match | [→](#2026-08-12--keras-td3-baseline-on-pendulum-v1-the-number-the-port-must-match) |
| 08-19 | Mutation testing, not a green suite, is what makes tests evidence — three injected defects, caught by 3 / 5 / 1 tests | [→](#2026-08-19--mutation-testing-is-what-turns-a-passing-suite-into-evidence) |
| 08-18 | Mixed-direction results are the *correct* evidence for a faithful port; the tie on the shared failure case is the strongest single piece | [→](#2026-08-18--mixed-direction-results-are-the-correct-evidence-for-a-faithful-port) |
| 08-17 | Weight initialization is a silent confound across frameworks — Glorot vs Kaiming is a factor of 1.7 at 256 wide, so it must be a named config key | [→](#2026-08-17--weight-initialization-must-be-an-explicit-config-key-when-comparing-frameworks) |
| 08-18 | Flattening `Dict` observation spaces at the registry rather than the driver opens 217 goal-conditioned envs — and the sorted-key layout must be asserted, not assumed | [→](#2026-08-18--flattening-dict-observation-spaces-at-the-registry-not-in-the-driver) |
| 08-12 | Only the *agent* layer needs PyTorch; the driver and buffer need work for **vectorization**, not framework — conflating the two is the mistake | [→](#2026-08-12--only-the-agent-layer-needs-pytorch-not-the-whole-toolkit) |
| 08-12 | TD3 is the extension point the method contribution is expressed through — every research variant overrides exactly one function, `train_critic` | [→](#2026-08-12--td3-is-the-extension-point-the-method-contribution-is-expressed-through) |
| 08-10 | Store `terminated`, never `terminated or truncated` — zeroing the bootstrap at a time limit teaches the critic that good states are worthless | [→](#2026-08-10--store-terminated-never-terminated-or-truncated) |
| 08-12 | The reference toolkit's "best model" criterion can only ever say yes: an averaging window in the wrong units, plus a relative threshold that inverts on negative rewards | [→](#2026-08-12--a-best-model-criterion-that-can-only-ever-say-yes) |
| 08-12 | Seeding the *training* env does not make evaluation reproducible — a 170-point evaluation spread at one fixed seed, and the evaluation number is the published one | [→](#2026-08-12--seeding-the-training-env-does-not-make-evaluation-reproducible) |
| 08-12 | The reference replay buffer's sampling cost is linear in occupancy — 82 µs at 5k rows, 16.2 ms at 1M — so it is invisible on a smoke test and dominant later | [→](#2026-08-12--the-reference-replay-buffers-sampling-cost-is-linear-in-buffer-occupancy) |
| 08-19 | A model loader that fails silently: six files matched by prefix, any miss continues with random weights, so an inference number can be a random policy's number | [→](#2026-08-19--a-model-loader-that-fails-silently-and-reports-a-random-policys-numbers) |
| 08-19 | Running the reference test suite writes real training runs into `results/`, indistinguishable from experiments | [→](#2026-08-19--running-the-reference-test-suite-writes-training-runs-into-the-results-tree) |
| 08-10 | A green `Pendulum-v1` smoke test cannot validate termination handling — its `terminated` is always `False` | [→](#2026-08-10--a-green-pendulum-v1-smoke-test-does-not-validate-termination-handling) |
| 08-10 | The reference toolkit is not reproducible as published — three wall-clock seeds and an unseeded action space | [→](#2026-08-10--the-reference-toolkit-is-not-reproducible-as-published) |

---

## Results

### 2026-08-18 — `TorchTD3-v0` reproduces the Keras baseline on four Gymnasium environments
Final avg-20 reward, one seed per arm, laptop CPU (no CUDA), stock cfgs with the 11 shared keys
byte-identical between `torch_td3.cfg` and `keras_td3.cfg`. Toolkit commit `a085ad9`, branch
`develop-dw`.

| Env | Episodes | `TorchTD3-v0` | `KerasTD3-v0` | logdir under `results/` |
|---|---|---|---|---|
| `Pendulum-v1` | 100 | **−149.29** | −157.63 / −162.98 | `Pendulum/index010, index000, index001` |
| `Hopper-v5` | 300 | **180.12** | 168.29 | `Hopper/index010, index020` |
| `MountainCarContinuous-v0` | 100 | −1.05 | −1.01 | `MountainCarContinuous/index030, index031` |
| `FetchReachDense-Flat-v0` | 500 | −1.51 (best −1.07) | **−1.22** | `FetchReach/index040, index041` |

Two secondary numbers worth reporting: on `Pendulum-v1` the Keras arm crosses avg-20 = −200 at
episodes 47 and 48 while the torch arm does not until 57 — slower to take off, better at the end. On
`FetchReachDense-Flat-v0` the torch arm finished the same 500 episodes in **6 m 00 s against
10 m 13 s**, 40% faster in wall clock, while converging slightly worse.

**Caveats that must travel with these numbers.** One seed per arm. The Keras agent seeds from
`time.time_ns()`, so its arm is not reproducible even in principle; the torch agent takes a `seed`
cfg key and is. Three of the four environments never set `terminated`, so only `Hopper-v5` exercises
the `(1 - done)` factor in the Bellman target.

### 2026-08-12 — Keras TD3 baseline on `Pendulum-v1` (the number the port must match)
Reference arm for the torch-vs-Keras comparison. Stock `cfgs/keras_td3.cfg`, no tuning.

| | |
|---|---|
| avg-20 training reward, first crossing of −200 | **episode 47** |
| final avg-20 (episode 100) | **−163.0** |
| best single episode | −0.9 |
| wall clock | 4 min 34 s, CPU |
| per-step cost once training starts | ≈18 ms |

Scale: random policy ≈ −1200, do-nothing ≈ −1900, "solved" ≤ −200.
**Caveat that must travel with this number:** it is a *single* run, and the driver seeds from
`time.time_ns()` (see Failure modes), so it is not repeatable. The published comparison needs ≥3 runs
per arm with variance. Useful shape check: our standalone PyTorch demo crossed −200 at ≈ episode 38
with `warmup_size 1000`, versus 47 here with `warmup_size 2500` — the same curve offset by the extra
warm-up, which is what it should be.
Evidence: `SciOptControlToolkit` @ `48e624f`, Python 3.11.9 / TF 2.21.0 / numpy 2.4.6, HP Elite x360
G11 CPU (no CUDA). Logdir
`results/Pendulum/index001_env_Pendulum-v1_agent_KerasTD3-v0_hash_48e624f_time_20260812-150620`.
Command: `python -m jlab_opt_control.drivers.run_continuous --agent KerasTD3-v0 --env Pendulum-v1
--nepisodes 100 --nsteps 200 --logdir ./results/Pendulum --index 1`.

---

## Method choices

### 2026-08-19 — Mutation testing is what turns a passing suite into evidence
47 unit tests on the ported critic and agent passed on the first run, which is weak information — it
is equally consistent with tests that assert nothing sharp. Three defects were injected into
`agents/torch_td3.py`, one at a time, and the suite re-run:

| Injected defect | Tests that failed |
|---|---|
| `torch.minimum` → `torch.maximum` in the clipped double-Q target | 3 |
| `(1.0 - dones)` → `dones` in the Bellman target | 5 |
| tau swapped in `soft_update` (`mul_(tau).add_(sp, alpha=1-tau)`) | 1 |

The `(1 - dones)` case is the one that justifies the effort: three of the four environments used in
this round never terminate early, so an inverted done flag is invisible in every reward curve except
Hopper's. Reporting "N tests pass" says nothing; reporting which injected defects the suite catches
says what the suite is worth.

Note on the tau result: only one test catches the swap, and that is correct rather than thin. The
tau = 0.5 midpoint case is symmetric under the swap and *should* still pass; a dedicated
direction test at tau = 0.25 is what detects it. A suite needs an asymmetric case, not just a
midpoint case.

### 2026-08-17 — Weight initialization must be an explicit config key when comparing frameworks
Keras `Dense` initializes Glorot-uniform; PyTorch `Linear` initializes Kaiming-uniform. For a 256×256
hidden layer the bounds are `sqrt(6/512) = 0.1083` and `1/sqrt(256) = 0.0625` — a factor of 1.7. Left
at framework defaults, any "PyTorch vs TensorFlow" learning curve is partly an *initialization*
comparison, and the confound is invisible in the code because neither side names the initializer.
Exposed as a cfg key `weight_init`, set to Glorot to match the reference, and pinned by a test that
fails if the torch default returns. Generalizes: when porting across frameworks, every silent default
that differs is a confound until it is named in config.

### 2026-08-18 — Flattening `Dict` observation spaces at the registry, not in the driver
Goal-conditioned environments (all 217 gymnasium-robotics ids: Fetch, Maze, Hand, Kitchen) publish a
`Dict` observation space of `achieved_goal` / `desired_goal` / `observation` whose `.shape` is `None`.
`run_continuous.py:191` reads `env.observation_space.shape[0]`, so every one of them raises
`TypeError` before training starts. A `FlattenObservation` wrapper concatenates the sub-spaces into a
single `Box` and the existing agents consume them unchanged.

Two properties worth stating in a methods section. First, `FlattenObservation` concatenates in
**sorted key order**, so a Fetch observation is `achieved_goal(3) | desired_goal(3) |
observation(10)` = `Box(16)` — the agent's input layout depends on that ordering, so it is asserted
against the unwrapped env at a fixed seed rather than assumed. Second, flattening is necessary but
not sufficient: FetchPush, FetchSlide and FetchPickAndPlace still need Hindsight Experience Replay,
which the reference toolkit does not implement.

Applied as an additive registry factory rather than a driver patch, because the toolkit is upstream
code — see decisions.md, 2026-08-17.

### 2026-08-12 — Only the *agent* layer needs PyTorch, not the whole toolkit
Isaac Lab's `ManagerBasedRLEnv` returns `torch.Tensor` observations already resident on the CUDA
device (`[num_envs, obs_dim]`) and expects a CUDA tensor action back. A TensorFlow agent forces a
GPU→CPU→GPU copy per step, which negates the massively-parallel-env design that is Isaac Lab's
entire reason for existing; TF and Torch also contend for CUDA context and VRAM in a single process,
and Isaac Sim containers ship torch, not TF. The registry, config, and ABC layers of
`jlab_opt_control` are framework-agnostic and are reused unchanged.
**Second-order point worth stating in a Methods section:** the driver and replay buffer also need
rework, but for **vectorization**, not framework — `run_continuous.py` assumes a single env, a scalar
reward, and one gradient step per env step. Conflating "port to torch" with "support N parallel envs"
is the mistake to avoid. Detail: [`strategy.md`](strategy.md).

### 2026-08-12 — TD3 is the extension point the method contribution is expressed through
In `jlab_opt_control`, every research variant is a subclass of the TD3 agent that overrides
`train_critic` and changes almost nothing else: `KerasSINDyCriticTD3(KerasTD3)`,
`KerasUncertaintyTD3(KerasTD3)` (147 lines total), `KerasSINDyUncertaintyTD3` (94 lines, mostly
composition). So the SINDy-structured critic and the uncertainty-aware critic are not separate
algorithms — they are **modifications of the Bellman-target computation inside TD3**, which is the
cleanest possible framing for a Methods section: baseline TD3 and the variants differ in exactly one
function. The practical consequence for the port is that a clean overridable `train_critic` is the
design property that matters most, and it is why the port order is TD3 first.
Evidence: `SciOptControlToolkit` @ `48e624f`, `jlab_opt_control/agents/keras_sindy_critic_td3.py:54`,
`keras_uncertainty_td3.py:46`, `keras_sindy_uncertainty_td3.py`.

### 2026-08-10 — Store `terminated`, never `terminated or truncated`
The Bellman target's `(1 - done)` factor must zero the bootstrap only on genuine termination.
Zeroing it at a time limit teaches the critic that good states are worthless. The reference toolkit
gets this right. Worth stating explicitly because it is invisible in results — see Failure modes.

---

## Failure modes

### 2026-08-19 — Running the reference test suite writes training runs into the results tree
`pytest utests/` produced **11 real training-run directories** inside `results/`, at commit
`a085ad9`, timestamps 2026-08-18 23:32–23:56. `utests/test_baselines.py` and `utests/test_agents.py`
train actual agents, and the driver resolves its logdir relative to the working directory, so the
runs land wherever pytest was invoked. In a TensorBoard listing they are indistinguishable from
experiments — `index000_env_Pendulum-v1_agent_KerasTD3-v0_hash_...` looks exactly like a real result,
and two of the eleven were `KerasDDPG-v0` and `KerasSINDyCriticTD3-v0` runs nobody launched on
purpose. Anyone reporting numbers from a shared results tree can pick up a test artefact by mistake.
Deleted; new tests in this project use `tempfile.mkdtemp()` as logdir for exactly this reason.

Secondary: `pytest utests/` exceeds ten minutes as a whole, `test_baselines.py` alone taking over
three, so it is not usable as a pre-commit check in its current form.

### 2026-08-19 — A model loader that fails silently and reports a random policy's numbers
`TorchTD3.load()` — and the Keras agent it was ported from — wraps the whole load in a `try`/`except`
that logs an error and **continues with randomly initialized weights**. TD3 needs six files matched
by name prefix; if the path is wrong, or one file is missing, or a shape mismatches, training or
`--inference True` proceeds against an untrained network. The only signal is one `ERROR` line in a log
that also carries routine `ERROR:CfgLogger` noise from missing optional cfg keys, so it does not stand
out. Consequence for a results table: an inference number can be a random policy's number, with
nothing in the output to say so. Now covered by two negative tests (a five-of-six-file directory and a
missing directory) that assert the error is actually emitted — but the silent fallback itself is
upstream behaviour and unchanged.

### 2026-08-10 — A green `Pendulum-v1` smoke test does not validate termination handling
Pendulum's `terminated` is *always* `False` — every episode ends by truncation at 200 steps. So the
`terminated`-vs-`truncated` bug above cannot be detected on Pendulum at all. Any task with real
termination (the door task) is the first place it shows up, and it shows up only as "learning is
quietly worse." Implication for the paper's reproducibility section: state which envs exercise which
code paths.

### 2026-08-12 — Seeding the training env does not make *evaluation* reproducible
A distinct trap from the wall-clock-seeding one below, and easier to fall into because the training
side looks correct. In our own `learn/td3_pendulum_demo.py` — a file whose comments
explicitly criticise the reference toolkit's seeding — training was bit-reproducible under a fixed
seed while the reported evaluation return varied by **170 points** across four runs of the same seed
(−1621.4 / −1550.4 / −1525.9 / −1449.8, identical training returns of −1508.2 throughout). Cause: the
separate `eval_env` had its *action space* seeded but its *state* RNG left to OS entropy, because
`evaluate()` calls `reset()` with no seed.

Why it belongs in a paper's reproducibility section: **the evaluation number is the one that gets
published**, and it is the one an unseeded eval env silently randomises. On Pendulum, whose start
angle is uniform over the circle, a 3-episode greedy evaluation carries enough start-state variance to
swamp a real difference between two methods. Any A/B claim built on few-episode evaluations needs the
eval env seeded independently of the training env, or enough eval episodes to average the start-state
distribution out — and the paper should say which.

The same structural trap exists in the reference toolkit and is worse there:
`drivers/run_continuous.py:258` runs its inference episodes on the **same env object** used for
training, so evaluation consumes and advances the training env's RNG stream — evaluation and training
are not even statistically independent.
Evidence: `RL_DT@develop` `learn/td3_pendulum_demo.py:241`, `:266-268`; runs recorded in
[`rounds/Round-2026-08-12-torch-agent-in-toolkit.md`](rounds/Round-2026-08-12-torch-agent-in-toolkit.md);
`SciOptControlToolkit@48e624f` `jlab_opt_control/drivers/run_continuous.py:258`.

### 2026-08-12 — The reference replay buffer's sampling cost is linear in buffer occupancy
`jlab_opt_control/buffers/er.py`, `ER.sample()`, is
`np.random.choice(max_index, size=nsamples, replace=False)` where `max_index = min(pointer, capacity)`.
With `replace=False` and no probability vector, NumPy materialises a **full permutation of
`max_index`** to draw `nsamples` indices from. Measured (HP Elite x360 G11, CPU, numpy 2.4.6, Python
3.11.9; 256 indices, best-of-5 of 10 calls, via `uv run --with numpy`):

| rows in buffer | `replace=False` | `replace=True` |
|---|---|---|
| 5,000 | 82 µs | 10.4 µs |
| 50,000 | 810 µs | 10.1 µs |
| 100,000 | 1.64 ms | 10.2 µs |
| 1,000,000 | **16.2 ms** | 9.3 µs |

Linear in occupancy; the with-replacement path is flat. **Why it matters for the paper:** the cost is
driven by how *full* the buffer is, not by the configured capacity, so it is invisible on the
standard `Pendulum-v1` smoke test (a few thousand rows → ~80 µs, negligible beside the gradient step)
and becomes the dominant per-step cost once the buffer fills — at 1M rows, index selection costs more
than the gradient step it feeds. Any sample-efficiency-vs-wall-clock comparison involving this buffer
must state the buffer occupancy, or the wall-clock axis is measuring the sampler rather than the
algorithm. The fix is `replace=True` (what every reference TD3 implementation does); the only
semantic loss is the guarantee that a batch holds no duplicate transition, which at batch 256 out of
≥2500 rows is statistically irrelevant.
Evidence: `SciOptControlToolkit` @ `48e624f`, `jlab_opt_control/buffers/er.py:69`, `cfgs/er.cfg`
(`buffer_capacity: 1000000`). Not fixed as of this entry — deferred, see
[`strategy.md`](strategy.md) Part 3.

### 2026-08-12 — A "best model" criterion that can only ever say yes
Observed on the first real run through the reference driver: all 10 inference checkpoints were saved
as improvements, including one whose evaluation return was 98 points *worse* than an earlier one. Two
independent defects in `drivers/run_continuous.py` combine:

1. **Averaging window vs. sampling interval.** `:264` takes
   `np.mean(inference_reward_list[-nepisode_avg:])` with `nepisode_avg = 20`, but the list is appended
   only every `inference_interval = 10` episodes. In a 100-episode run the list has 10 entries, so the
   "recent average" spans the whole run including the random-policy start. It therefore rises
   monotonically by dilution — −845 → −743 → −678 → −603 → −565 over episodes 50–90 — while the
   underlying evaluations bounced −117 / −129 / −223 / −4 / −227.
2. **A relative improvement threshold applied to a negative quantity.** `:266` is
   `avg > best * (1 + threshold)`. For `best < 0` this *lowers* the bar by `threshold`, so the 5 %
   margin intended to demand real improvement instead admits results up to 5 % worse. It behaves as
   designed only for positive-reward tasks — and both Pendulum and accelerator tuning-error rewards
   are negative.

**Why it belongs in a paper's reproducibility section:** this is the class of bug that makes reported
numbers *better* than the method deserves, because "best checkpoint" evaluation silently degenerates
into "last checkpoint," and any relative-improvement gate on a negative objective inverts. It is
worth stating as a general rule: **relative thresholds must be written sign-safe**
(`best + t*abs(best)`), and any "average of the last N" must be in the same units as the thing being
counted. Neither error is visible in a training curve; both are visible only by counting how many
checkpoints were accepted.
Evidence: `SciOptControlToolkit` @ `48e624f`, `jlab_opt_control/drivers/run_continuous.py:264`, `:266`,
`:281`, `:385`, `:387`, `:391`; run logdir
`results/Pendulum/index001_env_Pendulum-v1_agent_KerasTD3-v0_hash_48e624f_time_20260812-150620`
(`models/epoch_00000_000` … `epoch_00090_006`, 10 acceptances out of 10 opportunities). Not fixed —
shared driver code, raised as Q9.

### 2026-08-10 — The reference toolkit is not reproducible as published
`run_continuous.py` seeds from `time.time_ns()`, and `keras_td3.initialize_new_models()` re-seeds
from wall-clock again between critic constructions. The action space is never seeded, so the warm-up
(thousands of random transitions) varies run to run even if everything else is fixed. Any comparison
against it needs multiple seeds and reported variance, not single runs.

---

## Comparisons

### 2026-08-18 — Mixed-direction results are the correct evidence for a faithful port
Across four environments `TorchTD3-v0` is ahead on two (`Pendulum-v1`, `Hopper-v5`), behind on one
(`FetchReachDense-Flat-v0`) and tied on one (`MountainCarContinuous-v0`). Numbers in **Results,
2026-08-18**.

That pattern is the claim, not a weakness in it. A port that swept all four would more likely indicate
a changed hyperparameter or a different effective exploration rate than a better implementation — the
two agents share 11 byte-identical cfg keys precisely so that neither should dominate.

The strongest single piece of evidence is the **tie on the failure case**. On
`MountainCarContinuous-v0` both agents drop from roughly −33 to −1.0 by episode 3 and reach the goal in
**0 of 100 episodes**, converging on "spend no energy". This is TD3's canonical hard-exploration
failure: Gaussian noise at 10% of the action range never carries the car to the flag. Reproducing a
known failure mode identically, without having aimed at it, is harder to achieve by accident than
matching a success.

Remaining weakness, stated for a reviewer: one seed per arm, and the Keras arm cannot be re-seeded
because that agent seeds from wall clock. ≥3 seeds per arm is still outstanding.

---

## Figures

*(none yet)*

---

## Related work

*(none yet — start with the SINDy / physics-informed-critic papers behind
`keras_sindy_critic_td3.py`, and the uncertainty-aware TD3 variants)*

---

*Buckets, for filing: **Results** = measured numbers with conditions attached · **Method choices** = a
design decision plus the reason · **Failure modes** = things that silently degrade learning ·
**Comparisons** = baseline vs variant, with caveats · **Figures** = what plot from which logdir ·
**Related work** = papers read, and how they differ from what we do. A one-line stub with a date beats
nothing, and every entry adds a row to the index above.*
