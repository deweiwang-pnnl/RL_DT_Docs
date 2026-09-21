# `_docs` — all project documentation

`CLAUDE.md` at the repo root is the **map** and loads into every session, so it stays short.
Everything else is here: 16 files, grouped by **lifetime**.

Two rules keep it that way.

1. **One home per fact.** A measured number or a code defect lives in
   [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md) and nowhere else. Everything else links to
   it. The one deliberate exception is [`team-discussion.md`](team-discussion.md), which restates a
   defect table because it is a handout — it says so at the top.
2. **File it by how long it stays true.** Live · History · Learn.

---

## 1. To review the done work — five hops, in order

The whole record. No sixth file is needed, and none of the learning tracks are on the list.

| | Read | For |
|---|---|---|
| 1 | [`../CLAUDE.md`](../CLAUDE.md) § Current state, then § Roadmap | Where the project stands, and what is planned. Start here so the rest has a frame. |
| 2 | [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md) — the findings index, then whichever entries matter to you | Every measured number and every code defect, with evidence attached. The most valuable file in the repo. |
| 3 | [`WORKLOG.md`](WORKLOG.md) — the index table, then the round entries | What was done, round by round. Drill into [`rounds/`](rounds/) only for provenance on a specific claim. |
| 4 | [`strategy.md`](strategy.md) Parts 2 and 5 | What was ported, what was reused, what was deferred, and the three architecture options with a recommendation. |
| 5 | [`team-discussion.md`](team-discussion.md) — all of it, it is short | What to present, what to ask and who can answer it, three fixes to propose upstream. The only file with an action attached. |

## 2. To learn — [`learn/README.md`](learn/README.md)

Four numbered tracks with prerequisites and honest sizes, one runnable demo, and a printable review
list at the end. Start there, not here.

---

## Live — updated as the work moves

| File | What goes in it |
|---|---|
| [`WORKLOG.md`](WORKLOG.md) | The round index, newest first, then ~6 bullets per round. Detail goes in `rounds/`. The file `/round-start` and `/wrap` read. |
| [`PUBLICATION_MATERIALS.md`](PUBLICATION_MATERIALS.md) | Results with conditions, method choices with reasons, failure modes, comparisons, figures — each with its evidence. Collected as we go, never reconstructed. Scan the findings index at the top. |
| [`decisions.md`](decisions.md) | What we chose, when, why, and what it rules out. Append-only, in date order; supersede rather than edit. |
| [`strategy.md`](strategy.md) | The standing plan, now a status note: what was ported, reused and deferred, and the A/B/C architecture options for the Isaac Lab track. |
| [`team-discussion.md`](team-discussion.md) | Present · ask · propose. Replaces every old per-person question list. When an answer arrives, the decision graduates to `decisions.md` and the question is struck from here. |
| [`environment.md`](environment.md) | Machines, paths, GPU, Python envs, how to get a new computer running — plus the FAI/Bedrock billing appendix. |

## History — written once, then left alone

[`rounds/`](rounds/) holds one file per round, `Round-YYYY-MM-DD-<slug>.md`, dated from the day the
round starts so the folder sorts chronologically. Written **during** the round, not after. Open a round
by adding a row to `WORKLOG.md`; close it by updating that row's status. Anything durable that came out
of it gets appended to `decisions.md` rather than left buried in the log. The round template and the
kickoff prompt live in `~/.claude/commands/round-start.md`, not here.

`_hist/` at the **repo root** — not in `_docs/` — is where `/trace` writes a verified result: the
script, its raw output, and a `NOTES.md` saying what it settles. See [`../_hist/README.md`](../_hist/README.md).

## Learn — read once, then use as lookup

[`learn/`](learn/) — four tracks plus the one runnable file in `_docs`. Explanatory material only: no
project decisions, no measured numbers. Where a track disagrees with a live file, the live file wins.

## Not in this repo

- `<PROJECT_ROOT>/SciOptControlToolkit/` — a live clone of the Jefferson Lab toolkit on branch
  `develop-dw`, where all the RL code is. **Toolkit code goes there, notes go here; the two never mix.**
- `<PROJECT_ROOT>/_reference/` — USD assets, the digital twin package, the brief, the papers. ~2 GB,
  not version-controlled, re-obtained per machine. See [`environment.md`](environment.md).

## Where a new file goes

Ask how long it stays true. **Live** if it will be edited again — but first check whether it belongs as
a section in one of the six files above; six is the budget. **History** if it is a dated record — a
round file. **Learn** if it explains something rather than recording it. If it is a measured number or a
defect, it is not a new file at all: it is an entry in `PUBLICATION_MATERIALS.md` plus a row in its
index.

*Reorganized 2026-08-19: 36 files → 16. The mapping from every deleted file to where its content went is
in [`WORKLOG.md`](WORKLOG.md) under 2026-08-19, so `git log --follow` recovers anything.*
