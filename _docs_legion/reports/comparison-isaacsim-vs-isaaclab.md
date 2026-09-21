# Two ways to connect the toolkit to the digital twin — a comparison

**2026-08-29.** Both routes work. This is what each costs and what each buys.

- **Route A — bare Isaac Sim.** `_toolkits/toolkit-isaacsim/`. Isaac Sim's Python API only.
- **Route B — Isaac Lab + Docker.** `_toolkits/toolkit-isaaclab/`. Alvika's container, Martin's task.

## Read this before the numbers

**The two routes are not solving the same task.** Route B runs Martin's task as written: ~10 shaped
reward terms across 1140 lines, tuned together. Route A runs a **simplified task I wrote** — same
robot, same door joint, same 6+1 actions, but a three-term reward (approach / opening / effort).

So this comparison is valid for **throughput, code size, dependencies and operational cost**. It is
**not** valid for learning performance, and no conclusion of the form "route X learns better" can be
drawn from anything here. Neither route has been shown to learn the door task at all.

## Head to head

Matched conditions: single environment, 2 episodes × 40 steps, RTX 5090, TorchTD3 on `cuda`.

| | Route A (bare Isaac Sim) | Route B (Isaac Lab + Docker) |
|---|---|---|
| Throughput, 1 env | **148–151 steps/s** | 15–17 steps/s |
| Throughput, best measured | 148–151 (1 env only) | **~419 env-steps/s** (64 envs) |
| Parallel environments | 1 | 1 → 128 tested |
| Observation dim | 35 (mine) | 43 (Martin's) |
| Action dim | 7 | 7 |
| Code I had to write | **345 lines** | 248 lines |
| Task definition depended on | none — written from scratch | **1140 lines** (Martin's, reused) |
| Disk footprint | 18 GB | 34.7 GB image (+23 GB base) |
| Startup to first step | ~15 s | ~20 s + container |
| Runs without Docker | **yes** | no |
| GUI available | **yes, verified** | awkward from container |

### The single-environment number is misleading on its own

Route A looks ~10× faster per step at 1 environment — but that gap is mostly Isaac Lab's per-step
management overhead, which exists precisely because it is doing the work that makes *many*
environments possible. Route B at 64 environments reaches ~419 env-steps/s, roughly 3× Route A's
best, and it can go further. **Route A cannot be scaled without writing the parallelism myself**,
which is the single largest piece of work Isaac Lab is doing.

### Why that matters more than it appears

`warmup_size` is 2500: TD3 collects random transitions and does not train until the buffer holds
that many. At 1 environment, a 40-step episode contributes 40 transitions. **Route A as it stands
cannot practically reach the start of learning.** Route B at 128 environments contributes 5120 per
episode and clears warmup immediately.

For *validating plumbing*, single-environment is fine. For *training anything*, it is not.

## Where each route's effort goes

Route A's 345 lines are not equivalent to Route B's 248. Route B's 248 lines are glue; the actual
task — scene, observations, ten reward terms, resets, terminations, randomisation — comes from
Martin's 1140 lines, already written and debugged. Route A has no such foundation: my 345 lines
implement a *far simpler* task and would need to grow substantially to match, plus everything Isaac
Lab provides for free (parallel envs, config-driven task composition, the rl_games/RSL-RL/skrl
integrations, tooling).

Realistically, matching Martin's task through Route A means reimplementing most of those 1140 lines
and then the parallelism on top.

## What Route A genuinely buys

1. **No Docker.** Runs directly. Simpler mental model, fewer moving parts, no mounts.
2. **A working GUI.** Verified: launches in ~16 s, RTX renderer active. This is the better route for
   *looking at* the twin, which is a real need distinct from training.
3. **Full control, no framework conventions.** If Isaac Lab's manager abstraction ever fights a
   requirement, this route has no such constraint.
4. **Closer to a hardware-style control loop.** Worth remembering if the real Ridgeback + UR5e is the
   eventual target: Isaac Lab's vectorised, manager-based structure does not map onto one physical
   robot as directly as a plain step loop does.

## What Route B genuinely buys

1. **Parallelism**, which is the whole reason to use Isaac Sim for RL, and the thing Route A lacks.
2. **Martin's task, as written** — 1140 lines of tuned reward shaping reused rather than reinvented.
3. **A reproducible environment.** Version-pinned in `.env.base`; the same image runs for everyone.
4. **A generalising bridge.** The same adapter drove four built-in Isaac Lab tasks unchanged
   (obs 4→60, actions 1→8) — see [`isaaclab-builtin-tests-2026-08-29.md`](isaaclab-builtin-tests-2026-08-29.md).

## Recommendation

**Keep both, for different jobs.** They are not competing.

- **Route B for training.** It has the parallelism, the real task, and the reproducible environment.
  It is the only one of the two that can currently reach the start of learning.
- **Route A for looking, learning and experimenting.** GUI exploration, understanding the scene,
  trying ideas without container overhead, and as the natural starting point if real hardware becomes
  the target.

The strongest argument against making Route A the primary path is not throughput — it is that
matching Martin's task means rewriting ~1140 lines of working, tuned code, and then writing the
parallelism Isaac Lab already provides.

## The one change that would help both

Action selection is one forward pass per environment, in a Python loop. Route B's throughput plateaus
past ~16 environments because of it, and Route A would hit the same wall the moment it gained
parallelism. A `batch_action` method on the agent — one batched forward pass for N states — is the
highest-value next change, and it is a change to the toolkit itself rather than to either adapter.

## Caveats on these measurements

- 2 episodes per configuration. Per-episode variance was large (419 then 134 env-steps/s at 64
  envs), so treat throughput as order-of-magnitude.
- The driver seeds from wall-clock time, so nothing here is reproducible run to run.
- Route A's observation vector (35) differs from Route B's (43) because I assembled it myself; they
  are not the same observation.
- No learning was measured on either route.
