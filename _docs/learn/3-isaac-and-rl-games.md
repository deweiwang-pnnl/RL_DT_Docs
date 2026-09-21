# Track 3 — Isaac Sim, Isaac Lab, and the existing rl_games door task

> **What you get:** what the digital twin actually is, the Isaac vocabulary you need and no more, and
> a guided read of the preliminary door task that already exists.
> **Read it against:** `_reference/digital_twin_models-main/` — the USD scene under `AIRoboticsLab/`
> and the seven code files under `RL_CloudTesting/`.
> **Size:** ~210 lines. Part 1 reading; Part 2 is a day at the keyboard.
> **Prerequisites:** [Track 1](1-rl-and-td3.md) for the Gymnasium contract. Track 2 is not required.
>
> **Correction to the source this was built from.** The Jul-24 briefing guide states in its second
> paragraph that "there is **no code** in this package — it is 3D scene + physics data." That was
> wrong, and finding out was the most consequential discovery of 2026-08-03:
> `RL_CloudTesting/` contains a **working Isaac Lab door task with rl_games PPO**. We are adapting
> something, not starting from scratch. Everything in Part 2 below is read from that code.

---

# Part 1 — The twin

## What a digital twin is here

Not a 3D model — a **physics simulation**: geometry (meshes), physics (mass, inertia, collision
shapes, friction, gravity), articulation (joints, drives, limits) and optionally sensors. Because it
obeys physics, an RL agent can take millions of practice attempts safely.

The file format is **USD** (Universal Scene Description), Pixar's open scene format and Isaac Sim's
native language. The property that matters: a large scene is **composed** from many small referenced
files, which is exactly how this twin is built.

**What it models:** a **Clearpath Ridgeback** omnidirectional base carrying a **Universal Robots
UR5e** 6-DOF arm with a **Robotiq 2F-85** parallel-jaw gripper, next to an **Opentrons Flex**
liquid handler whose door the arm must open. Use case #1 in the brief.

## The vocabulary you actually need

1. **Stage / prims / references** — a scene is a tree of prims at paths like `/World/Ridgeback/ur5e/…`.
2. **Articulation** — a jointed robot. You control it through an articulation view: set joint targets,
   read joint position and velocity.
3. **Physics step vs render step** — RL steps physics many times; rendering is optional and expensive.
   This is what `--headless` and `decimation` are about.
4. **`ManagerBasedRLEnv` vs `DirectRLEnv`** — Isaac Lab's two ways to define a task. Ours is
   manager-based.
5. **`num_envs` and domain randomization** — cloning the scene N times for parallel training.

That is the whole list. You do not need to learn USD authoring.

## Requirements, honestly

Isaac Sim is **RTX-only** — it will not run on the Intel Arc laptop this project is largely written
on. It needs an NVIDIA RTX GPU, 8 GB VRAM to load a scene, 16 GB+ to be comfortable, and 24 GB+ for
large `num_envs`. Ubuntu 22.04 is the first-class platform; Windows 11 works for opening and
inspecting a scene and for small experiments. The assets were collected from **Isaac Sim 5.1**
(recorded in `.collect.mapping.json`, author `prat615`, project `LDRD_RoboticsAI`), so use 5.1 or
newer to avoid schema mismatches.

Practical consequence for us: everything in Part 2 can be *read* anywhere; nothing in it can be *run*
without the RTX 5080 workstation. See [`../environment.md`](../environment.md).

## The scene, file by file

Under `AIRoboticsLab/`:

| File | What it is |
|---|---|
| `AIRoboticsLab.usd` (40 KB) | **Top-level scene**, references everything else. Open this one. |
| `experiment.usd` | A second top-level scene. **Which is canonical is an open question.** |
| `SubUSDs/AIRoboticsLab_1.usd` (59 MB) | The lab room. Heaviest visual asset. |
| `SubUSDs/OpenTronsFlex.usd` (28 MB) | The instrument. Contains the **`UpperDoor`** prim — the door. |
| `SubUSDs/RidgebackWithURGripper.usd` | The assembled robot (composition). |
| `SubUSDs/ur5e_base / _physics / _sensor / _robot_schema.usd` | The arm, split by concern. |
| `SubUSDs/Robotiq_2F_85_phyisics_mimic.usda` | Gripper physics with **mimic joints** — one driven `finger_joint`, the others geared to it. The recommended variant. |
| `SubUSDs/Robotiq_2F_85_phyisics_loop.usda` | The same coupling modelled as a closed 4-bar linkage. The alternative. |
| `Defeatured_2F_85_PAD_OPEN_*.usd` | Simplified collision geometry for fast, stable contact physics. |
| `wxai_follower*`, `wxai_leader_*` | A Trossen WidowX-AI bimanual **teleoperation** rig. Bonus asset — relevant only if we want demonstrations for imitation learning. |

