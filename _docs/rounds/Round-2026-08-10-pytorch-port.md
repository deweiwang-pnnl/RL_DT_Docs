# Round-2026-08-10 — PyTorch port of the RL algorithms

**Goal:** convert the SciOptControlToolkit RL algorithms from TensorFlow/Keras to PyTorch,
validate them in Gymnasium, and leave the code ready to drop into an Isaac Sim / Isaac Lab
container. Done = TD3 reproduces the Pendulum baseline and `rl_dt/` imports without Isaac.

**Status:** in progress

> *Path note, added 2026-08-19.* This round file is history and its prose is left as written. Two
> things it names no longer exist: the planned `rl_dt/` package (never built — the agent went into the
> toolkit clone instead, see [`../decisions.md`](../decisions.md) 2026-08-12) and the read-only
> `_reference/SciOptControlToolkit-main/` copy (now a live clone at
> `<PROJECT_ROOT>/SciOptControlToolkit`). Links below were repointed to
> [`../learn/1-rl-and-td3.md`](../learn/1-rl-and-td3.md), which absorbed the `learning/` notes.

**Assignment (this week):** "Convert existing RL algorithms to PyTorch, test in gymnasium
environments, and prepare for integration with Isaac Sim/Lab containers."

## Plan

- [ ] **Environment check first.** Confirm PyTorch sees the RTX 5080 (Blackwell / `sm_120` needs a
      `cu128` build — older wheels fail). Record the working versions in `../environment.md`.
- [ ] **Read before porting.** `_reference/SciOptControlToolkit-main/jlab_opt_control/`:
      `drivers/run_continuous.py` (the loop) → `agents/keras_td3.py` (the algorithm) →
      `models/actor_fcnn.py`, `models/critic_fcnn.py` → `buffers/er.py`, `buffers/per.py`.
      Produce a port plan and get it approved before writing code.
- [ ] **Package scaffold:** `rl_dt/` with `agents/ models/ buffers/ envs/ cfgs/ drivers/ utils/`,
      plus `pyproject.toml` and `tests/`.
- [ ] **Buffers** (ER, then PER) + tests.
- [ ] **Models** (actor/critic MLPs, config-driven) + tests.
- [ ] **TD3 agent** — the three tricks: clipped double-Q, target-policy smoothing, delayed actor
      updates. Note: the reference shares one optimizer across both critics; decide whether to
      keep that or use standard separate critics, and record the choice.
- [ ] **Driver** (`train.py` / `eval.py`) with fixed seeds, TensorBoard logging, best-eval
      checkpointing.
- [ ] **Smoke test:** TD3 on `Pendulum-v1` → ≈ −200 within ~50 episodes. Multiple seeds.
- [ ] **SAC, DDPG** once TD3 is green.
- [ ] **Container readiness:** verify `import rl_dt` works with no Isaac installed; document the
      intended container entry point.

## Port constraints found while reading the reference

Not learning material — specs for the code we are about to write. Details and reasoning in
[`../learn/1-rl-and-td3.md`](../learn/1-rl-and-td3.md) § Gymnasium.

- **Store `terminated` in the buffer, never `terminated or truncated`.** The Bellman target's
  `(1.0 - dones)` factor must zero the bootstrap only on genuine termination; zeroing it on a time
  limit teaches the critic that good states are worthless. The reference gets this right (uses
  `done` for loop control, stores `terminate`) — preserve it. Silent failure mode: learning just
  gets quietly worse.
- **Pendulum never exercises that path** — its `terminated` is always `False` (every episode
  truncates at 200 steps). A green smoke test does *not* validate termination handling; the door
  task will be the first real test of it.
- **Seed three RNGs, not one:** `env.reset(seed=...)`, `env.action_space.seed(...)`, and
  `torch.manual_seed` / `np.random.seed`. The reference never seeds the action space, so its warm-up
  (thousands of transitions) is unreproducible even with everything else fixed. Pass `reset(seed=)`
  **once** at the start — every episode gives the identical start state 200 times.
- **Keras artifacts that should not survive the port:** the `model(tf.zeros(...))` warm-up calls
  (PyTorch declares layer shapes up front), the `get_weights`/`set_weights` list surgery in
  `soft_update`, and the per-call `training=` arguments.

## Log

### 2026-08-10
- Round opened.
- Read `CLAUDE.md`, `_docs/environment.md`, `WORKLOG.md`, `decisions.md`; then the reference
  toolkit: `agents/keras_td3.py`, `drivers/run_continuous.py`, `models/actor_fcnn.py`,
  `models/critic_fcnn.py`, `buffers/er.py`, `buffers/per.py`, `cfgs/*.cfg`, and the
  `agents/registration.py` factory.
- **Environment check — no NVIDIA GPU on this machine.** See `../environment.md`; this is a second,
  learning-only machine (HP Elite x360 laptop, Intel Arc integrated graphics — no `nvidia-smi`,
  no `nvcuda.dll`, no NVIDIA PnP device). The RTX 5080 / `cu128` requirement describes the PNNL
  workstation, not this box. Not a blocker for tasks 1–2: Pendulum-scale TD3 (two 256×256 MLPs,
  batch 256) is a CPU job — kernel-launch overhead dominates at that size. It does block task 3.
- Toolchain inventory: nothing installed yet. Python 3.14.6 on PATH and Python 3.11.9 both bare
  (pip/setuptools/pywin32 only); `uv` 0.12.0 available. Torch Windows wheels exist for cp311
  (→2.9.1) and cp314 (→2.11.0). Intend Python **3.11** — the documented target, and far better
  tested across the RL ecosystem than 3.14.
- **Scope narrowed for this round:** tasks 1 and 2 only (PyTorch port + Gymnasium validation).
  Task 3 (Isaac container prep) deferred — cannot be exercised on this machine anyway.
- Learning-first pass, no code yet. Notes written: `learning/pytorch-vs-tensorflow.md` and `learning/gymnasium-basics.md`, both since
  folded into [`../learn/1-rl-and-td3.md`](../learn/1-rl-and-td3.md). Added `learning/` as the home for
  topic-scoped explanatory notes (rounds link to them rather than containing them) — now
  [`../learn/`](../learn/).
- Open question to raise with Alvika / Malachi: `decisions.md` commits to **rl_games PPO** for the
  Isaac track, so what is the ported TD3 ultimately *for*? Best guess — the toolkit's SINDy and
  uncertainty variants (`keras_sindy_critic_td3.py`, `keras_uncertainty_td3.py`,
  `keras_sindy_uncertainty_td3.py`) are the intended research contribution, matching the
  "physics-informed / interpretable component" item in `CLAUDE.md`'s long-term list, with PPO as
  the baseline. **Inferred, not confirmed.** It changes how much extensibility to build into the
  agent layer now.

## Tests run

| What | Command | Result |
|---|---|---|
| | | |

## Decisions

<!-- Copy anything durable to ../decisions.md before closing the round. -->

## Carried over

<!-- Unfinished work and why. -->
