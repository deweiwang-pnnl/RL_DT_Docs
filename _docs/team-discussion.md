# Team discussion — present · ask · propose

> A handout, not a private note. Part 1 is what I say about the work, Part 2 is what I ask and **who
> can answer it**, Part 3 is what I propose changing in someone else's code.
>
> **Deliberate exception to this repo's linking rule.** The defect table in Part 1 is spelled out in
> full rather than linked, because this file gets read in a meeting by someone who will not follow
> links. It was cut from [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md) § Failure modes, which
> is the source of truth — if the two ever disagree, that file wins. Do not "fix" this into a link.
>
> Replaces the old `questions-for-malachi.md`, `meetings/`, and the three Jul-24 question lists.
> When an answer arrives: the decision goes to [`decisions.md`](decisions.md), the question is struck
> from here.

---

# Part 1 — Where the work stands

## The assignment, and what came back

Port the SciOptControlToolkit RL algorithms to PyTorch, TD3 first, validate on Gymnasium. Done, in a
clone on branch `develop-dw`.

- **`TorchTD3-v0` is written, registered and tested** — `agents/torch_td3.py`, `models/torch_models.py`,
  `core/torch_model_core.py`, `cfgs/torch_td3.cfg`. Commits `ee4ced6`, `61646af`, `5c928ff`.
- **82 tests**, all passing. The 47 on the critic and agent were then **mutation-tested**: three
  defects injected one at a time (`minimum`→`maximum` in the clipped double-Q, `(1−dones)`→`dones`,
  tau swapped in `soft_update`) and caught by 3, 5 and 1 tests respectively. "N tests pass" is weak
  evidence; "here is what the suite catches" is the claim.
- **Matched against Keras on four Gymnasium environments** — ahead on two (`Pendulum-v1`, `Hopper-v5`),
  behind on one (`FetchReachDense-Flat-v0`), tied on one (`MountainCarContinuous-v0`), where both
  agents reproduce TD3's canonical hard-exploration failure identically. That mixed pattern *is* the
  evidence for a faithful port; a clean sweep would more likely mean a changed hyperparameter. Numbers
  and logdirs in [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md).
- **Additive only: 1,376 insertions, 0 deletions.** No existing toolkit file changed behaviour. That
  was a deliberate decision (`decisions.md`, 2026-08-17) and it is why Part 3 exists as *proposals*
  rather than as commits.
- **Driver and replay buffer deliberately untouched.** They do need work — but for **vectorization**,
  not for framework. Conflating "port to torch" with "support N parallel envs" is the mistake I
  avoided; scope in [`strategy.md`](strategy.md).

**Known weakness, stated before anyone asks:** one seed per arm. The Keras arm cannot be re-seeded even
in principle — it seeds from `time.time_ns()`. ≥3 seeds with reported variance is the top outstanding
item.

## The one structural finding that shaped the plan

Every research variant in the toolkit is a subclass of TD3 that overrides `train_critic` and changes
almost nothing else:

```
class KerasSINDyCriticTD3(KerasTD3)         keras_sindy_critic_td3.py:54
class KerasUncertaintyTD3(KerasTD3)        keras_uncertainty_td3.py:46      147 lines
class KerasSINDyUncertaintyTD3(...)        keras_sindy_uncertainty_td3.py    94 lines
```

So the SINDy-structured critic and the uncertainty-aware critic are **not separate algorithms — they
are modifications of the Bellman-target computation inside TD3.** The most important property of any
port is therefore a clean overridable `train_critic` seam, and "TD3 first" is a prerequisite rather
than an ordering preference. This is also the cleanest possible framing for a Methods section: the
baseline and every variant differ in exactly one function. **Please confirm I have read this right** —
it is the assumption the whole design rests on.

## Defects found while grounding the port

Each measured on a real run, not read off the page. Reported because the numbers this driver produces
are the numbers a paper would cite.