**Learn the `_base` / `_physics` / `_sensor` / `_robot_schema` convention** — it is the standard Isaac
modular robot layout and it tells you where to look. To change a motor, edit `_physics`; to read joint
names, open `_physics` or the assembled robot; to add a camera, edit `_sensor`.

The `finger_joint` is the single command that opens and closes the gripper: drive stiffness 3, damping
2e-4, max force 26 N·m, range 0–47°.

## First hands-on

Open `AIRoboticsLab.usd` in the Isaac Sim GUI. In the Stage panel find `Ridgeback`, `ur5e`,
`Robotiq_2F_85`, and `OpenTronsFlex` → `UpperDoor`. Press Play and watch the robot settle under
gravity — if it explodes or sinks through the floor, that is a collision problem to report, not
something to work around. Open the Property panel on the door joint and read its drive stiffness,
damping and limits.

Four capabilities to confirm before anything else: **read joint and door state**, **command joints**,
**step physics**, **reset to a randomized initial pose**.

---

# Part 2 — The door task that already exists

Seven files in `_reference/digital_twin_models-main/RL_CloudTesting/`, 1,756 lines total. Everything
below is **read from the code, not run** — I have no RTX GPU. Treat the numbers as verified and the
behaviour as unverified.

| File | Lines | What it is |
|---|---|---|
| `ur5e_door_open_env_cfg.py` | 545 | Scene, observations, actions, 20 reward terms, terminations, sim settings |
| `ur5e_door_open_mdp.py` | 595 | The reward/observation/termination functions themselves — 31 of them |
| `ur5e_door_open_task.py` | 26 | `gym.register` for `Isaac-UR5e-DoorOpen-v0` |
| `rl_games_ppo_cfg.yaml` | 81 | The PPO hyperparameters |
| `train_rl_games.py` | 258 | Training entry point |
| `play_rl_games.py` | 243 | Checkpoint playback |
| `ReadMe.txt` | 8 | The two commands, which `CLAUDE.md` § How to run reproduces |

## Read it in this order

**1. `ur5e_door_open_task.py` (26 lines, five minutes).** The whole registration:
`gym.register(id="Isaac-UR5e-DoorOpen-v0", entry_point="isaaclab.envs:ManagerBasedRLEnv",
kwargs={"env_cfg_entry_point": UR5eDoorOpenEnvCfg, "rl_games_cfg_entry_point": <yaml>})`. Note
`disable_env_checker=True`. This is the same registry idea as Track 2's toolkit and as `gym.make` —
Track 1's point that Isaac Lab implements the Gymnasium interface without being part of Gymnasium's
collection is *this line* of code.

**2. `UR5eDoorOpenEnvCfg.__post_init__`, at the bottom of the env cfg.** The concrete task shape:

- **Actions** — `JointPositionActionCfg` on the 6 arm joints (`scale=0.5`, `use_default_offset=True`)
  plus `BinaryJointVelocityActionCfg` on the gripper (open `+1.0`, close `−1.0`). So the policy
  commands joint position targets, not torques, and the gripper is binary rather than continuous.
  **The Ridgeback base is not in the action space.**
- **Observations** (`concatenate_terms=True`, `enable_corruption=True`): arm `joint_pos_rel`,
  `joint_vel_rel`, door joint position and velocity, `rel_ee_handle_distance`, `last_action`, and a
  flag-gated `door_open_progress`. Privileged simulator state throughout — **no vision, no force,
  no torque, no contact flags.**
- **Timing** — `sim.dt = 1/60`, `decimation = 2`, `episode_length_s = 20.0`. So the policy acts at
  30 Hz for **600 steps per episode**.
- **Scene** — `num_envs=512`, `env_spacing=2.5`, with `FrameTransformerCfg` supplying the
  end-effector and handle frames the distance rewards need.

**3. `RewardsCfg` — 20 terms, and read the weights.** They form a scripted sequence: approach the
handle (1.2), approach from the robot side (1.5), align (1.0), pre-grasp orientation (2.0), approach
the gripper (4.0), align the grasp around the handle (2.0), grasp (5.0), gated door-open fraction
(2.0 and 2.5), multi-stage open (2.5), ungrasp after open (1.5), return home (2.0), sequence
completion bonus (2.0), and two penalties — moving the door while ungrasped (−6.0) and levering under
the door (−4.5). Then six `script_guided_*` terms: a phase gate, a grasp-phase bonus (1.2), arc handle
tracking (1.4), a grip-slip penalty (−2.5), a base `dof0` profile reward (0.4), and trajectory
tracking (2.0). Finally two generic regularizers: `action_rate_l2` (−0.005) and `joint_vel_l2`
(−0.001).

