# Learning package — well-plate round (2026-09-22 → 09-28)

For Dewei: what this round did and the concepts behind it, so you can explain it, change it, and judge the next result.
It complements the original tracks in [`../../_docs/learn/`](../../_docs/learn/) (RL and TD3, the toolkit, Isaac and
rl_games, the door task) — start there if PPO or Isaac Lab are new.

| File | What | Time |
|---|---|---|
| [`slides.html`](slides.html) | **Start here.** 13 slides, one idea each, with the diagrams and charts. Offline; ← / → to move, P → Save as PDF. | 20 min |
| [`wellplate-rl-lessons.md`](wellplate-rl-lessons.md) | The full text: seven parts, each with the idea, what happened in our project, where it is in the code, and "check yourself" questions (answers at the end). | 3 h in parts |

## Checklist

- [ ] Part 0 — the round on one page
- [ ] Part 1 — how an Isaac Lab task is built (managers, terms, why warm starts work)
- [ ] Part 2 — robot, gripper, contacts, gravity compensation (the lift blocker; E4)
- [ ] Part 3 — PPO as we use it: input normaliser, rewards × dt, truncation vs termination, learning-rate schedule
- [ ] Part 4 — measuring honestly: deterministic evaluation, per-episode diagnosis, swap test
- [ ] Part 5 — curricula and skills: tolerance, rising stack, mass; two skills; hand-off start states
- [ ] Part 6 — other libraries: what E5 compared and what it did not settle
- [ ] The 16 "check yourself" questions, answered without looking
- [ ] Three hands-on exercises (Part 7): a `--diag_stack` evaluation, TensorBoard on the bundle, one predicted reward change

## Related

- Meeting slides: [`../presentations/2026-09-28-weekly/`](../presentations/2026-09-28-weekly/)
- Detailed round report: [`../reports/wellplate-round-2026-09-28.md`](../reports/wellplate-round-2026-09-28.md)
- How to show recordings and TensorBoard: [`../guides/SHOWING_PROGRESS.md`](../guides/SHOWING_PROGRESS.md)
- Chronology: [`PROGRESS.md`](../evidence/wellplate/PROGRESS.md)