| Where | What | Consequence |
|---|---|---|
| `run_continuous.py:266` | `avg > best * (1 + threshold)` inverts sign for negative rewards. With `best = −845` the bar becomes `−887`, i.e. *below* best. | The "best model" checkpoint is not the best model. 10 of 10 eval points saved as improvements, one 98 points worse than an earlier one. `--load_model` cannot be trusted. |
| `run_continuous.py:264` vs `:281` | `nepisode_avg` counted in **episodes** in one place, **eval points** in the other. At the defaults the averaging window spans the whole run. | The reported average rises by dilution of the random-policy start, not because the policy improved: −845 → −565 while the underlying evaluations bounced −117 / −129 / −223 / −4 / −227. |
| `keras_td3.py:177–202`, `run_continuous.py:64` | Three separate wall-clock seeds, and `env.action_space` never seeded at all. | No run is reproducible. Any single-run comparison is one unrepeatable sample. |
| `run_continuous.py:258` | The evaluation episode runs on the **same env object** as training. | Eval consumes and advances the training RNG stream, so the two are not statistically independent. Measured **170 points** of evaluation spread across four same-seed runs of our own demo — and the evaluation number is the one that gets published. |
| `keras_td3.cfg` | `actor_update_freq` / `critic_update_freq` are read from config but **absent from the file**. Works only because the hardcoded fallback happens to be 2. | TD3's delayed policy update is not actually configurable, which breaks the toolkit's own no-hyperparameters-in-code rule. |
| `buffers/er.py:40–47` | 1M rows preallocated regardless of fill, and `buffer.npy` rewritten every `ceil(nepisodes/10)` episodes. | 80 MB written per snapshot always. A 15-episode smoke test wrote ≈720 MB to persist 240 KB of experience. |
| `buffers/er.py:69` | `np.random.choice(..., replace=False)` materialises a full permutation: 82 µs at 5k rows, **16.2 ms at 1M**. | Invisible on Pendulum, dominant once the buffer fills — at 1M rows index selection costs more than the gradient step it feeds. Any wall-clock comparison must state buffer occupancy. |
| `utests/` | `test_baselines.py` and `test_agents.py` train real agents into `results/` relative to the working directory. | 11 run directories appeared in the shared results tree, indistinguishable from experiments. Anyone reporting from that tree can pick up a test artefact. |
| `TorchTD3.load()` (inherited) | Whole load wrapped in `try`/`except` that logs and **continues with random weights**. | An inference number can be a random policy's number with nothing in the output to say so. Now covered by two negative tests; the fallback itself is upstream and unchanged. |

---

# Part 2 — Questions to raise, grouped by who can answer

Ranked within each group by how much the answer changes what I build. Each is one line of ask, one line
of what changes, and my recommendation where I have one.

## A. Project scope — Malachi as PM. These block design, not just detail.

1. **What goes in Section 1.2, "Tasks"?** It is blank in the brief. → It is the single largest missing
   specification; success thresholds and the randomization envelope both hang off it.
2. **What is the success criterion — open to *x* degrees, what tolerance, and must the policy hold?**
   → Defines the termination condition and the success metric, which must stay separate from the
   training reward. *Existing code commits to a full sequence ending at 180°; I need that confirmed or
   replaced.*
3. **What is the randomization envelope** — approach angle, handle rotation, base pose, door
   friction/mass? → This *is* the generalization claim. Right now the task's `position_range` is
   `(0.0, 0.0)`, so nothing generalizes yet; see [`learn/3-isaac-and-rl-games.md`](learn/3-isaac-and-rl-games.md).
   *My recommendation: fix an envelope now, however provisional, so evaluation can be built against it.*
4. **Are there concrete force/torque limits, and where do they come from?** → The brief requires "no
   brute-force pushing" and the existing task has **no force or torque anywhere** — not in
   observations, not in rewards, no contact sensor. A number turns that from a refinement into a
   requirement I can implement and test.
5. **Observation modality: privileged sim state, vision, or both?** → A major fork in effort.
   *Recommendation: privileged state for the baseline, vision as a later ablation — and say so in the
   paper rather than leaving it implicit.*
6. **Action space: joint targets, Cartesian/OSC, or torque — and is the mobile base in the RL loop?**
   → The existing code answers this *as built* (6 arm joint positions + binary gripper, base excluded)
   but not *as intended*. See the base-`dof0` reward anomaly in Part 2 § C.
7. **Is sim-to-real in scope at all?** → Determines how hard we push domain randomization, system ID
   and safety filters, and whether reset cost matters.
