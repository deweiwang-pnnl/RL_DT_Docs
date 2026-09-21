# Track 4 — The door task: the assignment and the research framing

> **What you get:** what we were actually asked to do, in the brief's own terms, and the three ways
> this work could become a paper.
> **Read it against:** `_reference/T2_RoboticProjectA.pdf` — the brief itself, which is the authority
> if anything here disagrees with it.
> **Size:** ~220 lines, but Part 1 is a two-page brief — one sitting. Read it **first** if you want
> motivation before mechanics.
> **Prerequisites:** none, though [Track 3](3-isaac-and-rl-games.md) makes Part 3 concrete.
>
> Part 1 is a faithful conversion of the brief and does not go stale. Parts 2–4 are interpretation —
> mine and, in places, dated. Anything marked **[dated]** was written before we read the code.

---

# Part 1 — The brief

*"FAI RL for Robotics", Malachi Schram, June 2026.*

## Problem definition

Robotic automation in scientific lab spaces requires completing tasks in a **human-centric
environment** — manipulating objects and equipment designed for **human hands**, not robotic grippers.
The robot must handle **variable geometries**: slightly different approach angles, different
manipulation orientations, a door handle that is rotated.

The overarching aim: **provide a generalized approach for using reinforcement learning in highly
variable lab spaces using manipulators — mobile or stationary.** Framed as critical for lab-based
automation.

Two example use cases:

1. **Open instrument doors with a mobile manipulator** to move labware between instruments. The doors
   are designed for humans; letting a robot open them enables automated sample runs without human
   intervention. Extends to cupboards and drawers in storage areas.
2. **Grasp falcon tubes and place them in a rack** for liquid-handling instruments. Must work from
   differing start positions and place tubes avoiding collisions, excessive torque and spills.
   Extension: multiple tubes in a specified order.

Use case #1 is what the twin is built for. Use case #2 shares the robot and is the natural follow-on —
the asset already exists at `_reference/digital_twin_models-main/ReinforcementLearning/TubeRacking.usd`.

## Environment

3D training scenes are **physically realistic**, built in Isaac Sim as USD with realistic gravity,
collisions and articulations. Robots can be assembled in any orientation so **task randomization** is
possible. Interacting equipment is customizable per task. End effectors can grip (**with tactile force
sensors**), suction, or imitate a human hand. **RGB cameras and lidar** can be added. Instrumentation
uses realistic scale, geometry and mass; geometry may be simplified for performance — with the caveat
that **enough physical detail must remain that reward hacking cannot bypass physical constraints.**

## State, action, reward — as specified

**Observation components for a manipulator gripper:** end-effector pose; joint angles and velocities;
gripper width / grasp state; pose estimate of the target (6D door position and rotation); target pose
or rack slot; **relative transforms** (target w.r.t. gripper, end goal w.r.t. gripper); **force and
torque at the wrist** (UR has F/T estimation, an external sensor is better); contact indicators and
collision flags.

**Actions:** (1) open the door hinge to *x* degrees using the handle — grab the handle, move the door
along an arc; (2) place a falcon tube in a rack.

**Rewards.** Event bonuses: stable-grasp bonus after N steps, first contact with the slot rim,
insertion achieved, successful release, and a large dominating full-success bonus. Penalties: drop,
collision or self-collision, **force/torque penalty or constraint — the reward must not encourage
brute-force pushing**, and excessive tilt.

**Section 1.2, "Tasks", is blank in the brief.** A placeholder never filled in. That is not an
oversight to route around — it is the single largest piece of missing specification, and it is why
success thresholds and the randomization envelope are still open questions.

## Goal, verbatim in substance

> To provide a **robust framework** for RL development for lab-based automation. A **modular test bed**
> to deploy RL algorithms and provide useful tools to scientists who need to increase data-collection
> capability.

---

# Part 2 — What kind of project this is

**A framework project first, a task project second.** The stated goal is not "solve the glass door" —
it is a modular, robust RL test bed for lab automation, with door-opening and tube-racking as the
first two proving tasks. That framing should drive scoping, code structure, and the paper.

**The generalization requirement is the real point.** The brief stresses variable geometry and task
randomization repeatedly. So the success criterion is not "open one door once" but **open the door
across a randomized distribution of poses and angles.** Domain randomization and robust evaluation
belong in from day one, not bolted on later. Measured against that bar, the existing task's
`position_range: (0.0, 0.0)` reset is the largest gap in the project — see
[Track 3](3-isaac-and-rl-games.md) Part 2.

**Reward hacking is called out explicitly, twice.** Consequences: reward shaping is a first-class
engineering task; **success metrics must stay separate from training reward**; force/torque penalties
and physical fidelity in the sim matter. All three are project rules in `CLAUDE.md` for this reason.

**Who owns what.** The brief is Malachi's; the twin is the DT developer's (`prat615`, project
`LDRD_RoboticsAI`); the RL toolkit is Malachi's group's, written for accelerators. Our job is the
middle: define the MDP, wrap the twin as a trainable env, train and evaluate. Alvika leads the RL
work; Dewei supports.

## The success ladder

A proposal, not an agreed plan — item 4 is where the brief's actual requirement starts.

1. **Reach** the handle, base fixed — proves the env, rewards and logging work at all.
2. **Grasp** the handle stably.
3. **Open** to a target angle from a fixed pose.
4. **Open** under randomized approach angle and handle rotation. ← the real bar
5. Add the **mobile base** (navigate, then manipulate) — only if in scope.
6. A **second instrument or the tube task** — what substantiates the word "framework".

The existing code aims at roughly step 3 with a heavily scripted reward, and commits to a full
sequence (approach → grasp → 10° → 90° → 180° → release → return home). Whether 180° is the intended
success criterion is an open question.

