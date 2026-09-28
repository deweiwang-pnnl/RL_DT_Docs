# WORKLOG — `trossen-ai` (the Legion machine)

Companion to [`WORKLOG.md`](../_docs/WORKLOG.md), which is **not modified** — it records work from Dewei's
laptop and the PNNL workstation. This file records work done on the Legion machine, which is a
separate environment with different capabilities (no tanuki access, an RTX 5090, Isaac Sim installed
two ways).

Same conventions: newest round at the top, about six bullets each, detail in `rounds/`. Measured
numbers and code defects go to
[`PUBLICATION_MATERIALS_legion.md`](PUBLICATION_MATERIALS_legion.md), not here.

## Index

| Round | Goal | Status |
|---|---|---|
| [Round-2026-09-22](rounds/Round-2026-09-22-wellplate-grasp-fix.md) | Fix the grasp with Martin's robot, then the 2-plate stack, centred stacking, 3 plates, loose bottom plate, realistic arm, other libraries | grasp fixed (16/16); align 82 %, lift 87.5 %, 2-plate stack 50.8 %; **centred stack (5 mm / 3° / 3°) 90.6 %**; **3 plates, all loose, loose bottom plate, realistic arm 54.7 %** (deterministic); E5 library comparison; meeting materials 09-28 |
| [Round-2026-09-14 (09-20/21 part)](rounds/Round-2026-09-14-isaaclab-tuberacking.md#2026-09-20--re-scoped-to-the-well-plate-task-overnight-ladder-launched) | Well-plate ladder: reach → align → lift → stack | reach 96.7 %, align 96 %, lift 0 % (8 runs), stack 0 %; presentation videos 09-21 |
| [Round-2026-09-14](rounds/Round-2026-09-14-isaaclab-tuberacking.md) | Isaac Lab on Alvika's tube task, then the well-plate ladder (reach → align → lift → stack → place) | reach 96.7 %, align 96 %; lift blocked by the converted 2F-140 gripper — see [presentations/2026-09-21-wellplate-status/](presentations/2026-09-21-wellplate-status/) |
| [Round-2026-08-27](rounds/Round-2026-08-27-legion-gpu-fix-and-dt-integration.md) | Stand the project up on a new machine, then connect the RL toolkit to the digital twin | done — three integration routes working, toolkit fixed for Blackwell GPUs, Isaac Sim installed both ways |

---

## 2026-09-22 → 09-28 — The lift blocker was ours; three plates stacked, centred, all loose

Commits 09-26 03:03 → 09-27 20:12 (`RL_DT`, 82 commits; code +5 230 lines in 48 files) plus the 09-28 wrap-up.
The 09-22 check of Martin's GRIPPERFIX and the 09-25 message to him predate the first commit (dates from the round
file). Started with lift at 0 % and no plate ever lifted; ended with three of Martin's plates stacked with every plate
loose. All numbers deterministic, 128 episodes, one training seed each. Detail:
[round file](rounds/Round-2026-09-22-wellplate-grasp-fix.md), [report](reports/wellplate-round-2026-09-28.md).