8. **Framework or task, and in what proportion for the paper?** → The stated goal is a modular test
   bed; a framework paper still needs a convincing task result. *Recommendation: build so the
   framework+task paper is guaranteed, the benchmark study is a section inside it, and the
   physics-informed result is upside claimed only if it lands —
   [`learn/4-door-task.md`](learn/4-door-task.md) Part 3.*
9. **Compute.** One RTX 5080 workstation caps `num_envs`. Is there a cluster, and is Azure realistic?
10. **Venue, deadline, co-authors.** → Sets how much goes into the framework versus the single task.

## B. The RL toolkit — Malachi as its author.

1. **Which architecture for the Isaac Lab track?** `decisions.md` commits to rl_games PPO for the door
   task while we are adding TD3 to `jlab_opt_control`; those need reconciling. → *Recommendation
   (option B of three in [`strategy.md`](strategy.md)): rl_games stays the door-task baseline, the
   toolkit carries the method contribution, validated on Gymnasium first.*
2. **Is TD3 alone the deliverable, or do I port the SINDy and uncertainty variants next?** → Changes
   how much extensibility I build now. The `train_critic` seam is already in place for it.
3. **Is the SINDy / physics-informed direction a target contribution for the *robotics* paper, or
   specific to accelerators?** → It is the strongest novelty lever we have. If yes, what is the
   candidate library for door-opening — hinge angle, contact force, torque terms?
4. **A formulation discrepancy I want resolved.** Colen 2026's LC-TD3 surrogate predicts a physical
   *observable* (energy) with an explicit constraint penalty; the released `KerasSINDyCriticTD3`
   instead distills the *critic* into a sparse model. Which do you want carried forward, and does the
   observable-constraint variant live with the PACES code? → Decides what I actually implement.
5. **Is my understanding of SINDy right?** As I read it: the human supplies a *library* of candidate
   terms, sparse regression picks the few that matter, and the output is a short readable equation —
   which is the opposite of a PINN, where the equation is imposed by hand. Correct me if that is too
   simple.
6. **Can I get the `paces` package?** → It holds the CEBAF/LCLS surrogate envs; `run_continuous.py`
   imports it optionally and `ExaminePACESPolicy.ipynb` depends on it. Also: are there trained
   checkpoints I can load?
7. **Did prioritized replay meaningfully help on your problems, or is uniform ER the practical
   default?** → Decides whether PER is worth porting at all.
8. **Is the public repo the one to track, or is my snapshot fixed?** → Determines whether Part 3's
   proposals have anywhere to go.
9. **Differentiable-sim RL** — Rajput 2025 shows analytic-gradient methods winning at high dimension.
   In scope for the robot, or model-free first? *Recommendation: model-free first.*

## C. The digital twin — `prat615`. Much of the old list is now answered by code.

`_reference/digital_twin_models-main/RL_CloudTesting/` answered, by being read: the door is a working
articulated task, the gripper is driven through a single `finger_joint`, and there is a registered
Isaac Lab env with a full PPO config. What the code did **not** answer:

1. **Which scene is canonical?** Our RL code uses `ENV_OT_UR_door/TrainingScene_flattened.usd`; the DT
   README points at `ENV_ESCBench/ESCBench_ROS_v6_140.usd`; the asset tree also ships
   `AIRoboticsLab.usd` and `experiment.usd`. → Deciding late means redoing scene paths.
2. **Gripper fork: 2F-85 or 2F-140?** RL code uses 2F-85; the DT README says current is 2F-140 with a
   v6 Ridgeback. → Redoing grasp tuning is the cost of getting this wrong.
3. **Is the mobile base drivable in physics?** `script_guided_base_dof0_profile_reward` (weight 0.4)
   shapes a base degree of freedom the action space does not contain. Either the base is actuated
   somewhere I have not found, or that term rewards something the policy cannot affect.
4. **Are mass, inertia and friction realistic or placeholder,** and which bodies are unreliable? →
   Bears directly on the anti-reward-hacking requirement.
5. **Is there a wrist F/T sensor modelled,** or do I read joint efforts / PhysX contact forces? → The
   force/torque requirement has to be implemented against something.
6. **Mimic or closed-loop gripper physics** for contact-rich grasping in 5.1, and are the
   `Defeatured_2F_85_*` collision meshes already wired into the recommended variant?
