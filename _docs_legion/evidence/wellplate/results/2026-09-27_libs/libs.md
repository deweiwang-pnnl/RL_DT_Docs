| stage | library / algorithm | env steps | wall-clock (min) | deterministic success | ends | checkpoint |
|---|---|---|---|---|---|---|
| Reach | rsl_rl | 6144000 | 14 | 1.000 | {'time_out': 0.0, 'plate_dropped': 0.0, 'arm_unstable': 0.0, 'success': 1.0} | WellPlate_RL/logs/rsl_rl/wellplate/2026-09-27_23-19-33_e5_reach/model_499.pt |
| Reach | skrl_ppo | 6144000 | 11 | 1.000 | {'success': 1.0} | WellPlate_RL/logs/skrl/wellplate/2026-09-27_23-33-44_ppo_torch/checkpoints/agent_12000.pt |
| Reach | skrl_sac | 6144000 | 0 | failed | see logs/train_Reach_skrl_sac.log | — |
| Reach | rl_games | 6144000 | 13 | 1.000 | {'success': 1.0} | WellPlate_RL/logs/rl_games/wellplate/2026-09-27_23-45-19/nn/last_wellplate_ep_500_rew__0.40663612_.pth |
| Reach | sb3 | 6144000 | 9 | 0.000 | {'time_out': 1.0} | WellPlate_RL/logs/sb3/Wellplate-Reach-v0/2026-09-27_23-58-00/model.zip |
| Align | rsl_rl | 12288000 | 26 | 0.039 | {'time_out': 0.9609, 'plate_dropped': 0.0, 'arm_unstable': 0.0, 'success': 0.0391} | WellPlate_RL/logs/rsl_rl/wellplate/2026-09-28_00-07-52_e5_align/model_999.pt |
| Align | skrl_ppo | 12288000 | 24 | 0.984 | {'success': 0.9844, 'plate_dropped': 0.0078, 'time_out': 0.0078} | WellPlate_RL/logs/skrl/wellplate/2026-09-28_00-34-13_ppo_torch/checkpoints/agent_24000.pt |
| Align | skrl_sac | 12288000 | 37 | 0.000 | {'time_out': 1.0} | WellPlate_RL/logs/skrl/wellplate/2026-09-28_00-58-39_sac_torch/checkpoints/agent_24000.pt |
| Align | rl_games | 12288000 | 20 | 0.000 | {'time_out': 1.0} | WellPlate_RL/logs/rl_games/wellplate/2026-09-28_01-36-00/nn/last_wellplate_ep_1000_rew__3.1670537_.pth |
| Align | sb3 | 12288000 | 19 | 0.000 | {'time_out': 1.0} | WellPlate_RL/logs/sb3/Wellplate-Align-v0/2026-09-28_01-56-24/model.zip |
| Reach | skrl_sac | 6144000 | 17 | 0.000 | {'time_out': 1.0} | WellPlate_RL/logs/skrl/wellplate/2026-09-28_02-15-37_sac_torch/checkpoints/agent_12000.pt |
| Reach | rsl_rl_fixed | 6144000 | 14 | 1.000 | {'time_out': 0.0, 'plate_dropped': 0.0, 'arm_unstable': 0.0, 'success': 1.0} | WellPlate_RL/logs/rsl_rl/wellplate/2026-09-28_02-33-03_e5f_reach/model_499.pt |
| Align | rsl_rl_fixed | 12288000 | 25 | 0.000 | {'time_out': 1.0, 'plate_dropped': 0.0, 'arm_unstable': 0.0, 'success': 0.0} | WellPlate_RL/logs/rsl_rl/wellplate/2026-09-28_02-46-47_e5f_align/model_999.pt |
