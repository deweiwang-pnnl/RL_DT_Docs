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
| **The overall story, for a team audience** | [`session-2026-08-27-legion.md`](session-2026-08-27-legion.md) |
| **To play with the digital twin yourself, in the GUI** | [`ISAAC_SIM_UI_GUIDE.md`](ISAAC_SIM_UI_GUIDE.md) |
| **To run the twin through Docker** | [`DIGITAL_TWIN_HOWTO.md`](DIGITAL_TWIN_HOWTO.md) |
| **Whether any of it actually learns** | [`long-run-learning-2026-08-30.md`](long-run-learning-2026-08-30.md) |
| **A specific measured number or bug** | [`PUBLICATION_MATERIALS_legion.md`](PUBLICATION_MATERIALS_legion.md) |
| **What to tell Malachi / Martin / Alvika** | [`team-discussion_legion.md`](team-discussion_legion.md) |

## Everything, by kind

**Live — mirrors of the originals, for this machine**

| File | Mirrors | Holds |
|---|---|---|
| [`WORKLOG_legion.md`](WORKLOG_legion.md) | `WORKLOG.md` | Round index and entry |
| [`PUBLICATION_MATERIALS_legion.md`](PUBLICATION_MATERIALS_legion.md) | `PUBLICATION_MATERIALS.md` | 6 results, 11 code defects, 2 method notes — **the single home for every number** |
| [`decisions_legion.md`](decisions_legion.md) | `decisions.md` | 9 decisions, each with what it rules out |
| [`environment_legion.md`](environment_legion.md) | `environment.md` | Machine, kernel pin, network limits, both Isaac Sim installs |
| [`team-discussion_legion.md`](team-discussion_legion.md) | `team-discussion.md` | Grouped by who can act |

**History**

- [`rounds/Round-2026-08-27-legion-gpu-fix-and-dt-integration.md`](rounds/Round-2026-08-27-legion-gpu-fix-and-dt-integration.md)
  — day-by-day narrative, including the four mistakes made and what they cost.

**Reports and guides**

| File | What it is |
|---|---|
| [`session-2026-08-27-legion.md`](session-2026-08-27-legion.md) | The session report, written to be presented |
| [`session-2026-08-28-gpu-fix-and-dt-wiring.md`](session-2026-08-28-gpu-fix-and-dt-wiring.md) | The live progress log kept during the work — superseded by the report above, retained because it records a wrong diagnosis being corrected |
| [`ISAAC_SIM_UI_GUIDE.md`](ISAAC_SIM_UI_GUIDE.md) | Exploring the twin in the Isaac Sim GUI — no Docker, no RL |
| [`DIGITAL_TWIN_HOWTO.md`](DIGITAL_TWIN_HOWTO.md) | Running the twin through the Docker container |
| [`comparison-isaacsim-vs-isaaclab.md`](comparison-isaacsim-vs-isaaclab.md) | The two integration routes, head to head |
| [`long-run-learning-2026-08-30.md`](long-run-learning-2026-08-30.md) | The multi-hour learning runs, why neither route solves the task, and the four problems found doing them |
| [`gpu-retest-2026-08-29.md`](gpu-retest-2026-08-29.md) | The re-tested Gymnasium environments in detail |
| [`isaaclab-builtin-tests-2026-08-29.md`](isaaclab-builtin-tests-2026-08-29.md) | Toolkit against four Isaac Lab built-in tasks |
| [`dt-via-isaaclab-2026-08-29.md`](dt-via-isaaclab-2026-08-29.md) | The 1→128 environment scaling sweep |

## The one thing to keep in mind when reading any of this

**Neither route learns the door task, and the task is not solvable as configured.** The toolkit
drives the digital twin through two independent stacks and that plumbing is verified in detail — but
multi-hour runs showed the trained policy never opens the door, because the handle sits 0.834 m from
an arm with roughly 0.85 m of reach and the mobile base is not actuated. Reward tripling on one
route is real optimisation of the approach terms, not progress on the task. The full account, with
the measurements, is in
[`long-run-learning-2026-08-30.md`](long-run-learning-2026-08-30.md). Repeated here because it is
the easiest thing to lose when skimming, and the easiest thing to overclaim.

## Merging this back

These files were deliberately kept parallel rather than merged into `../_docs/`, so that work from
two machines would not be interleaved before anyone had reviewed it. Once the two are reconciled,
most of this belongs folded into the originals — `../_docs/README.md` sets a budget of six live files
and warns against sprawl, and this folder adds fourteen more. The natural merge is: numbers into
`PUBLICATION_MATERIALS.md`, decisions appended to `decisions.md`, the machine section into
`environment.md`, and the guides kept as-is since they have no counterpart.
