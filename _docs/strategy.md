# Strategy — how much of SciOptControlToolkit becomes PyTorch, and how it meets Isaac Lab

> Written 2026-08-12 as a proposal, opening
> [Round-2026-08-12](rounds/Round-2026-08-12-torch-agent-in-toolkit.md). **Re-cast 2026-08-19 as a
> status note:** the scope in Part 2 has been executed, so each tier now records what closed it and
> with what evidence. Part 4's architecture choice is **still open** and is the top item in
> [`team-discussion.md`](team-discussion.md).
>
> **Purpose:** settle the scoping question ("does the whole toolkit need re-drafting in PyTorch?") with
> evidence, and lay out the three candidate architectures for the Isaac Lab track so they are discussed
> rather than decided unilaterally.
>
> Code citations are to `<PROJECT_ROOT>/SciOptControlToolkit`, branch `develop-dw`, at commit
> **`48e624f`** when the note was written. Line numbers rot; file and symbol names do not. Every
> measured number and every defect referenced here lives in
> [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md), not here.

---

## The question, and the answer in one line

**No.** Exactly one layer of the toolkit is framework-bound in a way that matters — the agent and its
networks. Everything else is either framework-agnostic already, or needs work for a reason that has
nothing to do with TensorFlow vs PyTorch.

Conflating those two reasons is the mistake this note exists to prevent.

---

## Part 1 — Why the agent layer has to be PyTorch

Not an aesthetic preference. Three concrete reasons, in descending order of how hard they are to work
around.

**1. Isaac Lab's data never leaves the GPU, and TF cannot receive it there.**
`ManagerBasedRLEnv.step()` returns `torch.Tensor` observations of shape `[num_envs, obs_dim]` already
resident on the CUDA device, and expects a CUDA tensor action back. A TensorFlow agent in that loop
forces, **every environment step**:

```
GPU (torch obs) → CPU (numpy) → GPU (tf tensor) → [network] → CPU (numpy) → GPU (torch action)
```

Four device transfers where the correct number is zero. Isaac Lab's whole design premise is that
stepping 256–4096 environments is cheap *because nothing synchronises with the host*. This is not a
constant-factor slowdown you can accept: the transfers serialise against the physics kernels, so the
parallelism itself stops paying.

**2. Two frameworks in one process contend for the same GPU.** TF and Torch each create a CUDA context
and each have their own allocator; TF reserves nearly all VRAM at first use. Isaac Sim is also in that
process and is itself VRAM-hungry. Three allocators, one 5080. Solvable with
`TF_FORCE_GPU_ALLOW_GROWTH` and careful ordering, but a permanent source of environment-specific
failure for no gain.

**3. The container ships torch, not TF.** Isaac Sim's official containers pin a PyTorch build matched
to the CUDA version; TF is absent, and making a TF wheel agree with CUDA 12.8+ / Blackwell is an
install problem we would own forever. `requirements.txt:9` already declares `torch>=2.10` and nothing
imports it, so **the port added no new dependency** — it started using one already sanctioned.

**Consequence:** the port is bounded by "what touches a neural network," not by "what is in the repo."

---

## Part 2 — The three-tier scope, and what closed each tier

### Tier 1 — PORT · **done**

Closed by commits `ee4ced6`, `61646af`, `5c928ff` on `develop-dw` (plus `a085ad9` for the env adapter),
**1,376 insertions and zero deletions**, and 82 passing tests of which the 47 on the critic and agent
were mutation-tested. → [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md).

| Keras file | Why it was framework-bound | Size | Ported to |
|---|---|---|---|
| `agents/keras_td3.py` | `tf.GradientTape`, `@tf.function`, Keras `Adam`, `get_weights`/`set_weights` surgery in `soft_update` | 429 lines, ~250 substantive | `agents/torch_td3.py` → `TorchTD3-v0` |
| `models/actor_fcnn.py` | `layers.Dense`, `tf.constant` for `action_scale`/`action_bias`, Keras `call()` | 72 | `models/torch_models.py` → `ActorFCNNTorch` |
| `models/critic_fcnn.py` | same | 68 | same file → `CriticFCNNTorch` |
| `core/model_core.py` | **`class Model(tf.keras.Model)`** — the model base class *is* a Keras model | 18 | `core/torch_model_core.py` |

