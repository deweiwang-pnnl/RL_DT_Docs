# WORKLOG

What was done, round by round — by Dewei or by the coding agent. Newest round at the top.

One line per round in the index; the narrative detail lives in the round file under
[`rounds/`](rounds/). Anything worth *publishing* (a result, a measured number, a lesson, a figure)
goes to [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md) instead of here — this file is the
record of work, that one is the record of findings. Keep each round entry to about six bullets.

## Index

| Round | Goal | Status |
|---|---|---|
| *2026-08-19* (docs only, no round file) | Reorganize `_docs/`: 36 files → 16, four learning tracks, one home per fact | done — see below |
| [Round-2026-08-17](rounds/Round-2026-08-17-torch-td3.md) | Install the agent commands, reorganize the docs, then write the PyTorch TD3 agent | done — `TorchTD3-v0` written, 82 tests, matched against Keras on 4 environments; a 5th in flight |
| [Round-2026-08-12](rounds/Round-2026-08-12-torch-agent-in-toolkit.md) | Add a PyTorch TD3 agent to `jlab_opt_control/agents`, wire it to a Gymnasium env, understand the kit | done — env installed, Keras baseline solved Pendulum; agent landed in the 08-17 round |
| [Round-2026-08-10](rounds/Round-2026-08-10-pytorch-port.md) | Port the RL algorithms to PyTorch, validate in Gymnasium, prepare for Isaac container integration | superseded — see 08-12 |

---

## 2026-08-19 — Documentation reorganization

No code touched, no results generated. `_docs/` had grown to 36 files, half of them pre-code material
filed as "closed" while holding the project's only Isaac primer and its best toolkit walkthrough; the
same facts were restated three or four times; and open questions were scattered across six files
addressed to one person.

- **Four learning tracks in [`learn/`](learn/)**, one file each — RL and TD3, the toolkit, Isaac and
  rl_games, the door task — plus the one runnable file (`td3_pendulum_demo.py`) and a
  [`learn/README.md`](learn/README.md) that carries the prerequisite chain and a printable
  five-file review list.
- **[`team-discussion.md`](team-discussion.md) replaces six question sources.** Present · ask ·
  propose: how the work is described, the open questions grouped by *who can answer them*, and three
  upstream patches written out rather than applied.
- **`strategy-torch-and-isaac.md` → [`strategy.md`](strategy.md)**, re-cast from proposal to status:
  PORT done, REUSE held, DEFER still deferred.
- **Single-sourcing rule adopted:** a measured number or a code defect lives in
  `PUBLICATION_MATERIALS.md` and nowhere else. Duplicate tables and restated defect lists collapsed to
  links. `PUBLICATION_MATERIALS.md` gained a findings index so it can be scanned rather than read.
- **`CLAUDE.md` § Current state corrected** — it still said "No agent code written yet", which every
  other file contradicted — and the two completed short-term roadmap items ticked.
- **27 files deleted in a second commit** (`3123e27`), after the salvage commit (`e752e85`, zero
  deletions), so `git log --follow` recovers any of them: `archive/` (17), `meetings/` (2),
  `learning/` (4 — the fifth, `td3_pendulum_demo.py`, moved to `learn/`), `setup/` (1),
  `rounds/README.md`, `questions-for-malachi.md`, `strategy-torch-and-isaac.md`. Result: **36 files
  → 16** under `_docs`, 3,815 lines including `CLAUDE.md` and `_hist/README.md`; 134 relative links
  and all 16 findings-index anchors resolve. Mapping:

