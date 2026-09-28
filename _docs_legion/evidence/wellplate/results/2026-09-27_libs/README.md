# Other RL libraries on the same task — E5 (PLAN v5, 2026-09-27)

Every library trained from scratch on the same Isaac Lab task ids, same 512 envs, same env-step budget, and was scored
by the same deterministic evaluation (64 envs × 2 episodes = 128; the Isaac Lab env's own termination terms). Settings
mirror the rsl_rl reference where a counterpart exists (MLP 512-256-128 ELU, 24-step rollouts, 5 epochs × 4 minibatches,
entropy 0.001, observation normalisation) — see `agents/*_cfg.yaml`. **One seed per run: a direction, not a variance.**

| Stage | Library / algorithm | Env steps | Wall-clock | Deterministic success |
|---|---|---|---|---|
| Reach | rsl_rl PPO (adaptive lr, reference) | 6.1 M | 14 min | 100 % |
| Reach | rsl_rl PPO (fixed lr 1e-4) | 6.1 M | 14 min | 100 % |
| Reach | skrl PPO | 6.1 M | 11 min | 100 % |
| Reach | rl_games PPO | 6.1 M | 13 min | 100 % |
| Reach | Stable-Baselines3 PPO | 6.1 M | 9 min | 0 % |
| Reach | skrl SAC | 6.1 M | 17 min | 0 % |
| Align | rsl_rl PPO (adaptive lr) | 12.3 M | 26 min | 3.9 % |
| Align | rsl_rl PPO (fixed lr 1e-4) | 12.3 M | 25 min | 0 % |
| Align | **skrl PPO** | 12.3 M | 24 min | **98.4 %** |
| Align | rl_games PPO | 12.3 M | 20 min | 0 % |
| Align | Stable-Baselines3 PPO | 12.3 M | 19 min | 0 % |
| Align | skrl SAC | 12.3 M | 37 min | 0 % |

Chart: `F9_libraries.png`. Full table with episode endings and checkpoints: `libs.md`; logs: `logs/`.

What the numbers say, and what they do not:
- Reach is easy for the three GPU-native PPO implementations (rsl_rl, skrl, rl_games), 11–14 min each.
- **Align from scratch separates them: only skrl PPO learned it (98.4 %).** The ladder never trained Align from
  scratch (it warm-started from Reach), so this is a harder test than the ladder itself.
- The skrl / rsl_rl gap is **not explained**. rsl_rl's KL-adaptive rate sat at its 1e-5 floor early (median 7.6e-5;
  skrl's median 1.4e-4), but rsl_rl with a fixed 1e-4 also scored 0 %. Untested differences: skrl normalises value
  targets, starts at a higher rate (~6e-4); seed luck is possible with one seed.
- Stable-Baselines3 PPO learned nothing in the budget: no KL-adaptive rate (fixed 3e-4), and its KL early stop (target
  0.01, measured 0.015) ends most updates after about one epoch. Its observation normalisation loaded correctly.
- skrl SAC with one gradient step per vectorised env step gets only 12 000 / 24 000 updates for 6.1 / 12.3 M env steps —
  far too few for an off-policy method at this scale; a fair SAC test needs more updates per step (and fewer envs).
- rl_games PPO: Reach 100 %, Align 0 %; its learning rate stayed healthy (median 2e-4), cause not investigated.

Next steps if a library switch is considered: 3 seeds per arm; skrl PPO vs rsl_rl with value normalisation; SAC with
more gradient steps; warm-started comparisons along the ladder.
