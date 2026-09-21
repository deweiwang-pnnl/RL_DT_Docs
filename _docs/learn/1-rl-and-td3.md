# Track 1 — Fundamental RL and TD3

> **What you get:** enough RL to read and modify the ported agent — the Gymnasium contract, the
> Bellman target, and the three tricks that make TD3 work.
> **Read it against:** [`td3_pendulum_demo.py`](td3_pendulum_demo.py) in this folder, running.
> **Size:** 450 lines, the longest track by a wide margin — it replaces three separate files.
> Parts 1–2 are the sitting; Parts 3–4 and the appendix are lookup, read them when you hit them.
> **Prerequisites:** none. Everything else in `learn/` assumes this one.
>
> Written during Round-2026-08-10, updated after the port landed. **Explanatory notes, not project
> decisions** — those live in [`../decisions.md`](../decisions.md). Where this disagrees with
> gymnasium.farama.org or pytorch.org, the docs win.

## How to run the demo

```bash
cd "<PROJECT_ROOT>/SciOptControlToolkit"        # any env with torch + gymnasium
.venv/Scripts/python "<REPO>/_docs/learn/td3_pendulum_demo.py"                  # 60 episodes
.venv/Scripts/python "<REPO>/_docs/learn/td3_pendulum_demo.py" --episodes 30 --seed 1
```

**A teaching artifact and a smoke test, not the port.** Deliberately one file with hyperparameters as
inline constants so the whole algorithm reads top to bottom. The shipped agent is
`jlab_opt_control/agents/torch_td3.py` in the toolkit clone, with hyperparameters in
`cfgs/torch_td3.cfg`, per `CLAUDE.md` ("no hyperparameters in code").

---

# Part 1 — The environment side

## Gymnasium is a library; Pendulum-v1 is one environment in it

Gymnasium is the maintained fork of OpenAI Gym, run by the Farama Foundation since OpenAI stopped
developing Gym around 2022. `import gymnasium as gym` is the modern import; a tutorial doing
`import gym` is pre-2022 code.

It provides **two** things, and conflating them hides why this project cares:

1. **An interface specification** — `reset()` / `step()`, `Box` and `Discrete` spaces, the
   `terminated`/`truncated` split. Abstract; contains no physics.
2. **A bundled collection of environments** — CartPole, Pendulum, MuJoCo, Atari.

The collection is the obvious half. **The interface is the half that matters here**, because Isaac Lab
implements #1 without being part of #2: `ManagerBasedRLEnv` is NVIDIA's code, in a different package,
on a different physics engine, using the same contract.

```
        Gymnasium interface  (reset / step / Box / terminated+truncated)
                    │
    ┌───────────────┼────────────────┬──────────────────┐
Pendulum-v1     CartPole-v1     MuJoCo tasks      Isaac Lab door task
(in Gymnasium's collection)                    (NVIDIA's code, same contract)
```

Pendulum and the door task are siblings under one specification. That is why one agent can drive both,
and why the agent layer must import without Isaac.

## The core contract

`reset()` → `(observation, info)`. `step(action)` →
`(observation, reward, terminated, truncated, info)`. The resulting loop
(`drivers/run_continuous.py`, `run_episode`):

```python
state, _ = env.reset()
while not done:
    action, _ = agent.action(state)
    next_state, reward, terminate, truncate, _ = env.step(action)
    done = terminate or truncate
    agent.memory((state, action, reward, next_state, terminate))
    agent.train()
    state = next_state
```

Observe → act → receive → store → learn → repeat. The environment owns the task, the agent owns the
learning, neither knows the other's internals.

## `terminated` vs `truncated` — the one thing to really understand

Gymnasium's headline change from old Gym's single `done` flag. It exists because merging the two was
causing silently wrong RL implementations.

| Flag | Meaning | Example |
|---|---|---|
| `terminated` | Ended **for a reason inside the MDP** — a genuine terminal state, no future beyond here. | CartPole pole angle > 12° |
| `truncated` | Cut off **from outside** — time limit, external abort. The state was fine; we stopped watching. | hit the 200-step cap |

