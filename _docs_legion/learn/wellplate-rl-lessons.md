# Learning package — the well-plate round (2026-09-22 → 09-28)

What this round did, and the concepts you need to own it: to explain it to the team, to change it, and to judge the
next result. Seven parts; each has **the idea in one paragraph**, **what happened in our project**, **where it is in
the code**, and **check yourself** questions (answers at the end). Slides with the same structure:
[`slides.html`](slides.html). Paths starting `WellPlate_RL/` are in `RL_DT/_isaaclab_wellplate/`.

| Part | Topic | Why it matters here | Time |
|---|---|---|---|
| 0 | What was done — one page | the map | 5 min |
| 1 | How an Isaac Lab task is built | every fix this round was in one of its six managers | 30 min |
| 2 | Robot, gripper, contacts, gravity | the lift blocker; the realistic arm | 30 min |
| 3 | PPO as we actually use it | normaliser, reward scaling, truncation, learning rate — four of our bugs | 45 min |
| 4 | Measuring honestly | deterministic evaluation, diagnostics, A/B tests | 20 min |
| 5 | Curricula and skills | how the hard tasks became learnable | 40 min |
| 6 | Other RL libraries | what E5 compared and what it did not settle | 20 min |
| 7 | Answers, glossary, further reading | | lookup |

---

## Part 0 — What was done, on one page

```
09-21  lift 0 % ──► 09-26  gripper fixed (4 defects) ──► align 82 · lift 87.5 · stack 50.8 %
                                   │
                                   ▼
09-27  centred stack (5 mm / 3° / 3°) 90.6 %  ◄── twist observation · tolerance curriculum · release bonus
                                   │
                                   ▼
09-27  three plates:  hand-off 52.3 · all loose 46.1 · loose bottom 49.2 · realistic arm 54.7 %
                      ◄── two skills · rising stack · hand-off start states · mass curriculum · gravity compensation
                                   │
                                   ▼
09-28  libraries: Reach easy for all GPU PPOs; Align from scratch only skrl PPO (98.4 %), reason open
```

The pattern that repeated all round: **a result fails → measure where it fails (per episode) → name one cause →
change one thing → measure again.** Every step is in [`PROGRESS.md`](../evidence/wellplate/PROGRESS.md).

---

## Part 1 — How an Isaac Lab task is built

**The idea.** A manager-based Isaac Lab environment is a scene plus a set of managers (five in our tasks; Isaac Lab also
has command, curriculum and recorder managers we do not use). The *scene*
holds assets (robot articulation, rigid objects, sensors). Each step the **action manager** turns the policy's output
into joint targets; physics runs `decimation` substeps; then the **termination manager** decides who is done, the
**reward manager** sums weighted terms, the **event manager** resets finished environments, and the **observation
manager** builds the next input. Every term is a small function `f(env, **params) → tensor(num_envs, …)` referenced
from a config class. Tasks differ only in which terms and parameters they list — so warm-starting a policy from one
task to the next works when the observation and action layouts stay the same.

**In our project.** Every stage (Reach, Align, Lift, Stack, Centered, Stack3*) is a config subclass of the one before;
the observation stayed identical (215 inputs after the twist term was appended **last**, so old checkpoints could be
widened with zero weights). For three plates we did not rewrite any term: three read-only stand-ins (`mover`, `base`,
`lower`) were added to the scene, and every term's `SceneEntityCfg("plate")` was remapped to `"mover"`.

**Where.** `WellPlate_RL/source/WellPlate_RL/WellPlate_RL/tasks/manager_based/wellplate/`: `scene.py` (assets,
constants, `VIEWS`), `base_env_cfg.py` (actions, observations, events, terminations), `*_env_cfg.py` (one per stage),
`mdp/` (the term functions), `__init__.py` (task ids + agent config entry points), `agents/` (per-library configs).

**Check yourself.**
1. A term function is called with `env` — why must it return one value per environment rather than a scalar?
2. Why was the new observation term appended at the *end* of the list?
3. Terminations are computed *before* rewards in a step. Which of our functions depends on that order?

---

## Part 2 — Robot, gripper, contacts, gravity

**The idea.** A robot is an *articulation*: links connected by joints, solved together by PhysX. Joints we command get
*actuators*; ours are **implicit PD drives** (`stiffness`, `damping`): PhysX pulls each joint toward its target like a
spring. A parallel gripper such as the Robotiq 2F-140 is a **four-bar linkage**: one driven joint, the rest follow
through *mimic* constraints and loop-closing joints — command a loop joint wrongly and the linkage fights itself.
Contacts are governed by **contact offset** (where contact starts being generated), **rest offset**, **max
depenetration velocity** (how hard overlaps are pushed apart) and solver iterations; wrong values let fingers sink into
or fling objects. **Gravity compensation**: a real UR controller adds the torque G(q) that holds the arm against gravity
at configuration q; PhysX can compute G(q) (inverse dynamics), and implicit actuators pass extra "feed-forward" efforts
straight to the joints.

