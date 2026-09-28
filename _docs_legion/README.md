# `_docs_legion` — documentation from the Legion machine

Everything here was produced on **`trossen-ai`** (the Legion laptop, RTX 5090) since **2026-08-27**; the latest
round ran **2026-09-22 → 09-28** (well-plate stacking in Isaac Lab). It is kept separate from
[`../_docs/`](../_docs/), which holds the original documentation written on Dewei's laptop and the PNNL workstation.

**The two folders are not duplicates.** They describe different machines with genuinely different
capabilities — this one has a Blackwell GPU and two Isaac Sim installations, but cannot reach tanuki
or the PNNL shared drives. Where a `_legion` file appears to contradict its counterpart in `_docs/`,
both are correct about their own machine.

Nothing in `../_docs/` was modified.

---

## Start here

| If you want | Read |
|---|---|
| **The latest results, for the team (2026-09-28)** | [`presentations/2026-09-28-weekly/`](presentations/2026-09-28-weekly/) — slides (`slides.html`), hand-out |
| **The detailed well-plate report with evidence** | [`wellplate-round-2026-09-28.md`](reports/wellplate-round-2026-09-28.md) |
| **To demo the recordings and TensorBoard** | [`SHOWING_PROGRESS.md`](guides/SHOWING_PROGRESS.md) |
| **To learn the concepts behind the well-plate round** | [`learn/`](learn/) — slides + text |
| **The overall story, for a team audience** | [`session-2026-08-27-legion.md`](reports/session-2026-08-27-legion.md) |
| **To play with the digital twin yourself, in the GUI** | [`ISAAC_SIM_UI_GUIDE.md`](guides/ISAAC_SIM_UI_GUIDE.md) |
| **To run the twin through Docker** | [`DIGITAL_TWIN_HOWTO.md`](guides/DIGITAL_TWIN_HOWTO.md) |
| **Whether any of it actually learns** | [`long-run-learning-2026-08-30.md`](reports/long-run-learning-2026-08-30.md) |
| **A specific measured number or bug** | [`PUBLICATION_MATERIALS_legion.md`](PUBLICATION_MATERIALS_legion.md) |
| **What to tell Malachi / Martin / Alvika** | [`team-discussion_legion.md`](team-discussion_legion.md) |

## Layout (reorganized 2026-09-21, updated 2026-09-28)

```
_docs_legion/
├── README.md                          this file
├── WORKLOG_legion.md                  round index for this machine
├── PUBLICATION_MATERIALS_legion.md    every measured number and code defect
├── decisions_legion.md · environment_legion.md · team-discussion_legion.md
├── rounds/                            one file per round (2026-08-27, 2026-09-14, 2026-09-22)
├── presentations/                     one folder per meeting — 2026-09-21-wellplate-status/, 2026-09-28-weekly/ (slides)
├── guides/                            DIGITAL_TWIN_HOWTO.md, ISAAC_SIM_UI_GUIDE.md, SHOWING_PROGRESS.md
├── learn/                             learning package for the well-plate round (slides + text)
├── evidence/                          copies of the cited results (from RL_DT), TensorBoard bundle
└── reports/                           dated analyses: gpu-retest, isaaclab-builtin-tests, dt-via-isaaclab,
                                       comparison-isaacsim-vs-isaaclab, long-run-learning, session summaries,
                                       wellplate-round-2026-09-28
```

The well-plate task's code and full logs live in `RL_DT/_isaaclab_wellplate/`; copies of every result the documents cite
(videos, charts, READMEs, [`PROGRESS.md`](evidence/wellplate/PROGRESS.md), TensorBoard curves) are in [`evidence/`](evidence/);
Alvika's tube task working copy in `RL_DT/_isaaclab_tuberacking/`.