Both end the loop, but they mean opposite things to the learner, because of value bootstrapping. The
critic's Bellman target is `q_targets = rewards + gamma * target_q * (1.0 - dones)`. When `dones = 1`
the future term vanishes — the state is worth exactly its immediate reward. **Correct for termination**
(the pole fell; there is genuinely no future). **Wrong for truncation** (the pendulum at step 200 is
still spinning and has plenty of future value). Zeroing the bootstrap there teaches the critic that
good states are worthless, and the error propagates backwards through the value function.

Rule: **bootstrap through truncation; cut the bootstrap only on termination.** Note how the loop above
uses `done` for control flow but stores `terminate` alone in the buffer. One careless `done` there is a
silent bug that just makes learning quietly worse — which is why the ported agent has a dedicated test
for it, and why that test was verified by breaking the line on purpose
([`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md) § Method choices, 2026-08-19).

**Pendulum caveat:** its `terminated` is *always* `False` — no failure state, no goal state, it just
spins until truncation at 200 steps. So the stored flag is always 0 and **this code path is never
exercised by the smoke test.** Do not read "Pendulum works" as "termination handling is correct." Of
the five environments used in the port comparison, only `Hopper-v5` terminates for real. The door task
will too.

## Spaces

A `Space` describes the shape of observations and actions. Three matter:

- **`Box`** — continuous, bounded, n-dimensional. Has `.shape`, `.low`, `.high`, `.sample()`.
- **`Discrete(n)`** — one integer in `0..n-1`. TD3 emits real values through a `tanh`, so it
  structurally cannot handle this; hence the toolkit's `assert "Box" in str(type(env.action_space))`.
- **`Dict`** — a named bundle of sub-spaces, and its `.shape` is `None`, which breaks any code reading
  `observation_space.shape[0]`. All 217 goal-conditioned gymnasium-robotics environments use it; see
  `envs/robotics_flat.py` in the toolkit clone for the wrapper that opened them up.

Spaces are also how the agent self-configures: it reads `observation_space.shape[0]` and
`action_space.shape[0]` to size networks, and `.high`/`.low` to scale output. No dimension is
hardcoded, which is what lets the same agent run Pendulum now and a 6-DOF arm later.
`action_space.sample()` does real work too — during warm-up the agent ignores its network and samples
uniformly, because an untrained network's actions are nearly constant and teach the critic almost
nothing.

## Pendulum-v1, and why −200

Swing-up: a rigid pendulum on a frictionless pivot, torque at the pivot, random start angle (usually
hanging down). The torque limit is **deliberately too weak to lift it directly**, so the policy must
learn to pump energy in and swing.

- **Observation — 3 numbers:** `cos(θ)`, `sin(θ)` in [−1, 1], and `θ̇` in [−8, 8]. Why `cos`/`sin`
  rather than the angle? Angle wraps: θ = +3.14 and θ = −3.14 are the same physical state at opposite
  ends of the numeric range, a discontinuity the network would have to learn. `(cos, sin)` is
  continuous everywhere. The trick recurs throughout robotics — we will want it for door-hinge angles.
- **Action — 1 number:** torque in [−2, 2].
- **Reward — always negative:** `r = −(θ² + 0.1·θ̇² + 0.001·torque²)`, θ measured from upright.
  Penalties for being away from vertical (dominant), spinning fast, and spending effort. Best possible
  is 0, so returns are negative and "better" means "closer to zero."
- **Episode length:** exactly 200 steps, always.

| Policy | Return | Reasoning |
|---|---|---|
| Do nothing | ≈ −1900 | hangs at bottom, θ ≈ π → ≈ 9.9 cost/step × 200 |
| Random torque | ≈ −1200 | jiggles, occasionally swings up by luck |
| **Good policy** | **≈ −150 to −200** | swings up in ~30–50 steps, then holds near-zero cost |
| Theoretical max | 0 | unreachable — requires starting upright |

Even a perfect policy cannot approach 0: the pendulum *starts* down and every step of the swing-up
accrues cost, worth roughly −100 to −150. So **−200 means solved.** The gap from −1200 to −200 is large
and unambiguous, which is why Pendulum is the standard smoke test — a real bug lands you near random
and you *know*, with no marginal result to interpret.

Because the start angle is random, single-episode returns are noisy. Judge the rolling average (the
toolkit's `nepisode_avg`, default 20) over multiple seeds, never one episode.

## Wrappers

An environment wrapping another, same interface, modified behaviour — composable like decorators. The
toolkit uses three: `TimeLimit` (injects `truncated` after N steps; redundant on Pendulum, which
already has a 200-step limit), `RescaleAction` (remaps the action range), and `FlattenObservation`
(collapses a `Dict` into one flat vector — the one that unlocked the Fetch/Hand/Maze/Kitchen families;
note it concatenates in **sorted key order**, so the agent's input layout depends on that ordering
rather than on anything declared).

Wrappers are where environment-specific adaptation belongs, which keeps the agent generic. For Isaac,
observation normalization should live here rather than inside TD3.

## Seeding — three RNGs, not one

| RNG | Seeded by | Controls |
|---|---|---|
| Environment | `env.reset(seed=...)` | starting states, env noise |
| Action space | `env.action_space.seed(...)` | `action_space.sample()` — the warm-up actions |
| Torch / NumPy | `torch.manual_seed`, `np.random.seed` | weight init, exploration noise, buffer sampling |

Seeding the env does **not** seed the action space. The Keras agent never seeds it at all, so even with
everything else fixed its warm-up differs run to run — and warm-up is thousands of transitions shaping
the entire early buffer. `TorchTD3` seeds all three from a `seed` cfg key, before any model is
constructed. Also: `reset(seed=...)` seeds the generator, so pass it **once** at the start; the same
seed on every reset gives the identical starting state 200 times.

A subtler trap sits one step out: seeding *training* does not make *evaluation* reproducible, and the
evaluation number is the one that gets published. Measured in this demo — 170 points of spread across
four runs of the same seed. See [`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md)
§ Failure modes, 2026-08-12.

## What Pendulum does not prove

- **Vectorization** — Isaac Lab returns 256+ envs as batched GPU tensors; this is one env returning
  CPU NumPy. Different loop shape, and replay buffers need real adaptation.
- **Termination handling** — always `False` here, as above.
- **Scale** — 3 obs / 1 action vs dozens / 7 joints. Hyperparameters will not transfer directly.
- **Anything task-shaped** — reward design, scene correctness, whether the door problem is well-posed.

Pendulum validates *the algorithm*. Everything else remains ahead.

---

# Part 2 — TD3

## What you should see

```
ep   1 | warmup | steps    200 | return  -1477.3 | avg10  -1477.3
ep   5 | warmup | steps   1000 | return  -1181.9 | avg10  -1315.5 | EVAL  -1215.4
ep  15 | train  | steps   3000 | return   -893.0 | avg10   -984.2 | EVAL   -382.1
ep  30 | train  | steps   6000 | return   -238.6 | avg10   -251.0 | EVAL   -155.2
```

Warm-up (ep 1–5) sits at −1200 to −1500 on uniform random actions with no learning; early learning
(5–20) climbs −1200 → −400 as the critic becomes useful and the actor follows; convergence (20–50)
reaches −400 → −200. `EVAL` is greedy and averaged over 3 episodes, so it is the honest number and
usually **better** than the training return. Expect noise — TD3 sometimes plateaus near −700 for ten
episodes and then drops fast. Still ≈ −1200 by episode 30 means something is wrong.

## The algorithm in one page

TD3 = **T**win **D**elayed **D**DPG. Two networks with different jobs:

- **Actor** `π(s) → a`. A *deterministic* policy: one state in, one action out. No probability
  distribution (that's SAC). Job: output the action the critic likes best.
- **Critic** `Q(s, a) → scalar`. Expected discounted return from taking `a` in `s`. Job: predict the
  Bellman target.

They bootstrap each other. The critic learns to predict returns from collected experience; the actor
learns to pick actions the critic scores highly. Neither is given the answer — the only ground truth is
the reward stream.

**The learning signal.** The value of a state-action pair is the reward now plus the discounted value of
where you end up, `Q(s, a) ≈ r + γ · Q(s', π(s'))`. Turn it into a regression target:

```python
target = rew + GAMMA * (1.0 - done) * target_q      # what Q *should* be
critic1_loss = F.mse_loss(self.critic1(obs, act), target)
```

`γ = 0.99` means a reward 100 steps out is worth ≈ 0.37 of an immediate one — enough foresight to plan
a swing-up, short enough to stay numerically stable.

**Why DDPG needed fixing.** DDPG is this loop with one critic, and it systematically **overestimates**.
Q is a noisy estimate, the actor is trained to maximise it, so the actor is an error-seeking missile
that finds wherever Q is spuriously high. That inflated value then enters its own target via
`Q(s', π(s'))`, so the error compounds and training collapses. TD3's three tricks each attack one part
of that loop.

## Trick 1 — clipped double-Q

```python
target_q = torch.min(self.critic1_target(next_obs, next_act),
                     self.critic2_target(next_obs, next_act))
```

Two independent critics, and the target uses the **minimum**. Both overestimate, but in *different
places* (different random init, different gradient noise), so for the actor to exploit an error
**both** must be wrong at the same point — far less likely. A deliberate downward bias traded for
stability: underestimating a good action is survivable, overestimating a bad one is not. The critics
stay independent — separate parameters, losses and optimizers. Only the `min` couples them.

## Trick 2 — target policy smoothing

```python
noise = (torch.randn_like(act) * self.action_scale * POLICY_NOISE).clamp(
    -NOISE_CLIP * self.action_scale, NOISE_CLIP * self.action_scale)
next_act = (self.actor_target(next_obs) + noise).clamp(self.low, self.high)
```

Similar actions should have similar values — physics is smooth, torque 1.00 and 1.02 cannot differ
wildly in worth. But a neural net can develop a sharp spurious spike and the actor will drive straight
into it. Sampling the target at `π(s') + noise` averages Q over a small neighbourhood, smoothing narrow
peaks away; it is a regulariser on the value landscape. The clip stops a rare large Gaussian draw from
sampling a completely unrelated action.

This noise is on the **target action inside the critic update** — different from exploration noise,
which is added to the action actually sent to the environment. Two noises, two jobs, easy to conflate
on a first reading of TD3.

## Trick 3 — delayed policy updates

```python
if self.total_updates % POLICY_DELAY == 0:      # every 2nd critic update
    actor_loss = -self.critic1(obs, self.actor(obs)).mean()
```

The actor is only as good as the critic guiding it, so updating it every step means chasing a target
that is itself thrashing. Every *other* step lets the critic settle between policy changes. Target
networks are soft-updated inside the same branch, so they move on the actor's schedule.

**The actor loss deserves a second look.** There is no "correct action" label anywhere — no supervised
signal. We want to *maximise* Q and optimizers minimise, hence the minus sign. Gradients flow backwards
through `critic1` into the actor's weights: the critic is a differentiable model of "how good is this
action," and the actor does gradient ascent through it. Only possible because actions are continuous
and Q is differentiable with respect to them.

`critic1`'s parameters receive gradients here too — but `actor_opt` was constructed with only
`self.actor.parameters()`, so `actor_opt.step()` cannot touch them, and they are cleared at the next
`critic1_opt.zero_grad()`. Worth understanding rather than trusting: in PyTorch, *what gets updated is
determined by which parameters you handed the optimizer*, not by where gradients flowed.

## Target networks

Three networks became six: each has a slow-moving copy. Without them the critic's target depends on the
critic's own current weights, so every update moves the target it is chasing — unstable in exactly the
way hitting a target attached to your own hand is unstable.

```python
def soft_update(net, target_net, tau):        # tau = 0.005
    for p, tp in zip(net.parameters(), target_net.parameters()):
        tp.mul_(1.0 - tau).add_(tau * p)      # target = 0.995*target + 0.005*online
```

Polyak averaging: each update pulls the target 0.5% toward the online net, tracking it ~200× slower, so
it is effectively a stable reference. Targets are never trained — hence `p.requires_grad_(False)`.

Note the asymmetry in that line. At `tau = 0.5` the two coefficients are equal, so swapping them
changes nothing, which is why a test at `tau = 0.5` cannot detect the swap and one at `tau = 0.25` can.
That is a real finding from the port, not a hypothetical.

## The replay buffer

```python
idx = rng.integers(0, len(self), size=batch_size)
```

Two jobs. **Decorrelation:** consecutive steps in an episode are nearly identical, so a batch of them
is effectively one sample and gives a badly biased gradient; uniform sampling from 100k transitions
gives a batch spanning many episodes. **Sample reuse:** each transition is trained on many times, which
is what makes off-policy methods like TD3/SAC far more sample-efficient than PPO — and that matters
when a sample means a simulator step, more still on real hardware.

Off-policy means the data can come from an *older, worse* policy and still be usable, because the
Bellman equation holds for any transition regardless of what generated it.

The draw above is **with** replacement. The toolkit's `buffers/er.py` draws without, which is three
orders of magnitude slower once the buffer fills — measured, with the numbers, in
[`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md) § Failure modes, 2026-08-12. Worth knowing
that the obvious choice here is also the fast one.

## PyTorch mechanics worth noticing

- **`with torch.no_grad():` around the target.** The target is a constant for this update. Without it,
  autograd builds a graph through the target networks and gradients flow where they must not — a subtly
  wrong algorithm that still runs.
- **`zero_grad()` before every `backward()`.** Gradients *accumulate* in PyTorch. Omit it and each
  update uses the sum of all previous gradients. Silent, and catastrophic.
- **`@torch.no_grad()` on `act()` and `soft_update()`.** Inference and in-place parameter surgery;
  neither needs a graph.
- **`register_buffer` for `action_scale` / `action_bias`.** Non-trainable tensors that should still move
  with `.to(device)` and be saved in `state_dict()`. A plain `self.x = torch.tensor(...)` silently stays
  on the CPU when the model moves to a GPU.

---

# Part 3 — Where the demo differs from the Keras reference, deliberately

| | Reference (`keras_td3.py`) | This demo | Why |
|---|---|---|---|
| Critic optimizers | one shared, losses summed | separate per critic | Same gradients, but Adam's per-parameter moments belong to each critic. Standard TD3 keeps them separate. |
| Seeding | wall-clock `time.time_ns()`; action space never seeded | all three RNGs from `--seed` | `CLAUDE.md`: fixed seeds, always. The reference cannot reproduce a run. |
| Keras warm-up calls | `model(tf.zeros(...))` to build variables | none | PyTorch declares layer shapes up front. |
| Target init | `set_weights(get_weights())` | `copy.deepcopy` | Idiomatic, and no dependency on the warm-up call above. |
| Config | `.cfg` JSON files | inline constants | This is a demo. The shipped agent uses `cfgs/torch_td3.cfg`. |

# Part 4 — How this played out in the real port

These notes were written before any agent code existed. Three things the port then taught, each with
evidence in [`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md):

- **A silent default can be a confound.** Keras `Dense` initializes Glorot-uniform, PyTorch `Linear`
  Kaiming-uniform — a factor of 1.7 on a 256-wide layer. Left alone, a "PyTorch vs TensorFlow" curve is
  partly an *initialization* comparison, and nothing in either file names the initializer. Now a cfg
  key. (§ Method choices, 2026-08-17)
- **A passing suite is weak evidence.** 47 tests passed first try; three defects were then injected into
  `torch_td3.py` one at a time to see which tests noticed — `minimum`→`maximum` caught by 3,
  `(1 - dones)`→`dones` by 5, the tau swap by 1. Report what a suite catches, not that it passes.
  (§ Method choices, 2026-08-19)
- **The result is mixed, and that is the point.** `TorchTD3-v0` beats the Keras arm on two
  environments, loses on one, ties on one. A clean sweep would more likely mean a changed hyperparameter
  than a better implementation. (§ Comparisons, 2026-08-18)

Open questions this material raises — what the ported TD3 is ultimately *for*, whether the SINDy and
uncertainty variants get ported, SAC or DDPG next — are collected in
[`../team-discussion.md`](../team-discussion.md), not here.

---

# Appendix — PyTorch vs TensorFlow, the five contrasts that mattered

The port was Keras → PyTorch, so these are the differences that actually showed up in the diff.

**1. Define-by-run vs define-then-run.** TF1 built a symbolic graph, then fed data through it in a
`Session`. PyTorch has no build step: you write ordinary Python on real data and the graph is recorded
as a side effect, fresh each forward pass and discarded after. So a PyTorch model is just Python —
`print()` a tensor mid-forward-pass, set a breakpoint inside the network, branch on data-dependent
values. TF2 made eager the default and largely closed the gap, but the lineage shows in
`@tf.function` on `train_critic` ("trace this once, then run it as a static graph"). Fast, and it is
why TF stack traces are hard to read: the failure happens inside a traced graph, not in your Python.
PyTorch's `torch.compile` is opt-in.

**2. Gradients: a tape object vs a tensor attribute.** TF declares the recording region and asks the
tape; PyTorch always records and accumulates *into* the tensors.

```python
with tf.GradientTape() as tape:                     # TF: start recording
    critic_loss1 = self.mse_loss(self.critic_model1(states, actions, training=True), q_targets)
gradients = tape.gradient(critic_losses, vars)      # ask the tape
self.critic_optimizer.apply_gradients(zip(gradients, vars))
```
```python
optimizer.zero_grad()   # torch: clear last step's gradients — mandatory
loss.backward()         # walk the graph, fill every .grad
optimizer.step()        # apply them
```

`zero_grad()` is mandatory because `.backward()` *adds to* `.grad` rather than replacing it. The
accumulation default is deliberate — it lets you split one large batch across several backward passes —
but forgetting it is the most common beginner bug. Note also that computing and applying gradients are
separate calls on separate objects; TF fuses them into `apply_gradients`.

**3. Explicit device placement.** TF places tensors on a GPU automatically when one exists; PyTorch
makes you say `x.to(device)` and errors if you mix CPU and GPU tensors. More verbose, but you always
know where data is — and it is why the same code runs on this CPU-only laptop and on the RTX 5080 box
with `device` as a cfg key.

**4. Weights: attributes vs flat lists.** Keras hands weights back as a flat list of arrays, so the soft
target update becomes list surgery (`[w * tau + tw * (1 - tau) for w, tw in zip(get_weights(), ...)]`
then `set_weights`). PyTorch modules expose named parameters you iterate and mutate in place. Same
math, different idiom — and exactly what `CLAUDE.md` means by **"port logic, not framework"**: write
the PyTorch version of the *idea*, don't reproduce Keras's list-of-arrays dance.

**5. Layer shapes are declared, not inferred.** Keras infers input size on first call, hence the
reference's `self.actor_model(tf.zeros([1, self.num_states]))` warm-up lines. PyTorch requires
`nn.Linear(in_features, out_features)` up front, so those warm-up calls — and the `set_weights` copies
that depend on them — disappear in the port.

Easy to misread: Keras passes `training=True/False` per call, PyTorch sets it as module state via
`model.train()` / `model.eval()`. For the plain MLPs here it changes nothing — but worth knowing *why*
the `training=` arguments vanish rather than assuming something was dropped.

---

## What this track does not cover

- **SAC** — replaces the deterministic actor with a squashed Gaussian plus entropy regularisation. A
  bigger change than DDPG, which is TD3 minus the three tricks and nearly free once TD3 exists.
- **PPO** — the on-policy algorithm the Isaac Lab track actually uses. Track 3.
- **Autograd internals** — what the graph looks like, and `detach()` in detail.
- **Vectorized envs and the buffer/driver rework they need** — Track 3, and
  [`../strategy.md`](../strategy.md) Part 3.
- **The toolkit's own structure** — registry, config, ABC, the SINDy variants. Track 2.

Deeper reference: `_reference/TD3_Robotic_Arm_RL_Guide.pdf`.
