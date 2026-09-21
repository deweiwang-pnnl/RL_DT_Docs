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
| [Round-2026-09-14](rounds/Round-2026-09-14-isaaclab-tuberacking.md) | Isaac Lab on Alvika's tube task, then the well-plate ladder (reach → align → lift → stack → place) | reach 96.7 %, align 96 %; lift blocked by the converted 2F-140 gripper — see [presentations/2026-09-21-wellplate-status.md](presentations/2026-09-21-wellplate-status.md) |
| [Round-2026-08-27](rounds/Round-2026-08-27-legion-gpu-fix-and-dt-integration.md) | Stand the project up on a new machine, then connect the RL toolkit to the digital twin | done — three integration routes working, toolkit fixed for Blackwell GPUs, Isaac Sim installed both ways |

---

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
  patch in [`../_patches/`](../_patches/README.md). **An initial diagnosis blaming an upstream
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