- **The lift blocker was our own gripper setup, not Martin's asset.** Four defects, each measured before fixing: pad
  joint driven to 0 (a URDF habit; in the USD it closes the four-bar loop), grasp height (18.4 mm pad travel),
  closing axis (the 128 mm side), contact settings. Grasp gate 16/16 (09-26 03:03). Martin's GRIPPERFIX layer does
  not compose with our robot file and was not used. [D12](PUBLICATION_MATERIALS_legion.md#d12),
  [D13](PUBLICATION_MATERIALS_legion.md#d13), [D16](PUBLICATION_MATERIALS_legion.md#d16)
- **Ladder:** align 82.0 %, lift 87.5 %, 2-plate stack 50.8 % (09-26 20:24). [R7](PUBLICATION_MATERIALS_legion.md#r7)
- **Centred 2-plate stack** (5 mm / 3° twist / 3° tilt, released) **90.6 %** (09-27 05:13); the 09-26 policy scores
  0 %. Made learnable by a twist observation, a tolerance curriculum and a success bonus larger than the critic's
  noise. [R8](PUBLICATION_MATERIALS_legion.md#r8), [M4](PUBLICATION_MATERIALS_legion.md#m4)
- **Three plates:** hand-off 52.3 %, all loose 46.1 %, loose bottom plate 49.2 %, realistic arm 54.7 % (09-27 11:43 →
  16:09). Three single-policy attempts failed — an input-normaliser spike, then the first skill overwritten (swap
  test), then learned avoidance of grasping. What worked: two skills, a rising-stack curriculum, start states
  recorded at real hand-offs, and a mass curriculum for the loose bottom plate.
  [R9](PUBLICATION_MATERIALS_legion.md#r9), [M5](PUBLICATION_MATERIALS_legion.md#m5),
  [M6](PUBLICATION_MATERIALS_legion.md#m6)
- **Realistic arm:** gravity-compensation torques make the gravity-on arm track like the gravity-off arm (434 mm →
  0.0 mm), so the policies transfer unchanged. [R10](PUBLICATION_MATERIALS_legion.md#r10)
- **Other libraries (09-27 20:12):** Reach is easy for rsl_rl, skrl and rl_games PPO. On Align from scratch only
  skrl PPO learned it (98.4 %). My first explanation, rsl_rl's learning-rate floor, was tested with a fixed-rate run
  and **rejected**; the gap is open. [R11](PUBLICATION_MATERIALS_legion.md#r11),
  [D15](PUBLICATION_MATERIALS_legion.md#d15)
- **Mistakes of my own, caught and recorded:** the centred driver restarted C1 from the 09-26 policy after C1a–C1c
  (stopped within a minute); the success bonus had paid 0 in every stage until 09-26
  ([D14](PUBLICATION_MATERIALS_legion.md#d14)); a claimed cause for the black bottom plate went into the slides,
  then was withdrawn.

**Decisions** (who, why, what it rules out — full entries in [`decisions_legion.md`](decisions_legion.md)):
- Martin's robot only, no Isaac Lab built-in robot (Dewei, 09-22). Rules out swapping the gripper asset as the fix.
- Robot gravity off for training, realistic arm later (Dewei, 09-26). The uncompensated arm stalled 0.3–0.4 m short.
  Rules out training on the uncompensated arm; revisited in E4.
- Bottom plate fixed first, loose later (Dewei, 09-26). Stages the hardest physics last.
- Centred criteria 5 mm / 3° / 3° with a 40 % gate (Dewei, PLAN v4). Fixes what "done" means for every later stage.
- Gate on the deterministic evaluation, not training success (Claude, 09-26). Rules out reporting noisy training
  numbers.
- Two skills instead of one policy (Claude, 09-27, within the PLAN v5 autonomy rules). Rules out, for now, a single
  policy that decides when the first plate is done.

**What this does not show:** run-to-run variance (single seeds); a reliable final setting (36 % time-outs, 9 % drops);
one policy for the whole task; perception (privileged poses), a moving base, or randomised plate physics; why skrl
beats rsl_rl on Align; why the bottom plate renders black.

**Next:** 3 seeds per result; cut the time-outs; one chaining policy; domain randomisation; test skrl's value-target
normalisation against rsl_rl; camera-based plate detection (ask Alvika); Martin on the black plate and a
self-contained robot USD. Questions are in [`team-discussion_legion.md`](team-discussion_legion.md).

### Documents produced this round

| File | What it holds |
|---|---|
| [`presentations/2026-09-28-weekly/`](presentations/2026-09-28-weekly/) | Meeting slides (offline HTML with videos, Marp copy for PowerPoint), hand-out |
| [`reports/wellplate-round-2026-09-28.md`](reports/wellplate-round-2026-09-28.md) | The detailed report with every result, diagnosis and evidence path |
| [`guides/SHOWING_PROGRESS.md`](guides/SHOWING_PROGRESS.md) | How to show the recordings (with timestamps) and TensorBoard |
| [`learn/`](learn/) | Learning package: seven parts with check-yourself questions, plus slides |
| [`evidence/`](evidence/) — [`PROGRESS.md`](evidence/wellplate/PROGRESS.md), [`PLAN.md`](evidence/wellplate/PLAN.md) v3–v5, [`results/`](evidence/wellplate/results/) | Copies of the chronology, plans and evidence (videos, charts, evaluation JSONs) from `RL_DT` |
| [`evidence/wellplate/tensorboard/`](evidence/wellplate/tensorboard/) | 40 runs' TensorBoard event files (56 MB) |

## 2026-08-30 → 08-31 — Do the routes actually learn? No, and here is why

Multi-hour runs on both routes to answer the question every earlier result left open.
Full report: [`long-run-learning-2026-08-30.md`](reports/long-run-learning-2026-08-30.md).

- **Neither route learned the door task.** The direct route's reward tripled (105.8 → 334.3) and
  converged by episode ~400, but replaying the trained policy deterministically moves the door in
  **0 of 6 episodes**. The 1.2% of training episodes where the door moved were exploration noise
  shoving it — the peak of exactly 3.1416 rad is the hinge's −180° limit, not a pulled-open door.
- **The task is not solvable as configured**, and this was measured rather than inferred: the handle
  sits 0.834 m from the arm base against a ~0.85 m reach, and the gripper gets no closer than
  0.207 m over 300 sampled arm poses. Martin's `ActionsCfg` actuates arm and gripper only.
  [D10](PUBLICATION_MATERIALS_legion.md#d10) — **needs a decision from Martin.**
- **Found an upstream performance bug that throttles every long run**: the replay buffer sampled
  with `np.random.choice(..., replace=False)`, which is O(buffer). 460× slower than `randint` at
  200k entries; the GPU sat at 3% while the CPU pegged.
  [D9](PUBLICATION_MATERIALS_legion.md#d9).
- **Three mistakes of my own**, all caught and documented: half the ported reward was silently dead
  because the fingertip prims do not resolve ([D11](PUBLICATION_MATERIALS_legion.md#d11)); neither
  training script logged reward at all, which a pilot caught before the night was wasted; and a
  `.gitignore` pattern aimed at buffer *data* also hid the buffer *source package* from git.
- **Logging door angle, not just reward, is what made the diagnosis possible** — reward rising while
  door angle stayed at zero is precisely the signature of optimising shaped terms without solving
  the task.

## 2026-08-27 → 2026-08-29 — New machine, toolkit fix, and three routes to the digital twin

Started from a copied project folder on an unfamiliar machine and ended with the toolkit driving
Martin's door task through two independent stacks. The bulk of the effort was not the integration —
it was making the toolkit run at all.

- **Machine brought up.** GPU was dead on arrival (`nvidia-smi` failing, no kernel module for the
  running kernel); resolved by pinning the boot kernel. Docker, `git-lfs` and `uv` installed. This
  machine cannot reach tanuki or the PNNL shared drives, so both DT repos exist as extracted copies
  and the Isaac Lab image was built locally rather than pulled.
  See [`environment_legion.md`](environment_legion.md).
- **The blocker: `TorchTD3-v0` segfaulted before its first training step.** Diagnosed to a
  TensorFlow/Triton native-library conflict — whichever loads second crashes — plus a silent second
  symptom where importing TF makes torch stop seeing the GPU. Fixed in 5 files; the Keras agents were
  regression-tested and still train. [D1](PUBLICATION_MATERIALS_legion.md#d1),
  patch in [`../_patches/`](evidence/patches/README.md). **An initial diagnosis blaming an upstream
  PyTorch/Blackwell bug was wrong** and is recorded as such.
- **Side effect worth more than the fix:** the lazy-import work cleared the blocker in
  [`strategy.md`](../_docs/strategy.md) Part 2 — the package now imports in a torch-only container, which is
  what made everything Isaac-related possible.
- **Environments re-tested on GPU.** Four of five published environments reproduced;
  `FetchReachDense-Flat-v0` cannot start due to a `gymnasium-robotics` / `mujoco` incompatibility
  unrelated to the toolkit. [R1](PUBLICATION_MATERIALS_legion.md#r1),
  [D6](PUBLICATION_MATERIALS_legion.md#d6).
- **Isaac Sim installed twice, deliberately** — the Docker container (Isaac Lab, for training) and a
  5.1.0 workstation install (GUI, for looking at the twin). Both verified loading Martin's scene.
  Guides: [`ISAAC_SIM_UI_GUIDE.md`](guides/ISAAC_SIM_UI_GUIDE.md),
  [`DIGITAL_TWIN_HOWTO.md`](guides/DIGITAL_TWIN_HOWTO.md).
- **Three integration routes built and measured** — bare Isaac Sim (345 lines, no framework), Isaac
  Lab single-env, and Isaac Lab vectorised (1→128 environments). The vectorised adapter also drove
  four Isaac Lab built-in tasks unchanged, which is what shows it is a general bridge rather than
  door-task-shaped. [R2](PUBLICATION_MATERIALS_legion.md#r2)–[R5](PUBLICATION_MATERIALS_legion.md#r5).
- **Three upstream toolkit bugs found** beyond the segfault: packaging that breaks `pip install -e .`,
  three subpackages missing `__init__.py`, and an undeclared dependency.
  [`team-discussion_legion.md`](team-discussion_legion.md) has the write-ups to send.

**What this does not show:** that anything *learns the door task*. Every run was minutes long with an
untrained policy, and the two routes do not use the same reward. Stated at length in
[`comparison-isaacsim-vs-isaaclab.md`](reports/comparison-isaacsim-vs-isaaclab.md).

### Documents produced this round

| File | What it holds |
|---|---|
| [`session-2026-08-27-legion.md`](reports/session-2026-08-27-legion.md) | The session summary, written for the team |
| [`PUBLICATION_MATERIALS_legion.md`](PUBLICATION_MATERIALS_legion.md) | Every measured number and code defect |
| [`environment_legion.md`](environment_legion.md) | Machine setup, kernel pin, network limits, both Isaac Sim installs |
| [`decisions_legion.md`](decisions_legion.md) | Nine decisions with reasoning and what each rules out |
| [`team-discussion_legion.md`](team-discussion_legion.md) | Items for Malachi, Martin and Alvika |
| [`ISAAC_SIM_UI_GUIDE.md`](guides/ISAAC_SIM_UI_GUIDE.md) | Exploring the twin in the GUI, for learning |
| [`DIGITAL_TWIN_HOWTO.md`](guides/DIGITAL_TWIN_HOWTO.md) | Running the twin through Docker |
| [`comparison-isaacsim-vs-isaaclab.md`](reports/comparison-isaacsim-vs-isaaclab.md) | The two routes, head to head |
| [`gpu-retest-2026-08-29.md`](reports/gpu-retest-2026-08-29.md) | The re-tested environments in detail |
| [`isaaclab-builtin-tests-2026-08-29.md`](reports/isaaclab-builtin-tests-2026-08-29.md) | The four built-in tasks |
| [`dt-via-isaaclab-2026-08-29.md`](reports/dt-via-isaaclab-2026-08-29.md) | The scaling sweep |

That is more files than the six-live-file budget in [`README.md`](../_docs/README.md) would suggest. They are
kept separate because this machine's record should not be interleaved with the originals, but
consolidating them into the main documents is worth doing once the two machines' work is merged.
