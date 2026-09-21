# `_docs_legion` — documentation from the Legion machine

Everything here was produced on **`trossen-ai`** (the Legion laptop, RTX 5090) during
**2026-08-27 → 08-31**. It is kept separate from [`../_docs/`](../_docs/), which holds the original
documentation written on Dewei's laptop and the PNNL workstation.

**The two folders are not duplicates.** They describe different machines with genuinely different
capabilities — this one has a Blackwell GPU and two Isaac Sim installations, but cannot reach tanuki
or the PNNL shared drives. Where a `_legion` file appears to contradict its counterpart in `_docs/`,
both are correct about their own machine.

Nothing in `../_docs/` was modified.

---

## Start here

| If you want | Read |
|---|---|
| **The overall story, for a team audience** | [`session-2026-08-27-legion.md`](reports/session-2026-08-27-legion.md) |
| **To play with the digital twin yourself, in the GUI** | [`ISAAC_SIM_UI_GUIDE.md`](guides/ISAAC_SIM_UI_GUIDE.md) |
| **To run the twin through Docker** | [`DIGITAL_TWIN_HOWTO.md`](guides/DIGITAL_TWIN_HOWTO.md) |
| **Whether any of it actually learns** | [`long-run-learning-2026-08-30.md`](reports/long-run-learning-2026-08-30.md) |
| **A specific measured number or bug** | [`PUBLICATION_MATERIALS_legion.md`](PUBLICATION_MATERIALS_legion.md) |
| **What to tell Malachi / Martin / Alvika** | [`team-discussion_legion.md`](team-discussion_legion.md) |

## Layout (reorganized 2026-09-21)

```
_docs_legion/
├── README.md                          this file
├── WORKLOG_legion.md                  round index for this machine
├── PUBLICATION_MATERIALS_legion.md    every measured number and code defect
├── decisions_legion.md · environment_legion.md · team-discussion_legion.md
├── rounds/                            one file per round (2026-08-27, 2026-09-14 … 09-21)
├── presentations/                     meeting hand-outs — start with 2026-09-21-wellplate-status.md
├── guides/                            DIGITAL_TWIN_HOWTO.md, ISAAC_SIM_UI_GUIDE.md
└── reports/                           dated analyses: gpu-retest, isaaclab-builtin-tests, dt-via-isaaclab,
                                       comparison-isaacsim-vs-isaaclab, long-run-learning, session summaries
```

The well-plate task itself (code, logs, videos, `PROGRESS.md`) lives in `RL_DT/_isaaclab_wellplate/`;
Alvika's tube task working copy in `RL_DT/_isaaclab_tuberacking/`.