**~410 lines, of which maybe 250 were real logic** — the estimate held. `core/model_core.py` was the
surprise: unlike `core/agent_core.py` (a pure ABC with no imports), the *model* base class inherits
from `tf.keras.Model`, so the torch networks cannot share a base class with the Keras ones. They
subclass `torch.nn.Module` and satisfy the same duck-typed surface — `save_cfg()`, `action_scale`,
`action_bias` — which is all the agent uses.

**One coupling still open.** `agents/__init__.py:30–36` imports all seven Keras agents at module import
time and `drivers/run_continuous.py:39` imports `tensorflow` at module level, so **TensorFlow must be
installed for the torch agent to run at all.** Fine on a workstation, fatal in an Isaac container.
Fixing it means guarded/lazy imports in shared kit code — a conversation, not a unilateral edit, and it
gates Isaac regardless of which architecture is chosen. Not in Part 3 of
[`team-discussion.md`](team-discussion.md) only because no patch is drafted yet.

### Tier 2 — REUSE UNCHANGED · **held**

Reused exactly as written; nothing in this tier was edited.

| File | What it does | Why it is framework-blind |
|---|---|---|
| `agents/`, `models/`, `buffers/registration.py` | string-ID → class registry, mirroring `gym.make` | pure `importlib`; never imports a framework |
| `core/agent_core.py` | the `Agent` ABC | 38 lines, abstract methods only, no imports |
| `utils/cfg_utils.py` | `cfg_get(dict, key, default)` | 13 lines of dict access |
| `utils/git_utils.py` | git SHA for the logdir name | subprocess |
| `cfgs/*.cfg` | JSON hyperparameters | data |

Worth reusing on its own merits, not just to save effort: the registry + JSON-cfg convention is the one
pattern `CLAUDE.md` committed to keeping, and it is what makes `--agent TorchTD3-v0` swap cleanly
against `--agent KerasTD3-v0` in one command line. Reimplementing it would have *removed* the ability
to A/B the two agents — which is exactly how the four-environment comparison was produced.

**The caveat that turned out to matter most.** `core/agent_core.py` declares only
`soft_update / train / action / load / save / save_cfg`. But `drivers/run_continuous.py` also calls
`agent.memory(...)` (`:347`) and `agent.buffer.save(...)` (`:279`, `:299`), and `utests/test_agents.py`
reaches into `agent.warmup_size`, `agent.batch_size`, `agent.buffer.size()`, `.pointer`, `.states`.
**The real interface is wider than the declared one** — satisfying the ABC is necessary but not
sufficient. The port derived its contract from the driver and the tests instead, and 82 tests now pin
it.

### Tier 3 — DEFER, for vectorization not framework · **still deferred**

`drivers/run_continuous.py` and `buffers/er.py` both need rework before Isaac. **Neither needs it
because of TensorFlow.** Detail in Part 3. The obligation was to not design anything that blocks it,
and that obligation was met (see § What this round must not do, below).

---

## Part 3 — What "vectorization, not framework" means concretely

The part worth being precise about, because "the driver needs porting too" is the plausible-sounding
wrong conclusion.

### The driver assumes exactly one environment

`run_episode` (`run_continuous.py:301`) hard-codes single-env shapes in its own assertions: a NumPy
array of shape `(num_states,)` (`:326`), a scalar Python float reward (`:341`), and a `while not done`
loop driven by one boolean. Under Isaac Lab every one is wrong in the same way — the leading `num_envs`
axis is missing. `state` is `[N, obs_dim]`, `reward` is `[N]`, `done` is `[N]`, and episodes end at
different times in different environments, so the loop cannot be `while not done` at all.

And the learning cadence:

```python
if train:
    agent.memory((state, action, reward, next_state, terminate))   # :347  one transition
    agent.train()                                                  # :348  one gradient step
```

One transition stored and one gradient step per env step. With `num_envs=256` a single `step()` yields
**256 transitions**; doing 256 separate `memory()` calls plus 256 gradient steps is both wrong (the
standard is a tunable updates-to-data ratio, not 1:1) and pathologically slow. Sorting that out is a
decision about *update ratio and batching* — a reinforcement-learning question. Rewriting those three
assertions in torch instead of numpy would change nothing about it.