| Deleted | Where it went |
|---|---|
| `archive/inherited-2026-07-24/01_Project_Overview.md`, `04_Paper_Skeleton_Thoughts.md`, `Attachment_RL_Understanding.md` | `learn/4-door-task.md` |
| `archive/inherited-2026-07-24/02_DigitalTwin_Detailed_Guide.md`, `02_DigitalTwin_Brief.md` | `learn/3-isaac-and-rl-games.md` (with a correction header — its "there is no code in this package" claim was wrong) |
| `archive/inherited-2026-07-24/03_RL_Toolkit_Detailed_Guide.md`, `03_RL_Toolkit_Brief.md` | `learn/2-toolkit.md` (§ 9 and § 10 only; its smoke test and "quirks" are superseded by `CLAUDE.md` and the measured failure modes) |
| `archive/inherited-2026-07-24/01_Questions_for_ProjectManager.md`, `02_Questions_for_DT_Developer.md`, `03_Questions_for_Malachi.md`, `Attachment_Questions_for_Malachi.md` | `team-discussion.md` Part 2 |
| `archive/inherited-2026-07-24/00_START_HERE.md` | superseded by `README.md` + `learn/README.md` |
| `archive/brainstorm-2026-06/SciOptControlToolkit_Walkthrough.md` | `learn/2-toolkit.md` (a PDF copy also survives at `_reference/SciOptControlToolkit_Walkthrough.pdf`) |
| `archive/brainstorm-2026-06/rl_development_plan_*.md` (504 lines), `robotics_rl_digital_twin_brainstorm.md` (489) | **nothing salvaged** — pre-code LLM brainstorm, superseded by `CLAUDE.md`'s roadmap, `strategy.md` and `learn/4-door-task.md`. `_reference/LLM_brainstorm/` no longer exists, so **git history is the only remaining copy** |
| `archive/superseded/` (2) | dead — the retired `_notes/README` and the retired worklog |
| `meetings/README.md`, `meetings/upcoming-malachi.md` | `team-discussion.md` Parts 1 and 2 |
| `setup/aws-bedrock-vscode-setup.md` | `environment.md`, final section |
| `learning/td3_pendulum_notes.md`, `gymnasium-basics.md`, `pytorch-vs-tensorflow.md` | `learn/1-rl-and-td3.md` |
| `learning/td3_pendulum_demo.py` | `learn/td3_pendulum_demo.py` (moved, three stale paths fixed) |
| `learning/README.md` | `learn/README.md` — the old one indexed 2 of its 4 files |
| `rounds/README.md` | naming convention → `README.md`; its kickoff prompt is redundant with `~/.claude/commands/round-start.md` |
| `questions-for-malachi.md` | `team-discussion.md` Part 2, with Q3/Q4/Q6 moved to "already answered by our own work" |

---

## Round-2026-08-17 — Harness, documentation layout, then the torch agent

Detail: [`rounds/Round-2026-08-17-torch-td3.md`](rounds/Round-2026-08-17-torch-td3.md).

- Installed the five slash commands to `~/.claude/commands/` (`round-start`, `wrap`, `trace`,
  `handoff`, `slides`), verified byte-identical to the source. Reorganized all documentation into
  `_docs/` grouped by lifetime — `/round-start` and `/wrap` look for `_docs/WORKLOG.md` and would
  otherwise have found the stale `_notes/worklog.md`.
- **Wrote `TorchTD3-v0` and its two models.** Commits `ee4ced6`, `61646af` and `a085ad9` on toolkit
  branch `develop-dw`: **1,376 insertions, zero deletions** — the only edits to pre-existing files are
  added lines in three `__init__.py` files and `.gitignore`.
- **All hyperparameters in `cfgs/torch_td3.cfg`, none in code.** 17 keys against Keras's 11; the 11
  shared keys are byte-identical, which is what makes the comparison controlled. Four of the extra six
  promote hardcoded Keras literals at the same numbers; `seed` and `device` have no Keras counterpart.
- **Matched the Keras baseline on four environments** — ahead on two, behind on one, tied on the
  fourth. Numbers, logdirs and caveats → [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md).
- **Opened the 217 gymnasium-robotics environments to the whole toolkit** with `envs/robotics_flat.py`,
  an additive registry factory that wraps `Dict` observation spaces in `FlattenObservation`. Built
  additively rather than as a driver patch, so the 3-line driver fix became an upstream proposal —
  [`team-discussion.md`](team-discussion.md) Part 3.
- **82 unit tests, 719 lines of test code**, then verified they fail on a real bug by injecting three
  defects and confirming each was caught. Both → PUBLICATION_MATERIALS.
- **Carried over:** the fifth environment, `AdroitHandDoor-v1`, was in flight at wrap time. A
  1000-episode run per arm launched 2026-08-19 00:44; at episode 145 the Torch arm's avg-20 had moved
  −43.78 → −36.77. **Estimate, to be replaced by the measured result:** both arms plateau around −25
  to −32 avg-20 and **do not open the door** — 200k steps is one to two orders of magnitude below
  published Adroit results. Whoever reads this next replaces the estimate.

