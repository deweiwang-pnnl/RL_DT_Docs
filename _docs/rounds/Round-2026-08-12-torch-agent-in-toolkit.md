# Round-2026-08-12 — PyTorch TD3 agent inside SciOptControlToolkit

**Goal:** add a PyTorch TD3 agent to `jlab_opt_control/agents/` alongside the Keras agents, wired to
run through the existing driver.
**Done =** `python -m jlab_opt_control.drivers.run_continuous --agent TorchTD3-v0 --env Pendulum-v1`
trains and reaches roughly the same reward as `--agent KerasTD3-v0` under the same cfg values.
**Real purpose:** understand this toolkit well enough to apply it to the Isaac Lab digital twin task.
Understanding over speed.

**Status:** in progress

> *Path note, added 2026-08-19.* History, left as written. Two files this round created were renamed in
> the reorganization and the links below follow them: `strategy-torch-and-isaac.md` →
> [`../strategy.md`](../strategy.md), and `questions-for-malachi.md` →
> [`../team-discussion.md`](../team-discussion.md).

## Where the work happens

| Repo | Branch | Contents |
|---|---|---|
| `<PROJECT_ROOT>/SciOptControlToolkit` | `develop-dw` | **toolkit code goes here** (clone of JeffersonLab/SciOptControlToolkit, HEAD `48e624f`) |
| `<PROJECT_ROOT>/RL_DT` | `develop` | **notes and logs go here** |

No notes in the toolkit repo, no toolkit code in RL_DT. Never `git push` in either — commit only,
Dewei handles auth.

## Plan

- [x] Read the toolkit end to end; derive the real interface contract from the driver and tests
- [x] Confirm the environment (GPU? Python? what is installed?)
- [x] Write [`../strategy.md`](../strategy.md) — scope reasoning +
      the three candidate architectures, with a recommendation
- [x] Start [`../team-discussion.md`](../team-discussion.md)
- [x] Install the environment — `.venv` in the toolkit repo, Python 3.11.9, everything resolves
- [ ] `models/actor_fcnn_torch.py` + `models/critic_fcnn_torch.py` + registration
- [ ] `cfgs/torch_td3.cfg`
- [ ] `agents/torch_td3.py` + registration as `TorchTD3-v0`
- [ ] Tests in `utests/test_agents.py` following `AgentTestMixin`
- [ ] Verify the driver's `tf.convert_to_tensor(state)` coercion actually works in the torch agent
- [ ] Smoke run on `Pendulum-v1`; compare against `KerasTD3-v0`, ≥3 seeds

## Log

### 2026-08-12

**Environment confirmed — this is the laptop, not the workstation.**

| Check | Result |
|---|---|
| Machine | `WF10878`, HP Elite x360 1040 14" G11 |
| GPU | Intel Arc integrated only; `nvidia-smi` not found → **no CUDA** |
| Python | 3.11.9 and 3.14.5 available; targeting **3.11** |
| Packages in 3.11 | `pip`, `setuptools`, `pywin32` — **nothing else installed yet** |
| `uv` | 0.12.0 |

Consequence: the torch agent must run CPU-only here, so `device` is a variable from the start and
nothing may assume CUDA. Not a blocker at Pendulum scale.

**Correction needed in [`../environment.md`](../environment.md):** its "Known machines" table maps
this OneDrive path to "Dewei, PNNL workstation / RTX 5080". The OneDrive path is *synced*, so it
exists on both machines and does not identify one. To fix in a later turn — not folded into this
component.

**Toolkit read.** Files read in full: `agents/keras_td3.py`, `agents/__init__.py`,
`agents/registration.py`, `drivers/run_continuous.py`, `models/actor_fcnn.py`,
`models/critic_fcnn.py`, `core/agent_core.py`, `utils/cfg_utils.py`, `buffers/er.py`,
`utests/test_agents.py`, `requirements.txt`, `setup.py`, `env.yaml`, and all relevant `cfgs/*.cfg`.
Skimmed the SINDy/uncertainty variants and `models/sindy_network.py`.