### The replay buffer: NumPy is fine, but this NumPy is not

`buffers/er.py` stores plain `np.zeros((capacity, dim))`. A NumPy buffer works perfectly well with a
torch agent — you convert a `batch_size × dim` slice per gradient step, a trivial copy. So **"the
buffer is NumPy" is not itself a reason to touch it.** Two things are:

1. **Insertion is scalar.** `record()` (`:50`) writes one row per call. Isaac hands back `N` rows at
   once, already on the GPU; pulling them to host to store in NumPy reintroduces exactly the transfer
   Part 1 was about. A device-resident tensor buffer with batched inserts is what Isaac wants.
2. **Sampling is O(buffer fill level), not O(batch size)** — `sample()` (`:69`) uses
   `np.random.choice(max_index, size=nsamples, replace=False)`, which materialises a full permutation
   of `max_index`. Measured, linear in occupancy, and invisible on a `Pendulum-v1` smoke test precisely
   because the cost tracks how *full* the buffer is rather than its configured capacity. The table, the
   conditions and the one-line fix are in
   [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md) § Failure modes.

Both are shape-and-device problems. Neither is a TensorFlow problem. Neither was fixed — this is
someone else's repo, and the torch agent inherits whatever the buffer does. Raised as a proposal in
[`team-discussion.md`](team-discussion.md) Part 3.

### What this round must not do — and did not

Nothing in `TorchTD3` may assume a leading batch axis of exactly 1: `action()` takes `[obs_dim]` today
but is written so `[N, obs_dim]` is a one-line change, and `train()` does not tie "one call" to "one
transition arrived." That was the whole forward-compatibility obligation, and it is satisfied.
Everything else stays deferred.

---

## Part 4 — The three candidate architectures · **open**

The real question behind the port is what role this toolkit plays on the Isaac Lab track, given that
[`decisions.md`](decisions.md) (2026-08-03) already commits to **rl_games PPO** there. Three coherent
answers.

**A — the toolkit replaces rl_games.** `jlab_opt_control` becomes the training stack for the door task:
`TorchTD3` consumes `ManagerBasedRLEnv` directly, the driver is rewritten for vectorized envs, the
buffer becomes a device-resident tensor ring, PPO is eventually added.
*For:* one stack for everything, so a research result is immediately a result on the real task.
*Against:* we would rebuild, unfunded, what rl_games already does well — vectorized rollout, mixed
precision, running observation statistics, multi-GPU, checkpoint/resume, LR scheduling, and the
thousand numerical details that decide whether PPO trains. It also reverses a recent decision and puts
the toolkit on the door task's critical path. *Cost:* weeks, ongoing.

**B — rl_games is the baseline; the toolkit carries the research contribution.** rl_games PPO trains
the door task and produces the baseline numbers unchanged. `jlab_opt_control` with `TorchTD3` is the
vehicle for the *method* contribution — the SINDy-structured and uncertainty-aware critics — validated
on Gymnasium first, then run on the door task as the comparison arm.
*For:* it matches what the code already says the research *is* (see Part 5). It preserves the rl_games
decision, keeps the toolkit off the critical path, and gives the clean two-arm comparison reviewers
want. *Against:* two stacks and two sets of results to keep honest; an off-policy-vs-on-policy
comparison needs its units stated and its caveat repeated every time. *Cost:* moderate — this round
plus vectorization later, and no rewriting of things that work.

**C — the toolkit stays a low-parallelism research bed.** Never pointed at Isaac Lab. It stays where it
is strong: single- or few-env problems where sample efficiency matters and throughput does not. The
door task is a separate rl_games effort that borrows *findings*, not code.
*For:* cheapest by a wide margin, and honest about the toolkit's design centre — the vectorization work
in Part 3 never happens. *Against:* the method contribution is then never demonstrated on the robot
task, which is the project's actual subject. "Does the SINDy critic help on the door?" — "we don't
know." *Cost:* small.

