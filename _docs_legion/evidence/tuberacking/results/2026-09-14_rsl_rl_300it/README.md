# rsl_rl PPO, 300 iterations, 512 envs — 2026-09-14 17:15

Task `Template-Tuberacking-Rl-v0` (tube reach), working copy with table placed under the tube.
Run dir: `../../TubeRacking_RL/logs/rsl_rl/tube_reach/2026-09-14_17-15-28/` (checkpoints, TensorBoard, params).

| iteration | mean reward | episode length | success | tube_dropped |
|---|---|---|---|---|
| 0 | 0.77 | 289 | 0.00 | 0.04 |
| 299 | 0.98 | 72 | **0.86** | 0.04 |

Full curve every 25 iterations: `curve_every25.txt`. ~3–5 s/iteration on the RTX 5090 laptop.

Videos: `train_it000_untrained.mp4` (initial state, random policy), `train_it200.mp4`,
`play_model299_4envs.mp4` (final policy, 4 envs, 400 steps). Frames alongside.
Camera is the default viewer — set `env_cfg.viewer.eye/lookat` before recording for a demo.