7. **Has this been run at `num_envs > 1`,** and is a stripped-down training scene (dropping the 59 MB
   room) available or wanted? → Directly caps throughput on one GPU.
8. **Is there a git repo to track** rather than a one-off zip, and are updates coming?
9. **What is the WidowX-AI teleop rig for** — demonstrations we could warm-start from, or a separate
   task?

## D. Team-wide

1. **Who owns which layer?** Alvika leads RL, I support, `prat615` owns the twin, the toolkit is
   Malachi's. Worth stating out loud so the env-definition boundary is not owned twice.
2. **Reproducibility as a team rule.** Fixed seeds, ≥3 seeds, reported variance, evaluation env seeded
   independently of training. → *Recommendation: agree this before results are generated, not after.
   The 170-point evaluation spread in Part 1 is what it costs to learn this later.*

## Already answered — by our own work, not by a person

Kept so they stop being re-asked.

| Question | Settled by |
|---|---|
| Shared or separate optimizers for the two critics? | Separate, one per critic — a **deliberate deviation**: Keras uses one Adam over both, which pools moment estimates across two networks TD3 needs to be independent estimators. `decisions.md` 2026-08-17. *Still worth your sign-off, since it is one of exactly three named differences between the arms.* |
| Is the wall-clock seeding intentional / must I copy it? | No. `seed` is a cfg key in `torch_td3.cfg` and the torch agent is reproducible. `decisions.md` 2026-08-17. |
| Does the dependency set really need Python 3.13, as `env.yaml` pins? | No — 3.11.9 resolves everything, TF 2.21.0 and torch 2.13.0+cpu in one env. `environment.md`. (`pysindy` is installed nowhere, which is why three notebooks do not run.) |
| Should `memory()` and `buffer` be in the agent ABC? | Moot for us: the real interface was derived from the driver and the tests, and is pinned by 82 of them. `core/agent_core.py` remains narrower than reality — worth mentioning, not worth blocking on. |
| Which env exercises genuine `terminated`? | `Hopper-v5` of the four; and the door task does, via `sequence_complete`. Three of four Gymnasium envs never terminate, which is why mutation testing was necessary. |
| Is the twin asset-only? | No. `RL_CloudTesting/` is a working Isaac Lab door task with rl_games PPO, found 2026-08-03. |

---

# Part 3 — Upstream proposals

Three concrete patches. All are in shared driver or buffer code, so I am proposing rather than
committing — the port was deliberately additive (1,376 insertions, 0 deletions). **Ask: may I submit
these?**

**1. Sign-safe checkpoint threshold — `drivers/run_continuous.py:266`, one line.**

```python
# current — for best < 0 this LOWERS the bar by `threshold`
if avg_inference_reward > best_avg_inference_reward * (1 + model_save_threshold):
# proposed
if avg_inference_reward > best_avg_inference_reward + model_save_threshold * abs(best_avg_inference_reward):
```

Both Pendulum and accelerator tuning-error rewards are negative, so the current form admits results up
to 5 % *worse* on exactly the tasks this toolkit is for. General rule worth adopting: relative
thresholds must be written sign-safe.

**2. `nepisode_avg` unit mismatch — `:264` against `:281`.** The averaging window is expressed in
episodes but applied to a list appended once per `inference_interval`. Either divide by the interval or
document the unit as eval points; as it stands the "recent average" spans the whole run and rises by
dilution. Not a one-liner in intent even if it is in diff size — it changes what every past number
meant, which is why it needs your call and not mine.

**3. `FlattenObservation` for `Dict` observation spaces — `:191`, three lines.** All 217
gymnasium-robotics ids (Fetch, Maze, Hand, Kitchen) publish a `Dict` space whose `.shape` is `None`, so
`env.observation_space.shape[0]` raises `TypeError` before training starts. We currently work around it
with an additive registry factory (`envs/robotics_flat.py`); the three-line wrapper in the driver would
make every goal-conditioned env work for everyone. Caveat to state: flattening concatenates in **sorted
key order**, and it is necessary but not sufficient — FetchPush/Slide/PickAndPlace still need HER.

**Also worth raising, no patch offered:** `buffers/er.py:69`'s `replace=False` (16.2 ms per sample at
1M rows; `replace=True` is flat at ~9 µs and is what every reference TD3 does), and that `pytest
utests/` writes real training runs into `results/`.
