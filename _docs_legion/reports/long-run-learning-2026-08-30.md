# Do the two routes actually learn? — multi-hour runs, 2026-08-30/31

The question left open by every earlier result: the toolkit *drives* the digital twin through two
stacks, but does anything **learn to open the door**?

**Answer: no. Neither route learned the task, and we now know why.** The reason turned out to be
worth more than a learning curve would have been.

---

## Headline

| | Bare Isaac Sim (base actuated) | Isaac Lab + Docker (Martin's config) |
|---|---|---|
| Episodes | ~1,610 | ~210 × 64 envs |
| avg-20 reward | 105.8 → **334.3** (peak 338.4) | 5.85 → **9.38** |
| Plateaued at | ~episode 400 | immediately |
| Door ever opened | 2 of 162 sampled episodes (1.2%) | **never** |
| Trained policy replayed | **door never moves, 6/6 episodes** | — |

The direct route's reward **tripled**, which looks like learning and is — but not of the task. It
learned to approach and align with the handle, which is what the un-gated reward terms pay for. The
door-opening terms contributed essentially nothing.

## The decisive test

A rising reward curve is not evidence of task success. So the trained policy was reloaded and
replayed deterministically (`train=False`, no exploration noise), six episodes:

```
ep0: door never moved
ep1: door never moved
ep2: door never moved
ep3: door never moved
ep4: door never moved
ep5: door never moved
```

**The 2 door-openings during training were exploration noise, not policy.** TD3 adds random noise to
actions while training; occasionally that noise shoved the door. The peak recorded — exactly
3.1416 rad, i.e. precisely the hinge's −180° limit — is the signature of the door being knocked to
its stop rather than pulled open.

This matters beyond bookkeeping: the brief forbids **brute-force pushing**. Had this been reported
as "learned to open the door", it would have been both wrong and wrong in the specific way the
project is meant to avoid. Evidence: `_toolkits/toolkit-isaacsim/_isaacsim_notes/policy-replay-verdict.txt`.

## Why the Isaac Lab route was flat

Not an algorithm problem — a **geometry** problem, measured before the runs:

```
handle -> arm base distance                   0.834 m   (UR5e reach ~0.85 m)
closest gripper->handle, 300 random arm poses 0.207 m
closest, 400 poses WITH base translation      0.137 m
```

Martin's `ActionsCfg` exposes `arm_action` and `gripper_action` only — the Ridgeback's three base
DOF are not actuated — and `EventCfg` uses `position_range: (0.0, 0.0)`, so every episode starts
from the same out-of-reach pose. **The gripper cannot get within 20 cm of the handle**, so no policy
can open the door, and the flat 9.38 reward is the correct outcome rather than a failure to train.

Its replay buffer filled to capacity (1,000,000) with transitions that contain no successful
behaviour to imitate.

The direct route was given the three base joints (action dim 7 → 10) precisely because of this
measurement. That is why it could improve at all — and it still did not solve the task.

## What went wrong along the way

Four problems were found and fixed during these runs. Three were mine; one is upstream and affects
everyone.

### 1. Replay-buffer sampling was O(n) — upstream, affects all long runs

`er.py` sampled with `np.random.choice(max_index, size=256, replace=False)`. NumPy implements that
by building and permuting an array of the **whole buffer** on every call:

| buffer | `choice(replace=False)` | `randint` | penalty |
|---|---|---|---|
| 1,000 | 0.40 ms | 0.03 ms | 12× |
| 50,000 | 4.80 ms | 0.04 ms | 112× |
| 200,000 | 19.88 ms | 0.04 ms | 460× |

Caught 1.5 h into the first attempt: the direct route had fallen from 150 to 10.8 steps/s at buffer
56k, the Isaac Lab route from 195 to 21 env-steps/s, with **the GPU idling at 3% while the CPU
pegged** — sampling, not physics or the network, was the bottleneck. Switched to `np.random.randint`
(sampling with replacement, as SB3, CleanRL and the reference TD3 implementation all do). Measured
5–6 ms → 0.050 ms at 60k entries.

**Not Isaac-specific.** This throttles every sufficiently long run in the toolkit, including the
published Gymnasium results. Short runs never fill the buffer enough to notice.

### 2. Half the ported reward was silently dead — mine

`left_inner_finger` and `right_inner_finger` report the **same world transform as `wrist_3_link`** —
verified through `XFormPrim`, `RigidPrim`, and USD's own `ComputeLocalToWorldTransform`, and
confirmed to move with the arm but never to separate from the wrist. Martin's straddle test is
`lfinger_z > handle_z AND rfinger_z < handle_z`; with identical values that is `x > h AND x < h`,
false for every possible input.

That zeroed `align_grasp_around_handle` and `approach_gripper_handle` — and because the three
opening terms are **gated on the grasp state**, every door-opening term was permanently zero too.
The first overnight run had *no gradient toward opening the door at all*. Replaced with a
TCP-height proxy that actually varies with behaviour.

### 3. Neither training script logged reward — mine

The agent writes its own critic/actor losses, but reward logging lives in the toolkit's driver,
which both integration scripts bypass with their own loops. An 8-hour run would have produced loss
curves and **no learning curve**. Caught by a 12-episode pilot before committing the night. Both
scripts now log episode reward, a 20-episode average, door angle (per-episode and best), buffer size
and throughput.

Logging **door angle** rather than only reward is what made the final diagnosis possible: reward
rose while door angle stayed at zero, which is exactly the signature of optimising the shaped terms
without solving the task.

### 4. A `.gitignore` pattern hid a source directory — mine

`_toolkits/**/buffers/`, intended for replay-buffer `.npy` dumps under `results/`, also matched
`jlab_opt_control/buffers/` — the source package. The buffer fix would not commit, and the package
had never been in git at all. Same class of mistake as an earlier `rsync --exclude='buffers'` that
deleted that same directory: a pattern aimed at data that also caught code.

## What this establishes

**Established:**
- The toolkit trains against the digital twin through both stacks, on GPU, for hours, unattended.
- Reward optimisation works — the direct route tripled its reward and converged cleanly.
- The door task **as currently configured is not solvable**, and the reason is measured, not guessed.
- Two real toolkit bugs found (buffer sampling; and see
  [`PUBLICATION_MATERIALS_legion.md`](../PUBLICATION_MATERIALS_legion.md) for the packaging and
  TF/triton ones).

**Not established:**
- That TD3 can learn this task. It has not been shown to, on either route.
- Any comparison of *learning* between the routes. They differ in action space (7 vs 10),
  observation vector (43 vs 35), and reward fidelity (13 terms vs 8, two of which were broken for
  the first run).

## What would need to change before trying again

1. **Make the handle reachable.** Either actuate the base in Martin's task, or move the robot's
   start pose within arm's reach. This is the blocker; nothing else matters until it is fixed, and
   it is a question for Martin.
2. **Fix the fingertip transforms**, or agree a substitute. The grasp-detection chain depends on
   them, and the opening rewards are gated behind it.
3. **Randomise the start pose.** `position_range` is `(0.0, 0.0)`; every episode is identical, so
   there is nothing to generalise over — already on the project roadmap.
4. **Expect a long horizon.** Approach → align → straddle → grasp → pull 180° is a deep chain for
   TD3 from sparse gated rewards. Even correctly configured, this may need curriculum, demonstrations,
   or a different algorithm. The existing `rl_games` PPO baseline is the natural comparison and has
   not been run here.
5. **Batched action selection** (`batch_action` on the agent) before any serious scaling — still the
   highest-value toolkit change.

## Artifacts

| | |
|---|---|
| Direct-route training log | `_toolkits/toolkit-isaacsim/_isaacsim_notes/run3-training-log.txt` |
| Isaac Lab training log | `_toolkits/toolkit-isaaclab/isaac_integration/run3-training-log.txt` |
| Policy replay verdict | `_toolkits/toolkit-isaacsim/_isaacsim_notes/policy-replay-verdict.txt` |
| Reachability measurements | `_toolkits/toolkit-isaacsim/_isaacsim_notes/reachability-*.txt` |
| Fingertip prim evidence | `_toolkits/toolkit-isaacsim/_isaacsim_notes/fingertip-prims-broken.txt` |

TensorBoard event files (144 MB and 701 MB) are **not** committed; the curves are summarised above.