**The single most useful thing I found.** Every research variant is a subclass of `KerasTD3` that
overrides `train_critic` and little else — `KerasSINDyCriticTD3`, `KerasUncertaintyTD3`,
`KerasSINDyUncertaintyTD3` (the last is 94 lines, mostly composition). TD3 is not one algorithm among
several in this toolkit; it is **the base class the research contribution is expressed as a delta
from.** So the most important design property of this round's code is a clean, overridable
`train_critic`. This also explains why the assignment says "TD3 first."

**`torch` is already a declared dependency and completely unused.** `requirements.txt:9` and
`env.yaml` both list `torch>=2.10`; `grep -rn "import torch"` over the whole package returns nothing.
Adding a torch agent introduces no new dependency.

**Strategy note written** — [`../strategy.md`](../strategy.md).
Three-tier scope (PORT ~390 lines / REUSE / DEFER), the "vectorization not framework" argument for
the driver and buffer, and architectures A/B/C with **B recommended**.

**Measured while writing it — the ER buffer's sampling is O(fill level).** `er.py:69` is
`np.random.choice(max_index, size=nsamples, replace=False)`, which makes NumPy build a full
permutation of `max_index`. Numbers on this laptop, numpy 2.4.6, 256 indices, best-of-5:

| rows in buffer | `replace=False` | `replace=True` |
|---|---|---|
| 5,000 | 82 µs | 10.4 µs |
| 50,000 | 810 µs | 10.1 µs |
| 100,000 | 1.64 ms | 10.2 µs |
| 1,000,000 | **16.2 ms** | 9.3 µs |

Linear in fill level; `replace=True` flat. Cost is driven by how full the buffer is, not by `er.cfg`'s
configured capacity of 1,000,000 — which is why it hides on Pendulum (a few thousand rows, ~80 µs)
and bites at scale (sampling then costs more than the gradient step it feeds). Tier 3, not fixing it
this round; raised as a question and logged as a failure mode.

**Interface contract, verified against the source rather than assumed.** The declared ABC is narrower
than the real contract:

- `core/agent_core.py` declares abstract: `soft_update`, `train`, `action`, `load`, `save`,
  `save_cfg`. **Note `memory` and `buffer` are *not* in the ABC.**
- but `run_continuous.py` also calls `agent.memory(...)` (`:347`), `agent.train()` (`:348`),
  `agent.save_cfg()` (`:236`), `agent.save("init")` (`:237`), `agent.save(str)` (`:270`, `:277`,
  `:297`), and `agent.buffer.save(f'{logdir}/buffers/buffer.npy')` (`:279`, `:299`)
- and `utests/test_agents.py` reads `agent.warmup_size`, `agent.batch_size`, `agent.buffer.size()`,
  `agent.buffer.pointer`, `agent.buffer.states`
- `action()` must return a 2-tuple; the driver asserts the action is an `np.ndarray` of shape
  `(num_actions,)` (`:331–332`)
- the driver calls `agent.action(tf.convert_to_tensor(state), train=train)` (`:328`) — **a TF
  EagerTensor reaches the torch agent.** To be coerced inside the agent with `np.asarray(state)`;
  *unverified until torch and TF are both installed* — on the to-do list, not assumed.

Hyperparameters found **hardcoded in the Keras agent** and therefore needed in `torch_td3.cfg`
(neither is in `keras_td3.cfg`): target-policy-smoothing noise std `0.2` (`keras_td3.py:218`) and
`self.noise_clip = 0.5` (`:148`). Also `actor_update_freq` / `critic_update_freq` are read from cfg
but absent from `keras_td3.cfg`, so both silently fall back to the default `2` via `cfg_get`.

Note the exact order of operations in the reference's target noise (`:218–222`) — clip **then** scale:

```python
noise         = tf.random.normal(tf.shape(actions)) * 0.2
noise_clipped = tf.clip_by_value(noise, -0.5, 0.5) * self.target_actor.action_scale
next_actions  = tf.clip_by_value(target_actor(next_states) + noise_clipped, lower, upper)
```