| | A — replaces rl_games | B — baseline + research arm | C — separate research bed |
|---|---|---|---|
| rl_games decision | reversed | preserved | preserved |
| Vectorization work needed | full | eventually, for the comparison arm | never |
| Method result shown on the door task | yes | yes | **no** |
| Toolkit on the door task's critical path | yes | no | no |
| Duplicate stacks to maintain | no | yes | yes |
| Effort | weeks+, ongoing | moderate | small |
| Main risk | we rebuild rl_games badly | comparison framing | contribution never lands on the real task |

---

## Part 5 — Recommendation: B

Three reasons, in order of weight.

1. **The code already votes for it.** Every research variant subclasses the TD3 agent and overrides
   `train_critic`, changing almost nothing else — TD3 is not one algorithm among several here, it is
   the base class the contribution is expressed as an override of. B is the architecture that pattern
   implies. A treats the toolkit as infrastructure it was not built to be; C declines to use the
   extension point on the task the project is about. Evidence and file citations:
   [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md) § Method choices.

2. **It is the only option that produces the paper's central figure.** The claim "a physics-informed /
   uncertainty-aware critic helps on a contact-rich lab-automation task" requires running the method on
   that task next to a credible baseline. C cannot produce it; A produces it against a baseline we
   built ourselves, which is much weaker evidence than one everyone already trusts.

3. **It fails cheaply.** B's expensive part — vectorized rollout plus device-resident buffer — is
   *deferred and optional*. If the method shows nothing on Gymnasium we stop before paying for it, and
   the door task is unaffected because rl_games was never displaced. A commits the spend up front.

**What B commits us to, in priority order:**

- `TorchTD3` with `train_critic` as a small, clearly-documented, overridable method — the seam the
  variants hang off. **Delivered:** it is the property the port was designed around.
- Agent code with no leading-batch-axis-of-1 assumption (Part 3). **Delivered.**
- Reporting the TD3-vs-PPO comparison in sample-efficiency terms with the on-/off-policy caveat
  attached every time, not in wall-clock alone. **Outstanding.**
- Accepting two stacks, and therefore two seeding and logging conventions that must both be
  reproducible. **Outstanding** — the torch side is reproducible via the `seed` cfg key; the Keras side
  cannot be, and the rl_games side pins `seed: 42`.

**What would change the recommendation:** if rl_games cannot handle the door task's force/torque
observations or termination structure without modification, A gets stronger — at that point we are
modifying a training stack either way, and modifying our own is preferable to patching someone else's.
Worth checking early, and it is now checkable: the task's `TerminationsCfg` and the absence of any
force/torque term are read out in [`learn/3-isaac-and-rl-games.md`](learn/3-isaac-and-rl-games.md).
Conversely, if the SINDy critic needs system identification on *single* long trajectories rather than
batched short ones, C gets stronger.

---

## Part 6 — What this note does not decide

Carried into [`team-discussion.md`](team-discussion.md):

- **The A/B/C choice itself** — still a recommendation to discuss, not a decision taken. It is question
  B1 there.
- **What the ported TD3 is ultimately for** — the same question from the other side (B2).
- Whether `memory` and `buffer` belong in the `Agent` ABC (Part 2 caveat) — moot in practice now, since
  82 tests pin the real interface.
- Whether the toolkit's `setup.py` (`packages=['jlab_opt_control']`, subpackages unlisted) is meant to
  be installed non-editable.

**Settled since:** `env.yaml`'s `python=3.13` is not a hard floor — the whole dependency set resolves
on 3.11.9 ([`environment.md`](environment.md)). Shared vs separate critic optimizers, deterministic
seeding, and `torch.utils.tensorboard.SummaryWriter` over `tf.summary` were all decided during the
port and are recorded in [`decisions.md`](decisions.md).

---

## See also

- [`rounds/Round-2026-08-12-torch-agent-in-toolkit.md`](rounds/Round-2026-08-12-torch-agent-in-toolkit.md)
  and [`rounds/Round-2026-08-17-torch-td3.md`](rounds/Round-2026-08-17-torch-td3.md) — the work itself
- [`decisions.md`](decisions.md) — the rl_games commitment this note reasons against
- [`learn/1-rl-and-td3.md`](learn/1-rl-and-td3.md) — the idiom-level translation notes for Tier 1
- [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md) — the Methods-section version of Parts 1 and 3