---

# Part 3 — The paper

## Three candidate theses

**(A) Framework + first task.** *"A digital-twin RL framework for human-centric lab automation,
demonstrated on a mobile-manipulator door-opening task with generalization over variable geometry."*
Matches the brief exactly; the contribution is a reusable pipeline plus a hard concrete task. Risk:
framework papers still need a convincing task result, so the door has to work.

**(B) Method paper — physics-informed / interpretable RL for contact-rich manipulation.** *"Injecting
known contact/constraint physics into RL for safe, sample-efficient, interpretable lab
manipulation."* Continues the group's SINDy / LC-TD3 line (Colen 2026) into robotics; strongest
novelty; natural MLST fit. Risk: highest — you must show the physics-informed component beats a strong
baseline, so don't commit before the baseline works.

**(C) Benchmark / empirical study.** *"Benchmarking PPO/SAC/TD3, ± domain randomization, ± physics
priors, on a lab door-opening digital twin."* Lowest risk, always publishable, a natural byproduct.
Lower novelty alone.

**Recommendation:** build so that **(A) is the guaranteed paper, (C) is a section inside it, and (B) is
the upside** you claim only if the result is strong. This makes the paper's ambition follow the
results instead of betting up front. Aligning on this is the main thing to settle with Malachi.

## Skeleton, framing A with the method angle built in

Working title: *A Physics-Informed Digital-Twin Reinforcement Learning Framework for Human-Centric
Laboratory Automation: Mobile-Manipulator Door Opening.*

1. **Introduction** — lab automation needs robots operating human-designed equipment under variable
   geometry; the gap is that general RL frameworks aren't tailored to constrained, contact-rich,
   human-centric lab tasks. Contributions: (i) a modular digital-twin test bed; (ii) an MDP formulation
   with force/torque constraints and variable-geometry generalization; (iii) benchmarked baselines;
   (iv) *if it pans out* a physics-informed interpretable component.
2. **Related work** — RL for manipulation and articulated objects; sim-to-real and domain
   randomization; physics-informed and constrained RL; lab/science automation. Cite Rajput 2025 and
   Colen 2026 as the lineage this extends from accelerators into robotics.
3. **System and digital twin** — the Isaac Sim 5.1 scene, fidelity choices, and the explicit
   anti-reward-hacking rationale.
4. **Problem formulation** — the MDP as specified in Part 1, plus termination and success criteria and
   the randomization envelope that defines "generalization".
5. **Method** — algorithms on parallel Isaac Lab envs; the physics-informed component as an upside
   section; domain randomization and sim-to-real considerations.
6. **Experiments** — learning curves and **success rate over randomized poses** (the real metric);
   ablations on dense vs sparse reward, ± randomization, ± physics prior, algorithm choice; safety
   metrics (peak force/torque, collision rate) showing no brute-force solution; interpretability
   evidence if (B); generalization vs randomization breadth; failure modes.
7. **Discussion** — what transfers to other instruments and tasks; limitations; the sim-to-real gap.
8. **Conclusion** — the test bed as reusable; tube-in-rack; hardware transfer; multi-step workflows.

## What makes it publishable, and where the risk is

The strongest novelty lever is **physics-informed + interpretable** — the group's signature, and what
separates this from a generic "RL opens a door" paper. Gate it on a working baseline. Second lever:
rigorous **generalization over variable geometry with an explicitly force-constrained solution**,
which answers the brief directly and is a clean story. Third: the **released test bed** itself.

Main risk: long-horizon contact-rich manipulation is genuinely hard, so let ambition follow results.
And **reproducibility must be fixed up front** — the reference toolkit is non-reproducible by design,
which is exactly why our own agent takes a `seed` cfg key and why the evaluation-seeding trap in
[`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md) is worth knowing before you generate
results rather than after.

## Minimum results before writing

1. A working baseline that opens the door from a fixed pose — proves the pipeline.
2. A generalization result over randomized approach angle and handle rotation — the headline metric.
3. Constraint evidence: force and torque stayed within limits.
4. *(Upside)* the physics-informed variant beating the baseline on sample efficiency, safety or
   interpretability.
5. All of it with **fixed seeds, ≥3 seeds, reported variance.** Still outstanding — the current
   four-environment comparison is one seed per arm.

---

# Part 4 — What has changed since this was written

**[dated]** The interpretation above was written in July 2026, before any code was read. Two things
have moved:

- **The twin is not asset-only.** A working Isaac Lab door task with rl_games PPO already exists.
  Anything above that reads as "we must build the env from scratch" should be read as "we must adapt
  and fix the env that exists" — [Track 3](3-isaac-and-rl-games.md).
- **The agent side has landed.** A PyTorch TD3 now exists inside the toolkit, tested and matched
  against the Keras baseline on four Gymnasium environments. So the "port the algorithms" line in the
  ladder above is done, and what remains is vectorization and the Isaac integration —
  [`../strategy.md`](../strategy.md).

What has **not** changed: Section 1.2 of the brief is still blank, no success threshold or tolerance
has been set, the randomization envelope is unspecified, the observation modality is undecided beyond
"privileged sim state for now", and whether sim-to-real is in scope is unknown. Those are the decisions
that most change what gets built, and they are the top of
[`../team-discussion.md`](../team-discussion.md).

---

## What this track does not cover

- **The algorithms** — [Track 1](1-rl-and-td3.md).
- **The toolkit the method contribution lives in** — [Track 2](2-toolkit.md).
- **The scene and the existing task code** — [Track 3](3-isaac-and-rl-games.md).
- **Decisions already made and why** — [`../decisions.md`](../decisions.md).
- **The questions themselves, ranked and grouped by who can answer them** —
  [`../team-discussion.md`](../team-discussion.md).