For Pendulum (`action_scale = 2.0`) that yields σ = 0.4 and a clip of ±1.0 in action units, which
matches standard TD3's `policy_noise=0.2·max_action`, `noise_clip=0.5·max_action`. So the reference
agrees with the literature for symmetric action spaces — worth reproducing rather than "fixing."

**Ran `_docs/learn/td3_pendulum_demo.py` for the first time.** Dewei asked for something runnable
to play with. The demo was written in Round-08-10 but — given the env was bare then and WORKLOG says
"no production code written" — appears never to have been executed. It runs, and it solves Pendulum.

Environment: ephemeral `uv run --python 3.11 --with torch --with gymnasium --with numpy`, so nothing
was installed into a project env. torch 2.13.0+cpu, gymnasium 1.3.0, CPU, seed 0, 60 episodes,
~5 min wall clock.

| ep | return | avg10 | EVAL |
|---|---|---|---|
| 1 | −1071.9 | −1071.9 | |
| 10 | −1549.1 | −1379.5 | −1557.0 |
| 20 | −1516.7 | −1373.8 | −1196.2 |
| 25 | −1522.2 | −1195.4 | −799.8 |
| 30 | −519.9 | −874.7 | −597.7 |
| 35 | −127.7 | −447.2 | **−125.8** |
| 60 | −252.0 | −138.6 | −161.6 |

`final avg10=-138.6  best_eval=-125.1  SOLVED`. Comfortably past the −200 bar.

**Two defects found in the demo / its notes, neither of which affects the toolkit port:**

1. **`eval_env`'s state RNG is never seeded, so `EVAL` is not reproducible.**
   `td3_pendulum_demo.py:266–268` creates `eval_env` and seeds `eval_env.action_space` — but
   `action_space.sample()` is never used during evaluation, and `evaluate()` calls `env.reset()` with
   no seed (`:241`), so the start states come from OS entropy. Confirmed by running `--seed 0
   --episodes 2` three times:

   | run | return | avg10 | EVAL |
   |---|---|---|---|
   | 1 | −1508.2 | −1290.0 | −1621.4 |
   | 2 | −1508.2 | −1290.0 | −1550.4 |
   | 3 | −1508.2 | −1290.0 | −1449.8 |

   Training bit-identical, `EVAL` different every time (a fourth run gave −1525.9). The file's own
   comment at `:259–261` criticises the reference toolkit for exactly this class of bug, and
   `td3_pendulum_notes.md` instructs the reader to *judge by EVAL* — the one number that does not
   reproduce. One-line fix: `eval_env.reset(seed=args.seed + 10_000)` once at construction.
   **Directly relevant to the port:** the same trap exists in `run_continuous.py`, which runs
   inference episodes on the *same* env object as training (`:258`) and never seeds it at all.

2. **`td3_pendulum_notes.md`'s diagnostic threshold gives a false alarm.** It says *"If it is still
   ≈ −1200 by episode 30, something is wrong."* This run was at avg10 −1195 at episode 25 and −875 at
   episode 30 — i.e. it would have tripped that check — and then solved cleanly by episode 35. The
   notes' "What you should see" table (breakthrough by ep 15–20) is roughly 15 episodes optimistic
   against measurement; the table was illustrative, not measured. The *shape* it describes is right;
   the episode numbers and the abort threshold are not. Worth correcting so nobody debugs a working
   implementation.

**Two hard couplings found — a torch-only install of this kit is impossible today.**

1. **`agents/__init__.py` imports all seven Keras agents at module import time** (`:30–36`). Any
   `agents.make(...)`, including `make('TorchTD3-v0')`, requires `import jlab_opt_control.agents`,
   which imports TensorFlow. `drivers/run_continuous.py` also imports `tensorflow` at module level
   (`:39`). So **TF must be installed to run the torch agent**, even though the torch agent will not
   use it. Fixable with lazy/guarded imports in `agents/__init__.py`; that is a change to shared kit
   code, so it needs Malachi's agreement rather than my initiative. Matters for Isaac: a torch-only
   container cannot import this package as written.

