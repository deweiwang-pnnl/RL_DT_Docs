# Decision log

Append-only, in date order, newest at the bottom. One entry per decision: what, when, why, and what it
rules out. An entry is never edited or removed once written — if a decision is reversed, a new entry
says so. A decision recorded late is inserted at its own date and marked **backfilled**.

Open questions live in [`team-discussion.md`](team-discussion.md); when one is answered, the answer
graduates to a new entry here.

---

## 2026-08-03 — Build in PyTorch, not TensorFlow
The reference toolkit (`SciOptControlToolkit`) is TF/Keras. The Isaac Lab RL ecosystem
(rl_games, skrl, RSL-RL, SB3) is PyTorch. We port the *logic* rather than wrap TF.

## 2026-08-03 — rl_games PPO for the Isaac Lab track
Already working in the preliminary `RL_CloudTesting/` code. Staying on it avoids a rewrite.
Revisit if we need off-policy sample efficiency (SAC/TD3) for comparison results.

## 2026-08-03 — Privileged simulator state for observations
Vision is a later option, not the first target.

## 2026-08-03 — Repo is `RL_DT/`, a subfolder of the project root
`_docs` and `_reference` stay outside version control (USD assets are hundreds of MB).
Consequence: they must be re-obtained per machine — documented in `environment.md`.

---

## 2026-08-12 — Add a torch agent *inside* the existing toolkit, not a new `rl_dt/` package
**Backfilled 2026-08-19** — decided in Round-08-12 and cited in `CLAUDE.md` as standing, but never
written here.

`CLAUDE.md` originally planned a from-scratch PyTorch package in this repo (`rl_dt/agents/`, `models/`,
`buffers/`, `envs/`, `cfgs/`, `drivers/`, `utils/`). Instead the port lands in the live clone at
`<PROJECT_ROOT>/SciOptControlToolkit/jlab_opt_control/`, reusing its registry, config, ABC and
git-hash layers unchanged.

Why: only the agent-and-networks layer is genuinely framework-bound (~410 lines), and reusing the
registry is what makes `--agent TorchTD3-v0` swap against `--agent KerasTD3-v0` in one command line —
which is the only way to get a controlled framework comparison. Reasoning:
[`strategy.md`](strategy.md) Parts 1–2.

Rules out keeping RL code in this repo. `RL_DT/` holds documentation and the record of work only; the
two repos never mix, and the `rl_dt/` package layout is marked superseded in `CLAUDE.md` rather than
quietly dropped.

## 2026-08-17 — Changes to the toolkit are additive only
Nothing in `SciOptControlToolkit` gets modified or deleted; new files plus added lines in
`__init__.py` registries only. Verified rather than asserted: `git diff --stat 48e624f..HEAD` on
branch `develop-dw` is **1376 insertions, 0 deletions**.

Why: it is upstream code shared with other users, and a purely additive change cannot break an
existing run, which makes the branch safe to hand to Malachi at any point.

Rules out the cleaner fix in two places. Goal-conditioned `Dict` observation spaces would be better
handled by three lines in `drivers/run_continuous.py` than by the `envs/robotics_flat.py` factory that
exists to work around it, and the two driver defects found in Round-08-12 (the sign-inverted
checkpoint threshold, the `nepisode_avg` unit mismatch) stay unfixed. Both become an upstream proposal
written in this repo for Malachi to decide on.

## 2026-08-17 — `seed` and `device` are cfg keys in `TorchTD3`, with no Keras counterpart
`cfgs/torch_td3.cfg` deliberately breaks byte-identical parity with `keras_td3.cfg` on two keys. The
Keras agent seeds from `time.time_ns()`, so no Keras run is repeatable; the torch agent seeds
`random`, `numpy`, `torch`, CUDA and the action space **before any model is constructed**, so network
initialization is inside what is reproducible. `device` exists because this laptop has no CUDA and
the workstation does, so it can never be assumed.

Rules out the simplest defence of the port ("the configs are identical"). The honest statement is
that the 11 *shared* keys are byte-identical, four more promote Keras literals at their existing
values, and these two are additions. Also means the two arms are not symmetric: torch runs can be
replicated exactly, Keras runs cannot.

## 2026-08-17 — Four Keras hardcoded literals promoted to cfg keys at their existing values
`actor_update_freq` 2, `critic_update_freq` 2, `target_noise_clip` 0.5 (a literal at
`agents/keras_td3.py:148`) and `target_policy_noise` 0.2 (a literal at line 218) are cfg keys in the
torch agent, set to the numbers the Keras agent already used.

Why both halves matter: the project rule is no hyperparameters in code, and a framework comparison is
only controlled if the values are unchanged. Promoting them to config satisfies the first without
violating the second.

Rules out tuning them as part of the port. Any future change to these four is a separate experiment
with its own before/after, not a detail buried in a port commit.

## 2026-08-17 — Separate Adam optimizers, one per critic — a deliberate *deviation* from Keras
`TorchTD3` gives each of the two critics its own `torch.optim.Adam`. The Keras agent uses **one** Adam
over the concatenated variables of both.

Why deviate, when everything else in the port aims at parity: a single optimizer pools Adam's
first/second-moment estimates and its step counter across two networks that TD3 requires to be
*independent* estimators — the clipped double-Q target is only meaningful if the two critics err
differently. This is documented in the `TorchTD3` class docstring as difference 2 of 3.

Rules out the "the two agents differ in nothing" defence of the port. Three deviations exist and are
named — deterministic seeding, separate critic optimizers, and the TensorBoard writer below — so any
residual gap in the four-environment comparison has three candidate explanations that must be stated
rather than one that can be waved away.

## 2026-08-17 — `torch.utils.tensorboard.SummaryWriter` for logging, not `tf.summary`
The torch agent writes its own scalars rather than reusing the driver's TF summary writer.

Why: the point of porting this layer is a package importable in a torch-only Isaac container, and
routing torch metrics through `tf.summary` would put TensorFlow back into the one file that was ported
to remove it. Side benefit found while running the comparison: the Keras agent makes its own
`tf.summary` writer the *process default*, so the driver's scalars land in the agent's event file; the
torch agent leaves TF's global default alone. Both land in `metrics/` and TensorBoard merges them, so
`tensorboard --logdir ./results/` still overlays both arms.

Rules out nothing that matters. Note that TF is still required to *import* the package, for an unrelated
reason — [`strategy.md`](strategy.md) Part 2, Tier 1.