**4. `ur5e_door_open_mdp.py`** — the 31 functions behind those terms. Read
`door_open_fraction`, `grasp_state_gate`, `sequence_completion_bonus` and
`script_guided_trajectory_tracking_reward` (with its `_interp_piecewise` helper), in that order. This
file is where the task design actually lives.

**5. `TerminationsCfg`** — two terms: `time_out` (`time_out=True`, so it surfaces as
**`truncated`**) and `sequence_complete` (a real **`terminated`**). Good news for Track 1's
distinction: unlike Pendulum, this task genuinely terminates, so the `(1 − done)` factor is live code
here and getting it wrong would matter.

**6. `rl_games_ppo_cfg.yaml`** — `a2c_continuous` / `continuous_a2c_logstd`, an `actor_critic` MLP
`[256, 128, 64]` with `elu`, **shared trunk** (`separate: False`), `fixed_sigma: True`. Config:
`gamma 0.99`, `tau 0.95` (this is GAE-λ, *not* the Polyak τ from Track 1 — same letter, different
thing), `learning_rate 1e-3` with `lr_schedule: adaptive` and `kl_threshold 0.01`, `e_clip 0.2`,
`entropy_coef 0.01`, `horizon_length 32`, `minibatch_size 32768`, `mini_epochs 5`,
`normalize_input`/`normalize_value`/`value_bootstrap` all true, `max_epochs 2000`, `seed 42`.

Two things to notice, because they connect to what you already know. `value_bootstrap: True` is
rl_games doing exactly what Track 1 says must happen at a time limit — bootstrapping the value
function through truncation instead of zeroing it. And `seed: 42` is fixed here, which the reference
toolkit never manages.

## Four things to verify while reading — with what I suspect

I have not run this, so these are **checks, not findings**. Confirm each before building on the task.

1. **The batch/minibatch arithmetic.** rl_games builds a batch of `horizon_length × num_actors`, where
   `num_actors: -1` resolves to `num_envs`. The ReadMe's command uses `--num_envs 256`, giving
   32 × 256 = **8,192**, against a `minibatch_size` of **32,768** — four times larger than the batch.
   The cfg's own `num_envs=512` gives 16,384, still half. `num_envs = 1024` is the value that makes it
   come out exactly. Check whether rl_games errors, silently clamps, or the ReadMe command was never
   the one actually used.
2. **Zero domain randomization.** `EventCfg` has one term, `reset_joints_by_offset`, with
   `position_range: (0.0, 0.0)` and `velocity_range: (0.0, 0.0)`. Every episode starts from the
   identical pose, so **nothing in the brief's "variable geometry" requirement is exercised yet** and
   a trained policy has no reason to generalize. This is the single largest gap between this task and
   the project's stated goal.
3. **A reward term for a joint the policy cannot command.** `script_guided_base_dof0_profile_reward`
   (weight 0.4) shapes a base degree of freedom, but the action space contains only the 6 arm joints
   and the gripper. Either the base is actuated somewhere I have not found, or this term rewards
   something the policy has no way to affect. Verify against a live run.
4. **No force or torque anywhere.** Not in the observations, not in the rewards, no `ContactSensor` in
   the scene cfg — only `FrameTransformerCfg`. The brief explicitly requires "no brute-force pushing",
   so a force/torque penalty is a *missing requirement*, not a refinement. It is on the roadmap in
   `CLAUDE.md` and it is why the tactile-data question matters in
   [`../team-discussion.md`](../team-discussion.md).

And the design judgement to form your own view on: **the reward is heavily script-guided.** Six terms
track a reference trajectory and several more gate on sequence phase. That will very likely produce a
door-opening motion, and it is close to imitating a scripted plan under a policy's name. Reducing that
dependence is a medium-term roadmap item; decide for yourself where the line sits between shaping and
telling.

## What is genuinely undocumented

Nothing in this project explains **rl_games itself** — its `a2c_continuous` implementation, how
`horizon_length` and `mini_epochs` interact, how it wraps a vectorized Isaac Lab env, or what its
checkpoint format is. `train_rl_games.py` and `play_rl_games.py` (258 + 243 lines) are the local
entry points and worth reading for the wrapper boilerplate, but the library is upstream. Read it at
its own repo when you need it. This is a real gap, stated rather than papered over.

---

## What this track does not cover

- **PPO as an algorithm.** Track 1 covers off-policy TD3; PPO is on-policy, with a clipped surrogate
  objective and GAE, and nothing here teaches it. If you only read one thing, read why `e_clip` and
  `entropy_coef` exist.
- **Installing Isaac Sim / Isaac Lab** — needs the workstation; see [`../environment.md`](../environment.md).
- **Vectorized envs on the agent side** — how a 512-env batched GPU tensor changes the driver and
  replay buffer: [`../strategy.md`](../strategy.md).
- **The task's assignment and research framing** — [Track 4](4-door-task.md).
- **The open questions** these files raise: [`../team-discussion.md`](../team-discussion.md).