2. **`core/model_core.py` is NOT framework-agnostic** — it is `class Model(tf.keras.Model)`. My
   strategy note put `core/agent_core.py` in the reuse tier, which is right (it has no imports at
   all), but `model_core.py` belongs in the *port* tier and I had not listed it. The torch actor and
   critic therefore **cannot subclass the kit's `Model`**; they subclass `torch.nn.Module` and satisfy
   the same duck-typed surface (`save_cfg`, `action_scale`, `action_bias`). No shared base class
   between the Keras and torch model families. Correction applied to
   [`../strategy.md`](../strategy.md).

**What environments the kit actually ships.** Only `Circle2D`, registered twice
(`envs/__init__.py`): `DnC2s-Circle2D-Statefull-v0` and `-Stateless-v0`, both with
`max_episode_steps=1`. A **one-step** problem — reward is a function of the action, there is no
sequential credit assignment, and with γ irrelevant the Bellman target reduces to the immediate
reward. That is a *black-box optimization* benchmark, not a control task, and it tells you plainly
what the kit was built for: accelerator tuning, not multi-step manipulation. Relevant to the A/B/C
discussion. Everything else the driver can run comes from Gymnasium via `gym.make` (default
`Pendulum-v1`) or the optional, not-installed PACEs package.

Also `Circle2D` does not meet the current Gymnasium API: `reset(self)` (`circle_env.py:85`) takes no
`seed`/`options` kwargs, so `env.reset(seed=...)` raises `TypeError` — which is *why* nothing in the
kit seeds its envs. It also returns `''` instead of `{}` for `info`, and sets `terminated=True` **and**
`truncated=True` together at the step limit (`:81`), where a time limit should set `truncated` only.
Harmless in a one-step env; exactly the confusion that makes the termination bug invisible.

**The toolkit environment is installed and the kit runs.** `.venv` inside `SciOptControlToolkit`
(gitignored already), created with `uv venv --python 3.11`, then `uv pip install -r requirements.txt`
and `uv pip install -e .`. Everything in `requirements.txt` resolved on **Python 3.11.9** with no
pins loosened — `tensorflow 2.21.0`, `tf-keras 2.21.0`, `tensorflow-probability 0.25.0`,
`torch 2.13.0+cpu`, `gymnasium 1.3.0`, `numpy 2.4.6`, `pandas 3.0.5`. Both frameworks coexist in one
env with no conflict, and both correctly report no GPU.

**This partly answers Q6** (`env.yaml` pins `python=3.13`): 3.13 is **not** a hard floor — the whole
declared dependency set installs and imports on 3.11. Still open is whether `pip install .`
(non-editable) works, given `setup.py` lists only the top-level package; I used `-e`, which sidesteps
it.

**First toolkit run — `KerasTD3-v0` on `Pendulum-v1`, 15 episodes, 25 s wall clock.** Exit 0. Writes
`results/Pendulum/index000_env_Pendulum-v1_agent_KerasTD3-v0_hash_48e624f_time_20260812-150525/`
containing `buffers/ models/ cfgs/ metrics/ results.npy` — the git hash and timestamp are in the
directory name, which is the part of this toolkit's design worth keeping.

The most instructive thing in the log is the **warm-up gate becoming visible in the wall clock**:

| episode | total steps | episode elapsed |
|---|---|---|
| 9 | 2000 | 0.16 s |
| 11 | 2400 | 0.11 s |
| **12** | **2600** | **4.11 s** |
| 13 | 2800 | 3.67 s |
| 14 | 3000 | 4.53 s |

`keras_td3.py:283` gates training on `buffer.size() > max(batch_size, warmup_size)` = 2500, so
episodes 1–12 are pure random rollout at ~0.1 s each and episode 13 onward pays ~3.5–4.5 s for 200
TF gradient steps on CPU. Two consequences: with `warmup_size 2500` and 200-step episodes, **nothing
is learned for the first 12.5 episodes**, so a 15-episode run is a plumbing check and nothing more;
and the per-step cost is ~18 ms, which sets the scale a torch agent has to be compared against.

Added `results/` to the toolkit's `.gitignore` — the driver writes there when launched from the repo
root, and only `jlab_opt_control/drivers/results/*` was covered.