---

## Round-2026-08-12 — PyTorch agent inside the toolkit

Detail: [`rounds/Round-2026-08-12-torch-agent-in-toolkit.md`](rounds/Round-2026-08-12-torch-agent-in-toolkit.md).
Work happens in **two repos**: toolkit code in `<PROJECT_ROOT>/SciOptControlToolkit` (branch
`develop-dw`, HEAD `48e624f` at the time), notes and logs here.

- Read the toolkit end to end and derived the agent interface **from the driver and the tests**, not
  from the ABC — `core/agent_core.py` omits `memory` and `buffer`, both of which the driver requires.
- **Installed the toolkit environment and ran the kit for the first time.** `uv venv --python 3.11`;
  the whole declared dependency set resolves on **Python 3.11.9**, TF 2.21.0 and torch 2.13.0+cpu in
  one env, so `env.yaml`'s `python=3.13` pin is not a hard floor. `torch>=2.10` was already declared
  and imported nowhere, so the port added no dependency. Machine correction: this is the laptop
  (`WF10878`, Intel Arc, **no CUDA**), not the RTX 5080 workstation.
- **Keras baseline established** — `KerasTD3-v0` solves `Pendulum-v1` on stock cfg. → PUBLICATION_MATERIALS.
- Wrote the strategy note ([`strategy.md`](strategy.md)): the three-tier PORT / REUSE / DEFER scope,
  the argument that driver and buffer work is about **vectorization not framework**, and architectures
  A/B/C with **B** recommended. Driving finding: every research variant subclasses `KerasTD3` and
  overrides `train_critic`, so a clean overridable seam is the port's most important property.
- Two things the first real run taught that reading could not: the `warmup_size` gate is visible in
  the wall clock, and the "best model" checkpoint criterion never rejects anything. Also measured a
  real performance bug in `buffers/er.py`. All three → PUBLICATION_MATERIALS, failure modes.
- Audited `notebooks/`: all four analyse a *trained* checkpoint, none trains anything, three need
  `pysindy` (declared nowhere), and `ExaminePACESPolicy.ipynb` hardcodes another developer's Mac path.

---

## Round-2026-08-10 — PyTorch port (learning pass)

Detail: [`rounds/Round-2026-08-10-pytorch-port.md`](rounds/Round-2026-08-10-pytorch-port.md).

- Read `CLAUDE.md`, `environment.md`, `decisions.md`, then the reference toolkit end to end.
- Environment check: **no NVIDIA GPU on the laptop**. The RTX 5080 / `cu128` requirement describes the
  PNNL workstation only. Not a blocker for Pendulum-scale TD3. Target Python **3.11**.
- Learning notes written, now merged into [`learn/1-rl-and-td3.md`](learn/1-rl-and-td3.md) with the
  standalone demo at [`learn/td3_pendulum_demo.py`](learn/td3_pendulum_demo.py).
- No production code written. **Superseded:** the plan was a from-scratch `rl_dt/` package; the 08-12
  decision is to add a torch agent *inside* the existing toolkit instead.

---

## Before rounds (setup phase)

- **2026-08-12** — answered "does the whole kit need re-drafting in PyTorch?" (no); cloned
  `JeffersonLab/SciOptControlToolkit` to `<PROJECT_ROOT>/SciOptControlToolkit` on branch `develop-dw`
  as a live working copy; adopted `WORKLOG.md` + `PUBLICATION_MATERIALS.md` and retired
  `_notes/worklog.md`; documented FAI/Bedrock billing for the VS Code extension (now the last section
  of [`environment.md`](environment.md)).
- **2026-08-04** — `Z:\RL_Twin` no longer resolves; the canonical path is the OneDrive folder and
  `Z:\` was purged from `CLAUDE.md`. Project documentation moved inside the repo so it travels with
  `git clone`; `_reference/` (~2 GB) stays out.
- **2026-08-03** — read all of `_docs/`, skimmed both reference codebases, and found that the DT
  package is **not asset-only**: `_reference/digital_twin_models-main/RL_CloudTesting/` holds a working
  Isaac Lab `ManagerBasedRLEnv` door task with rl_games train/play scripts. Gaps in it: no force/torque
  penalty, no domain randomization, heavy script-guided rewards — all three are now roadmap items.
  Wrote `CLAUDE.md` and set up the repo.