**In our project.**
- The lift blocker: the pad joint (a loop-closing joint in the USD) was driven to 0 because the URDF joint of the same
  name is a fixed mount → pads in a V; plus grasp height, closing axis, and contact settings (Isaac Lab's own 2F-140
  values fixed the "pads sink through the plate" behaviour). 16/16 grasps after the fix.
- A test that **teleports** a body every step (`write_root_pose_to_sim`) overrides the solver; the 09-20 "no colliders"
  conclusion came from such a test and was wrong.
- Robot gravity was off during training (the stiff-but-uncompensated arm stalled 0.3–0.4 m short). With G(q) added every
  physics step the gravity-on arm tracks exactly like the gravity-off arm (0.0 mm vs 434 mm uncompensated), and the
  trained policies transferred unchanged.

**Where.** `scene.py` (gripper variants G0/G1/G2, `REFERENCE_PHYSICS`, `GRIPPER_ACTUATORS`, `ROBOT_CFG`),
`mdp/mimic_gripper.py`, `robot_spawner.py`, `mdp/gravity_comp.py` (`GravityCompDiffIKAction`), `realistic_arm.py`,
probes `scripts/probe_gripper_sweep.py`, `probe_arm_tracking.py --arm {default,on,comp}`.

**Check yourself.**
4. Why does an overdamped PD arm (400 / 80) with gravity on but no compensation end up *short* of an IK target,
   rather than oscillating around it?
5. Why is "teleport the plate between the fingers and see if it falls" not a valid grasp test?
6. The compensation torques are recomputed every *physics* step (120 Hz), not every *policy* step (30 Hz). Why?

---

## Part 3 — PPO as we actually use it

**The idea.** PPO collects a rollout (here 24 steps × 512 environments), estimates **advantages** with GAE from a learned
value function (the *critic*), and updates the policy several epochs over minibatches while **clipping** the
probability ratio (0.2) so no update moves too far. The policy is a Gaussian: the network outputs a mean action, a
learned **action std** sets the exploration noise; entropy bonus keeps it from collapsing. Four practical details
decided whole stages this round:

1. **Observation normalisation.** rsl_rl standardises inputs with running statistics: `(x − mean) / (std + 0.01)`. An
   input that never varied during training has std ≈ 0, so any new value there becomes a huge input.
2. **Rewards are scaled by the step time.** Isaac Lab multiplies each term by `weight × dt` (dt = 1/30 s). A one-off
   bonus of weight 50 pays 1.7.
3. **Termination vs truncation.** A *termination* (e.g. plate dropped) means "no future reward". A *truncation*
   (`time_out=True`: time limit, and our success terms) means "the episode was cut, the future still had value" —
   rsl_rl adds γ·V(s) to the last reward. So succeeding does not forfeit the dense reward stream, but then the **success
   bonus is the only net gain from finishing** — and it must be large compared with the critic's error.
4. **Learning rate schedule.** rsl_rl's KL-adaptive schedule divides the rate by 1.5 whenever a minibatch's KL exceeds
   2 × the target; in our tasks it sat at its 1e-5 floor, so the policy could polish but not learn new behaviour.

**In our project.**
- (1) Three-plate attempt 1: a 180°-flipped base plate's quaternion (the same plate!) became a ~100σ input. Fix: report
  symmetric quantities in a canonical form (either end, either sign).
- (2)+(3) Centred C1a: the policy placed the plate and held it forever — bonus 1.7 vs critic noise ±5–7. Bonus 600 →
  1.6 % → 67 %.
- (3) Isaac Lab's `is_terminated_term` masks truncations, so our success bonus had paid 0 in every stage until 09-26
  → own `success_reward`.
- (4) Fixed learning rate 1e-4 for the centred runner. (In E5 a fixed rate did *not* explain rsl_rl vs skrl — don't
  over-generalise one finding.)
- Action std grew 1.0 → 3.7 across stages because actions are clipped to ±1 (a wide std costs nothing) → entropy
  0.01 → 0.001 and std reset at warm starts.

**Where.** `agents/rsl_rl_ppo_cfg.py` (all PPO settings), `mdp/wellplate_mdp.py: success_reward`, `stack_env_cfg.py`
and `centered_env_cfg.py` (reward weights with the reasons in comments), `scripts/reset_action_std.py`,
`set_checkpoint_lr.py`, `widen_obs_checkpoint.py`, `swap_normalizer.py`.