**The Keras baseline this round has to be matched — `KerasTD3-v0` on `Pendulum-v1`, 100 episodes,
4 min 34 s.** This is the number `TorchTD3-v0` gets compared against.

```
.venv/Scripts/python -m jlab_opt_control.drivers.run_continuous \
    --agent KerasTD3-v0 --env Pendulum-v1 --nepisodes 100 --nsteps 200 \
    --logdir ./results/Pendulum --index 1
```

| episode | avg-20 training reward |
|---|---|
| 1 | −1223.5 |
| 20 | −1319.0 |
| 30 | −1198.9 |
| 40 | −559.1 |
| **47** | **first crossing of −200** |
| 50 | −138.5 |
| 60 | −131.1 |
| 100 | −163.0 |

`final avg20 = −163.0`, best single episode −0.9. **Solved**, on stock `keras_td3.cfg` with no tuning.
Logdir `results/Pendulum/index001_env_Pendulum-v1_agent_KerasTD3-v0_hash_48e624f_time_20260812-150620`.
Note this is *one* seed and the driver seeds from wall clock, so it is not repeatable (Q4) — the real
comparison needs ≥3 runs of each arm. Shape sanity check: our own standalone demo crossed −200 around
episode 38 with `warmup_size 1000`; the kit crosses at 47 with `warmup_size 2500`, i.e. the same
trajectory offset by the extra warm-up. Consistent.

**A model-saving bug found by watching this run.** Every single inference point saved a "best"
checkpoint — `epoch_00000_000` through `epoch_00090_006`, ten of them, no rejections — even at episode
90, whose eval return (−226.8) was *worse* than episode 60's (−128.6). Two independent causes:

1. **The averaging window covers the whole run.** `run_continuous.py:264` is
   `np.mean(inference_reward_list[-nepisode_avg:])` with `nepisode_avg` default **20**, but inference
   only runs every `inference_interval` = **10** episodes. Over 100 episodes that is 10 eval points,
   so `[-20:]` is *all of them* — including the random-policy evals from episode 0. The "average
   inference reward" therefore climbs monotonically as the early disasters are diluted, and rises
   whether or not the policy improved: −845 → −743 → −678 → −603 → −565 across episodes 50–90, while
   the underlying evals bounced −117 / −129 / −223 / −4 / −227. The two units are mismatched:
   `nepisode_avg` is counted in *episodes* for the training average (`:281`) and in *eval points* for
   this one.

2. **`model_save_threshold` has the wrong sign for negative rewards.** `:266` is
   `if avg > best * (1 + 0.05)`. With `best = −845` that threshold is `−887`, which is *below* best —
   so the 5 % margin intended to demand a real improvement instead **relaxes** the criterion by 5 %,
   accepting policies that are up to 5 % worse. It tightens as intended only when rewards are
   positive. The correct form is `avg > best + threshold * abs(best)`. Pendulum's reward is always
   negative, and so is the accelerator-tuning reward this kit was built for.

Net effect: `models/epoch_*_*` is not a "best" checkpoint set, it is a snapshot every 10 episodes, and
the `_%03d` percentage in the filename is not meaningful. Anyone loading "the best model" via
`--load_model` gets whatever was saved last. This is shared driver code, not the agent — reporting it
rather than fixing it unilaterally (→ Q9).

**The `notebooks/` folder is post-hoc analysis, not tutorial material.** All four load a *trained*
checkpoint from `./results/<Env>/*<agent_id>*/models/epoch_*` and plot; none trains anything, so none
could run before today. Dependency check against the installed env:

| notebook | needs beyond the installed env | runnable here? |
|---|---|---|
| `ExaminePendulumPolicy.ipynb` | nothing | **yes, once a Pendulum run exists** |
| `ExamineCirclePolicy.ipynb` | `pysindy` | yes, after `pysindy` + a Circle2D run |
| `SINDyPendulumPolicy.ipynb` | `pysindy` | yes, after `pysindy` + a Pendulum run |
| `ExaminePACESPolicy.ipynb` | `paces`, plus a hardcoded path to another dev's Mac | **no** |

