# TensorBoard bundle — well-plate round, 2026-09-28

Event files only (no checkpoints) of the runs behind every result reported in
`RL_DT_docs/_docs_legion/reports/wellplate-round-2026-09-28.md`. Copied from
`RL_DT/_isaaclab_wellplate/WellPlate_RL/logs/` on the Legion laptop (4.6 GB there, mostly checkpoints that are in
neither repo; the event files of every run are also tracked in `RL_DT`).

## Open it

```bash
pip install tensorboard            # once, any Python 3.9+
tensorboard --logdir tensorboard_wellplate_2026-09-28 --port 6006
# then open http://localhost:6006
```

Good first views (Scalars tab, filter box):
- `Episode_Termination/success` — training success (with exploration noise; lower than the reported deterministic numbers)
- `Episode_Reward/` — each reward term, per episode
- `Loss/learning_rate` — rsl_rl's adaptive learning rate (the E5 finding)
- `Train/mean_reward` — total reward

Use the run filter (left pane) with the regexes below to show one curriculum at a time.

## Which folder is what (rsl_rl/wellplate/)

| Regex | Runs | What |
|---|---|---|
| `_stack$` | 09-26 stack runs | the 2-plate stack ladder (50.8 %) |
| `_centered$` | 08-06 … 10-59 | centred 2-plate curriculum C1a, C1b, C1c, C1, C2, C3 (90.6 %) |
| `_stack3b$` | 15-55 … 17-05 | second placement, rising stack h = 0, 6.5, 13, 19.5, 26 mm |
| `_stack3b$` | 17-38 / 18-43 / 22-08 | second placement B2 (E1 52.3 %), E2 all loose (46.1 %), E3b loose bottom (49.2 %) |
| `_stack3a$` | 20-16 … 21-46 | first placement onto a loose bottom plate, mass 20 kg → 50 g |
| `_e5_` / `_e5f_` | reach / align | E5 rsl_rl from scratch (adaptive / fixed learning rate) |

Other libraries (E5): `skrl/wellplate/*_ppo_torch`, `*_sac_torch` (23-45-10 is the failed first SAC start),
`rl_games/wellplate/*`, `sb3/Wellplate-{Reach,Align}-v0/*`. Their tag names differ (skrl: `Reward / …`;
rl_games: `rewards/…`, `info/last_lr`; SB3: `rollout/ep_rew_mean`).

Iteration numbers continue across warm starts, so the curricula line up end to end.
