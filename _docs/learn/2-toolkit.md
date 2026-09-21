# Track 2 — The SciOptControlToolkit

> **What you get:** the map you need to find your way around `jlab_opt_control` — what each layer
> does, the one pattern that explains all of it, and where our own code sits inside it.
> **Read it against:** the live clone at `<PROJECT_ROOT>/SciOptControlToolkit`, branch `develop-dw`.
> **Size:** ~180 lines. One sitting, then use the reading order in § 8 over a day at the keyboard.
> **Prerequisites:** [Track 1](1-rl-and-td3.md) — this track assumes you know what TD3 is.
>
> Merged from a pre-code walkthrough and the Jul-24 briefing guide, then corrected against the
> installed clone. Measured numbers and code defects are **not** repeated here — they live in
> [`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md).

## 1. What it is

`jlab_opt_control` is Malachi Schram's (JLab) TensorFlow/Keras toolkit for RL-based control of
**particle accelerators** — distributing RF gradients across CEBAF's superconducting cavities to
minimize cryogenic heat load and trip rate under a hard total-energy constraint. About 4,500 lines.

It is not a robotics framework and was never meant to be. We use it because it is where our group's
method contribution already lives, and because it is Malachi's code — the patterns in it are the
patterns our work is expected to fit.

**One pattern explains the whole repo: registry + config.** Every component — agent, model, buffer,
env — is registered by a string ID in a subpackage's `__init__.py`
(`register(id="KerasTD3-v0", entry_point=..., kwargs={"cfg": "keras_td3.cfg"})`) and built by
`make("KerasTD3-v0", ...)`. Deliberately modelled on `gym.make()`. Hyperparameters never appear in
code; they live in `cfgs/*.cfg` as JSON. Internalize this and the repo stops being surprising: an
experiment is assembled from the command line, and adding a capability means adding a file plus one
registry line.

## 2. The two papers, mapped onto the code

Both from this group, both in `_reference/`. Reading the code without them tells you *what* it does
and not *why*.

| Paper | Idea | Where in code |
|---|---|---|
| **Rajput 2025** (MLST 6 025018) | Compares MOGA, MOBO, CMO-TD3, CMO-DDRL for multi-objective CEBAF optimization. Differentiable-sim RL wins at high dimension (200 cavities); plain TD3 fails the energy constraint there. | The TD3 baseline in `agents/keras_td3.py` is the CMO-TD3 foundation. The CEBAF surrogate envs are in the separate **PACES** package, optionally imported by `run_continuous.py`. |
| **Colen 2026** (MLST 7 015005) | LC-TD3 / Sparse-LC-TD3: augment TD3 with a *learnable* physics surrogate (neural or SINDy sparse dictionary) that predicts an observable and constrains the policy. The sparse version is interpretable — it recovers `E = Σ Gᵢlᵢ` — and is the only method that converges on the 197-cavity linac without a differentiable env. | `agents/keras_sindy_critic_td3.py`, `keras_sindy_uncertainty_td3.py`, `core/sindy_lib_core.py`, `utils/sindy_lib/`, `models/sindy_network.py`, `models/uqsindy_network.py` |

The transferable lesson, and the reason this toolkit is in our project at all: **injecting known
physics is what makes RL scale on high-dimensional, hard-constrained systems.** Isaac Lab supplies
the parallel-physics side; this toolkit supplies the agent-side patterns.

## 3. Repo map

```
jlab_opt_control/
├── core/      abstract base classes: Agent, Model, ReplayBuffer, SINDyLibrary
├── agents/    TD3 (main), DDPG, SAC, REDQ-TD3, Uncertainty-TD3, SINDy-TD3 variants
│              + torch_td3.py  ← ours
├── models/    actor/critic MLPs built from cfg, SINDy networks
│              + torch_models.py, core/torch_model_core.py  ← ours
├── buffers/   er.py (uniform replay), per.py (prioritized replay)
├── envs/      Circle2D toy env + a gym-style registry
│              + robotics_flat.py  ← ours
├── cfgs/      JSON — ALL hyperparameters
│              + torch_td3.cfg  ← ours
├── drivers/   run_continuous.py — THE entry point
└── utils/     cfg parsing, git-hash logging, SINDy feature libraries
```

| Layer | Files | What to know |
|---|---|---|
| **Driver** | `drivers/run_continuous.py` | The whole RL loop. `main()` → `run_opt()` → `run_episode()`. ~390 lines; the ~50 that matter are the episode loop. |
| **Agent** | `agents/keras_td3.py` and variants | TD3 = DDPG + three fixes, all visible in `train_critic()` / `train_actor()`. |
| **Models** | `models/actor_fcnn.py`, `critic_fcnn.py` | Plain MLPs. Actor 2×256 ReLU → tanh scaled to action bounds; critic concat(s,a) → 2×256 → scalar Q. |
| **Buffers** | `buffers/er.py`, `per.py` | Uniform vs prioritized replay. |
| **Envs** | `envs/circle_env.py` | `Circle2D-v0` (see § 6). Standard Gymnasium envs work directly. |
| **Registry** | `*/registration.py` | The `make()` / `register()` machinery. |
| **Configs** | `cfgs/*.cfg` | `keras_td3.cfg`: lr 3e-4 both nets, γ 0.99, τ 0.005, batch 256, warmup 2500, ER buffer 1M. |

## 4. Execution flow — start here

```bash
python -m jlab_opt_control.drivers.run_continuous \
    --agent KerasTD3-v0 --env Pendulum-v1 --nepisodes 100 --nsteps 200
```

1. `main()` parses args → `run_opt()`.
2. `create_and_configure_env()` tries three registries in order: standard Gymnasium, the toolkit's own
   envs (`Circle2D-v0`), then PACES (optional, absent here).
3. The env is wrapped in `TimeLimit`; the agent is built via `agents.make()`.
4. `run_episode()`: `agent.action(state)` → `env.step(action)` → `agent.memory((s,a,r,s',terminate))`
   → `agent.train()`. **One gradient update per env step**, single environment.
5. Every `inference_interval` (10) episodes a noise-free evaluation episode runs, and the model is
   checkpointed when the rolling average inference reward improves by `model_save_threshold`.
6. Everything needed to reproduce a run lands in `./results/index###_env..._time.../` — TensorBoard
   scalars, `results.npy`, buffer snapshots, config copies, and the git SHA.

Two things in that list are **measurably broken** — the checkpoint criterion never rejects anything,
and the evaluation runs on the training env object. Do not take steps 5–6 at face value; read
[`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md) § Failure modes before you trust a
number that came out of this driver.

**Reading tip that will save you an hour.** Derive the agent interface from the driver and the tests,
**not** from the ABC. `core/agent_core.py` omits `memory` and `buffer`, both of which
`run_continuous.py` requires — the declared interface is narrower than the real one.

## 5. The TD3 agent is the extension point

Read `agents/keras_td3.py` closely, because it is the class every research variant is a delta from.
Six networks (actor + target, two critics + two targets), built via `models.make()` from cfg.
`train_critic()` holds tricks 1 and 2, `train_actor()` holds trick 3, and `action()` handles the
warm-up gate and exploration noise.

The structural finding that shaped our whole plan: **`KerasSINDyCriticTD3`, `KerasUncertaintyTD3` and
`KerasSINDyUncertaintyTD3` all subclass the TD3 agent and override `train_critic`, changing almost
nothing else.** So the SINDy-structured critic and the uncertainty-aware critic are not separate
algorithms — they are modifications of the Bellman-target computation inside TD3. A clean overridable
`train_critic` is therefore the single most important design property of any port, which is why our
port did TD3 first. Detail: [`../strategy.md`](../strategy.md).

## 6. Envs — and the assumption they reveal

`Circle2D-v0` has a 2D state and 2D action, reward `1000·exp(−5·|‖s‖ − 0.95|)` peaking on a circle of
radius 0.95, and a **single-step episode** by default. It is an *optimization problem dressed as RL*,
which mirrors exactly how the papers treat CEBAF: pick the cavity gradients once, collect the reward.

**Internalize this.** The toolkit's home problem is near-single-step optimization under a hard
constraint. The door task is a genuine long-horizon sequential MDP — approach, grasp, swing, over
hundreds of timesteps. That single difference drives most of what has to change: reward shaping,
termination design, algorithm choice, and parallelism.

## 7. The physics-informed agents — the research crown jewel

`core/sindy_lib_core.py` and `utils/sindy_lib/` implement SINDy-style feature libraries (Polynomial,
Fourier) composable with `+` (concat) and `*` (product), mapping `[s, a]` to candidate terms
(1, Gᵢ, GᵢGⱼ, Gᵢ², …).

`KerasSINDyCriticTD3` then adds two things to TD3: a **SINDy critic**, a sparse-regularized linear
model over those library features trained each step to match `min(Q1, Q2)` of the neural critics; and
a modified actor loss `q = β·q_sindy + (1−β)·q_critic`, where cfg `sindy_beta` defaults to **1.0** —
meaning the actor trains *entirely* through the interpretable surrogate. Because the surrogate is a
linear combination of known basis functions, you can read the learned equation off and check it
against physics.

`KerasUncertaintyTD3` has critics output `(Q, log σ²)` with a KL regularizer on the variance head, and
during training picks the action with **maximum critic uncertainty** among 256 random candidates —
active-learning-style exploration.

**One discrepancy worth carrying to a meeting.** Colen 2026's LC-TD3 surrogate predicts a physical
*observable* (energy) with an explicit constraint penalty. The released SINDy agent instead distills
the *critic* into a sparse model. Same machinery, different target — the observable-constraint variant
presumably lives with the PACES envs, which we do not have. This is an open question, not a settled
reading: [`../team-discussion.md`](../team-discussion.md).

## 8. Reading order

At the keyboard, in the live clone. Items 3–4 are ours and are the fastest way to see the patterns
above applied by someone who had to learn them recently.

1. `drivers/run_continuous.py` — `run_episode()` then `run_opt()`. The whole loop.
2. `agents/keras_td3.py` — `__init__`, `action()`, `train()`, `train_critic()`, `train_actor()`.
3. `agents/torch_td3.py` — the same algorithm in PyTorch, ours. Diff it against #2 mentally.
4. `utests/test_torch_td3.py` — 47 tests. Reading tests is the fastest way to learn what the
   contract actually is, including the parts the ABC omits.
5. `models/actor_fcnn.py` + `critic_fcnn.py`, then `buffers/er.py` → `per.py`.
6. `envs/circle_env.py` plus any `registration.py` — the registry pattern in ten lines.
7. Colen 2026 § 3, then `agents/keras_sindy_critic_td3.py` → `core/sindy_lib_core.py`.
8. `notebooks/ExaminePendulumPolicy.ipynb` — loads a trained checkpoint and plots the policy. The
   useful one; three of the other four need `pysindy` (installed nowhere) and
   `ExaminePACESPolicy.ipynb` hardcodes a path on another developer's Mac.

The runnable smoke test and the baseline number to expect are in `CLAUDE.md` § How to run — one
command, already verified on this machine. Don't take the install instructions from the old briefing
docs; `env.yaml` pins Python 3.13, and the whole dependency set in fact resolves on 3.11.9.

## 9. What this track does not cover

- **The port's scope and status** — what was ported, what was reused, what was deliberately deferred,
  and the architecture options: [`../strategy.md`](../strategy.md).
- **The measured defects** and every number with evidence attached:
  [`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md).
- **PER and REDQ-TD3** — registered and untested by us end to end.
- **The PACES envs** — a separate package we do not have.
- **Isaac Lab and rl_games** — [Track 3](3-isaac-and-rl-games.md).

Deeper reference: `_reference/SciOptControlToolkit-wiki`,
`_reference/SciOptControlToolkit_Walkthrough.pdf`, and the two MLST papers
`_reference/Rajput_2025_*.pdf` and `_reference/Colen_2026_*.pdf`.