`pysindy` is required by three of them and is in **neither `requirements.txt` nor `env.yaml`** — the
declared environment cannot run the toolkit's own notebooks. `ExaminePACESPolicy.ipynb` hardcodes
`/Users/jcolen/Documents/rl_opt_control/models/CEBAF/`. All four have **saved outputs**, so they are
useful to read as static documents regardless. `ExaminePendulumPolicy.ipynb` is the one that matters
for this round: it rebuilds the agent through `agents.make`, loads `models/epoch_*`, and plots critic
value over (θ, ω) with marker size = torque magnitude — i.e. it is the visual check on what the port
learned, and it will exercise the torch agent's `load()` path.

Note its glob is `./results/Pendulum/*{agent_id}*` — **`Pendulum`, not `Pendulum-v1`**. The driver's
`--use_env_subdir` would produce `results/Pendulum-v1/`, which the notebook does not match; passing
`--logdir ./results/Pendulum` explicitly does. Minor, but it means the notebook and the driver flag
disagree.

## Tests run

| What | Command | Result |
|---|---|---|
| GPU present? | `nvidia-smi` / `Get-CimInstance Win32_VideoController` | no NVIDIA; Intel Arc only |
| Python available | `py -0`, `py -3.11 -V` | 3.11.9 ✓, 3.14.5 |
| Packages installed | `py -3.11 -m pip list` | pip/setuptools/pywin32 only — nothing to run yet |
| torch used in toolkit? | `grep -rn "import torch" --include=*.py .` | no matches (exit 1) |
| ER sample cost | `uv run --with numpy python -c '<timeit>'` | table above; linear in fill level |
| TD3 demo smoke | `uv run --python 3.11 --with torch --with gymnasium --with numpy python td3_pendulum_demo.py --episodes 3` | runs; torch 2.13.0+cpu, gymnasium 1.3.0, CPU |
| TD3 demo full | same, `--episodes 60 --seed 0` | **SOLVED** — final avg10 −138.6, best_eval −125.1 |
| Demo seed determinism | same, `--episodes 2 --seed 0`, ×3 | training identical; **EVAL differs each run** → bug 1 above |
| Env install | `uv venv --python 3.11` + `uv pip install -r requirements.txt` + `uv pip install -e .` | exit 0; TF 2.21.0 + torch 2.13.0+cpu on py 3.11.9 |
| Frameworks import together | `python -c "import torch, tensorflow"` | both import; both report 0 GPUs |
| Registry | `agents/envs/buffers.list_registered_modules()` | 7 agents, 2 envs (`Circle2D` ×2), 2 buffers (`ER-v0`, `PER-v0`) |
| **Kit smoke run** | `python -m jlab_opt_control.drivers.run_continuous --agent KerasTD3-v0 --env Pendulum-v1 --nepisodes 15 --nsteps 200 --logdir ./results/Pendulum` | **exit 0, 25 s**; artifacts written; warm-up gate visible in per-episode timing |
| **Keras baseline** | same, `--nepisodes 100 --index 1` | **exit 0, 4 m 34 s; SOLVED** — avg20 crosses −200 at ep 47, final −163.0 |
| Checkpoint criterion | `ls results/Pendulum/index001*/models/` | 10 of 10 eval points saved a "best" model → bug above |

The one claim in this file not backed by execution (TF EagerTensor → `np.asarray` coercion) is
labelled as unverified where it appears.

## Decisions

Taken this round (copy to `../decisions.md` when the round closes):

- **Scope: port the agent + its two networks only.** Reuse the registry, ABC, cfg, and git-hash
  layers unchanged. Driver and buffer rework is deferred and is about *vectorization*, not framework.
- **Recommend architecture B** (rl_games as the Isaac baseline; the toolkit carries the SINDy /
  uncertainty method contribution). A recommendation for discussion, **not** a decision — see Q1.

Still to decide, in code, this round:

- shared vs separate critic optimizers (→ Q3; leaning **separate**, i.e. standard TD3)
- `tf.summary` vs `torch.utils.tensorboard.SummaryWriter` into the same logdir
- the deterministic seeding scheme, and where the seed gets logged

## Carried over

*(nothing yet)*