**Check yourself.**
7. With success as a truncation, what exactly is the value difference between "release now (success)" and "keep
   holding one more step"?
8. Why did the goal-pose inputs have zero variance during C3 training?
9. Why can a wide action std be free when actions are clipped to ±1 — and why did it hurt the binary gripper?

---

## Part 4 — Measuring honestly

**The idea.** Training curves show success **with exploration noise**; the policy you deploy acts on its mean. For a
binary gripper the noise opens the grip at random, so training success can fall while the real policy improves. The
reported number must come from a **separate deterministic evaluation** with enough episodes (128 here; one standard
deviation ≈ 4.4 points at 50 %). When something fails, look at **per-episode final states** (where was the plate, was
it held, how far off) rather than averages, and test hypotheses with **A/B swaps** that change exactly one thing.

**In our project.**
- Every gate used `eval_policy.py` (deterministic, 128 episodes). Lift: training 19.9 %, deterministic 87.5 %.
- `--diag_stack` per-episode diagnosis found "placed but held" (C1a), "never picks up" (E1 run 3), "released askew
  next to the stack" (B1).
- **Swap test** (E1 run 2): C3 weights + new normaliser 93 %; new weights + C3 normaliser 3.9 % — so it was the weights.
- `--track_switch` measured the hand-off: placed plate moved > 5 mm within 5 steps in 61 % of envs.
- Probes before training (grasp gate 16/16, multi-plate checks, arm tracking) caught setup bugs cheaply.
- A hypothesis that looked convincing (rsl_rl's learning rate explains the E5 gap) was tested and **rejected**; the
  write-up says so.

**Where.** `scripts/rsl_rl/eval_policy.py` (`--diag_stack`, `--checkpoint2`, `--track_switch`),
`record_labelled.py` (captioned videos), `scripts/probe_*.py`, `swap_normalizer.py`, [`PROGRESS.md`](../evidence/wellplate/PROGRESS.md) (decisions with
evidence), chart [`results/2026-09-28_presentation/T1_training_curves.png`](../evidence/wellplate/results/2026-09-28_presentation/T1_training_curves.png).

**Check yourself.**
10. A stage's training success falls from 80 % to 30 % while its deterministic evaluation rises. Name two mechanisms.
11. What would you change in the swap test if the result had been "both hybrids ~50 %"?

---

## Part 5 — Curricula and skills

**The idea.** RL learns from reward it actually receives. If the goal is too hard, nothing is ever rewarded and the
policy has no gradient toward it; if a new task is mixed with an old one it can **overwrite** the old skill
(catastrophic forgetting) or learn to **avoid** the activity that keeps failing. Three tools:
- **Curriculum**: start where success happens, then tighten one knob in steps, each gated (tolerance, geometry, mass).
- **Separate skills**: keep a skill that works as its own policy; train the new part as a second policy.
- **Skill chaining with start states**: train the next skill from the states where the previous skill actually hands
  over, not from a convenient reset.

**In our project.**
| Problem | Tool | Result |
|---|---|---|
| At 10° twist nothing was rewarded | tolerance curriculum 45° → 3° | C3 90.6 % |
| One policy for both placements forgot the first / stopped grasping | two skills | first-placement skill untouched |
| Second placement at full stack height: 0.8 % | rising stack: a kinematic middle plate inside the bottom plate rising 0 → 26 mm | 91.4 % at full height |
| Second skill dragged the placed plate at the hand-off | 2000 recorded hand-offs as start states + displacement penalty | E1 52.3 % |
| Loose 50 g bottom plate: first skill collapsed | mass curriculum 20 kg → 50 g + displacement penalty | 61.7 % → E3 49.2 % |

Note the **physically impossible** training scenes (a plate inside another): allowed for shaping, never for the
numbers that count — every gate used real dynamic plates.

**Where.** `run_centered.sh` (tolerance stages), `run_skills.sh` (rising stack, B2, E2), `run_e3.sh` (mass stages),
`mdp/multi_plate.py` (`reset_multi`, `stack_height`, `bank_prob`, `lower_displacement`, `bottom_displacement_penalty`),
`data/handoff_bank.pt`, `eval_policy.py --save_handoff_bank`.

**Check yourself.**
12. Why did the rising stack start at 0 mm rather than, say, 10 mm?
13. What goes wrong if the hand-off bank is recorded with a *different* first-placement policy than the one used at
    evaluation?
14. Why is a displacement *penalty* needed when success already requires the lower plate to stay in place?

---

## Part 6 — Other RL libraries

**The idea.** Isaac Lab wraps four libraries behind the same task ids: rsl_rl (on-policy PPO, GPU-native, Isaac Lab's
default), skrl (PPO, SAC, TD3, …; YAML configs), rl_games (PPO, very fast), Stable-Baselines3 (general-purpose,
CPU-oriented policies with a vectorised-env wrapper). Each has its own config vocabulary, logging tags and checkpoint
format; a fair comparison needs the same env steps, network, and **one shared evaluation**.

**In our project.** Reach from scratch: rsl_rl, skrl, rl_games PPO 100 % (11–14 min). Align from scratch: only skrl PPO
(98.4 %). Stable-Baselines3 (fixed rate + KL early stop) and skrl SAC (one update per 512 env steps) learned neither —
under-powered settings, not a verdict. Single seeds; the skrl advantage is unexplained (next test: value-target
normalisation, which skrl has and rsl_rl does not).

**Where.** `agents/*_cfg.yaml`, `scripts/{skrl,rl_games,sb3}/{train,play}.py` (Isaac Lab's scripts + our task import +
`--eval_episodes`), `scripts/eval_common.py`, `run_libs.sh`, `run_libs2.sh`, [`results/2026-09-27_libs/`](../evidence/wellplate/results/2026-09-27_libs/).

**Check yourself.**
15. Why is "the same number of iterations" not a fair budget across libraries, and what did we use instead?
16. SAC with 512 environments and one gradient step per environment step: how many updates per million samples?

---

## Part 7 — Answers, glossary, further reading

### Answers
1. Everything is batched over thousands of environments; managers weight, sum and reset per environment.
2. So an old checkpoint's first layer can be widened with zero weights for the new columns — the old policy is
   unchanged at the start.
3. `success_reward` reads the termination term's value in the same step; `multi_stack_success` performs the phase
   switch before rewards see the state.
4. The PD spring needs an error to produce torque against gravity; the relative IK then takes the sagged pose as the
   next starting point, so the error persists.
5. Teleporting overrides the contact solver every step; friction and penetration are never resolved as in a real grasp.
6. Gravity torque changes with the configuration within a policy step; the compensation must track q at physics rate.
7. Only the bonus (plus the one-step reward difference); the future value is bootstrapped either way.
8. The bottom plate never moved and the robot base was locked, so the goal pose in the robot frame was constant.
9. Clipping hides the std's cost on the arm; for the binary gripper any noise crossing zero flips open/closed.
10. Exploration noise flipping the gripper; a growing action std; single-placement training vs full-sequence evaluation.
11. Suspect both parts, or something else (e.g. the value function / episode structure); test further hybrids.
12. At 0 mm the task equals C3, which already succeeds — the curriculum starts where reward is received.
13. The start-state distribution no longer matches the real hand-off; the second skill meets unfamiliar states.
14. Success is sparse and late; the penalty gives an immediate, graded signal the moment the stack is pushed.
15. An "iteration" means different amounts of data per library; we fixed **env steps** (6.1 M / 12.3 M).
16. About 1 950 updates per million samples (1 000 000 / 512).

### Glossary
| Term | Meaning here |
|---|---|
| Deterministic evaluation | policy's mean action, no noise, 128 episodes — the reported number |
| Truncation / termination | episode cut with / without bootstrapped future value |
| Warm start | continue training from a previous stage's checkpoint |
| Gate | minimum deterministic success before the next stage starts (40 %) |
| Role stand-in | read-only scene object that points to whichever plate plays a role in each env |
| Hand-off bank | recorded robot + plate states at the moment the first skill finished |
| Kinematic body | moved only by code, never by contacts |
| G(q) | joint torques that hold the robot against gravity at configuration q |

### Further reading
- Isaac Lab documentation — manager-based environments, actuators, the RL library wrappers: https://isaac-sim.github.io/IsaacLab/
- Schulman et al. 2017, *Proximal Policy Optimization Algorithms*, arXiv:1707.06347
- Schulman et al. 2015, *High-Dimensional Continuous Control Using Generalized Advantage Estimation*, arXiv:1506.02438
- Andrychowicz et al. 2020, *What Matters in On-Policy Reinforcement Learning?*, arXiv:2006.05990 — normalisation,
  learning rates and other "details" that decided our stages
- Pardo et al. 2018, *Time Limits in Reinforcement Learning*, arXiv:1712.00378 — truncation vs termination
- Bengio et al. 2009, *Curriculum Learning*, ICML
- Konidaris & Barto 2009, *Skill Discovery in Continuous RL Domains using Skill Chaining*, NeurIPS
- Kirkpatrick et al. 2017, *Overcoming catastrophic forgetting in neural networks*, PNAS (arXiv:1612.00796)
- Haarnoja et al. 2018, *Soft Actor-Critic*, arXiv:1801.01290
