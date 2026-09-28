# RL_DT_docs — documentation for the RL-for-digital-twin project

Notes, reports, meeting materials and learning material. **No code lives here** — the code, training results and
videos are in the sibling repo `RL_DT` (PNNL GitLab). Keep the two repos side by side in one folder:

```
RL_Twin/
├── RL_DT/          code + results (the well-plate task: RL_DT/_isaaclab_wellplate/)
└── RL_DT_docs/     this repo
```

The meeting slides play videos straight from `RL_DT/…/results/` through that relative layout.

## Start here

| If you want | Go to |
|---|---|
| **The latest results — weekly meeting 2026-09-28** | [`_docs_legion/presentations/2026-09-28-weekly/`](_docs_legion/presentations/2026-09-28-weekly/) — open `slides.html` |
| The detailed report of the latest round, with evidence | [`_docs_legion/reports/wellplate-round-2026-09-28.md`](_docs_legion/reports/wellplate-round-2026-09-28.md) |
| How to show the recordings and TensorBoard | [`_docs_legion/guides/SHOWING_PROGRESS.md`](_docs_legion/guides/SHOWING_PROGRESS.md) |
| To learn the concepts behind the latest round | [`_docs_legion/learn/`](_docs_legion/learn/) (slides + text) |
| To learn RL, TD3, the toolkit and the door task from the start | [`_docs/learn/`](_docs/learn/) |
| The round-by-round history | [`_docs_legion/WORKLOG_legion.md`](_docs_legion/WORKLOG_legion.md) (Legion machine) · [`_docs/WORKLOG.md`](_docs/WORKLOG.md) (laptop / workstation) |
| Every measured number and defect | [`_docs_legion/PUBLICATION_MATERIALS_legion.md`](_docs_legion/PUBLICATION_MATERIALS_legion.md) · [`_docs/PUBLICATION_MATERIALS.md`](_docs/PUBLICATION_MATERIALS.md) |
| Open questions for Malachi, Martin, Alvika | [`_docs_legion/team-discussion_legion.md`](_docs_legion/team-discussion_legion.md) · [`_docs/team-discussion.md`](_docs/team-discussion.md) |

## Layout

| Folder | What | Written on |
|---|---|---|
| [`_docs/`](_docs/) | The original documentation: worklog, decisions, strategy, publication materials, the four learning tracks, rounds 08-10 → 08-17 | Dewei's laptop, PNNL workstation |
| [`_docs_legion/`](_docs_legion/) | Everything from the Legion laptop (`trossen-ai`, RTX 5090) since 2026-08-27: live files (`*_legion.md`), `rounds/`, `reports/`, `guides/`, `presentations/` (one folder per meeting), `learn/` — see its [README](_docs_legion/README.md) | Legion laptop |
| [`_hist/`](_hist/) | Frozen snapshots: PDF review packets (08-21, 09-02) and the scripts that built them | both |

The two `_docs*` folders are companions, not duplicates: each records its own machine, and neither is edited from the
other machine.

## Conventions

- **Live files** (worklog, decisions, publication materials, team discussion, environment) are kept current; a
  measured number or defect lives in the publication file once and everything else links to it.
- **Rounds** (`rounds/Round-YYYY-MM-DD-slug.md`): one continuous block of work, written as it happens, not edited
  afterwards except for pointers.
- **Decisions** are append-only: what was chosen, why, what it rules out, and who decided.
- Presentations are self-contained folders (`slides.html` offline, `slides.md` for Marp → PowerPoint, `assets/`).
- Large or regenerable artefacts (checkpoints, TensorBoard logs, replay buffers) stay out of both repos; hand-carry
  bundles go to `RL_Twin/_exports/` on the machine that made them.
