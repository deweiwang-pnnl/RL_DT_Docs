# Learning tracks

Four files. Read them in this order, or jump to the one you need — each says what it assumes.
Everything here is **explanatory material**. Project decisions live in
[`../decisions.md`](../decisions.md), measured numbers in
[`../PUBLICATION_MATERIALS.md`](../PUBLICATION_MATERIALS.md). Where a track disagrees with the
official docs, the docs win.

## The four tracks

| | Track | What you get | Lines | Needs |
|---|---|---|---|---|
| `[ ]` | [1 — RL and TD3](1-rl-and-td3.md) | Enough RL to read and modify the ported agent: the Gymnasium contract, the Bellman target, TD3's three tricks. Plus a PyTorch-vs-TensorFlow appendix. | 450 | — |
| `[ ]` | [`td3_pendulum_demo.py`](td3_pendulum_demo.py) | **Run this.** One self-contained file, TD3 solving Pendulum in ~50 episodes. The only runnable thing in `_docs/`. | 333 | Track 1 |
| `[ ]` | [2 — The toolkit](2-toolkit.md) | How to find your way around `jlab_opt_control`: registry + config, the layers, the reading order, where our code sits. | 180 | Track 1 |
| `[ ]` | [3 — Isaac and rl_games](3-isaac-and-rl-games.md) | What the twin is, the Isaac vocabulary, and a guided read of the door task that already exists. | 218 | Track 1 |
| `[ ]` | [4 — The door task](4-door-task.md) | What we were actually asked to do, and the three ways it could become a paper. | 221 | — |

**Prerequisite chain:** 1 → 2, and 1 → 3. Track 4 stands alone.

**Reading order if you want the shortest path to being useful:** 4 (why) → 1 (how) → run the demo →
3 (the actual task). Track 2 matters when you next touch toolkit code.

**Reading order if you want motivation first:** 4 → 1 → 2 → 3.

Track 1 is the heavy one at 450 lines because it replaces three separate files. Parts 1–2 are the
sitting; Parts 3–4 and the appendix are lookup — don't try to absorb them in one pass.

## Honest gaps

Stated so you don't go looking for material that isn't here.

- **PPO is not taught anywhere**, and it is the algorithm the Isaac Lab track actually uses. Track 3
  reads its config; nothing explains the clipped surrogate objective or GAE.
- **rl_games itself is undocumented** in this project. Track 3 names this as a real gap.
- **SAC and DDPG** get a sentence each.
- **Nothing in Track 3 has been run** — no RTX GPU on this machine. Its four "verify while reading"
  items are checks, not findings.

---

# When you finish: the review list

Five files, in this order. This is the whole record of what has been done — no sixth file is needed,
and none of the tracks above are on it.

```
[ ] 1.  ../../CLAUDE.md              § Current state, then § Roadmap
        ────────────────────────────────────────────────────────────────────────
        Where the project stands in ten lines, and what is planned. Start here so
        the rest has a frame.

[ ] 2.  ../PUBLICATION_MATERIALS.md  the findings index at the top, then the
                                     entries you care about
        ────────────────────────────────────────────────────────────────────────
        Every measured number and every code defect, with evidence attached. The
        most valuable file in the repo. Scan the index; read the entries that
        matter to you.

[ ] 3.  ../WORKLOG.md                the index table, then the round entries
        ────────────────────────────────────────────────────────────────────────
        What was done, round by round. Drill into ../rounds/ only when you need
        provenance for a specific claim.

[ ] 4.  ../strategy.md               Parts 2 and 5
        ────────────────────────────────────────────────────────────────────────
        What was ported, what was reused, what was deliberately deferred, and the
        three architecture options with a recommendation.

[ ] 5.  ../team-discussion.md        all of it — it is short
        ────────────────────────────────────────────────────────────────────────
        What to present, what to ask and who can answer it, and the three fixes
        to propose upstream. The only file with an action attached.
```

Two things to expect while reading. `PUBLICATION_MATERIALS.md` and `WORKLOG.md` overlap by design —
the worklog says what was done, publication materials says what is worth telling someone else. And the
fifth environment (`AdroitHandDoor-v1`) is marked as an **estimate awaiting a measured result** in
exactly one place; if you see that marker, it has not been replaced yet.
