# Toolkit → digital twin via Isaac Lab + Docker — 2026-08-29

The Isaac Lab route, run cleanly in sequence and measured across environment counts.
Counterpart to [`dt-via-isaacsim-direct`](#) (the bare Isaac Sim route, `_toolkits/toolkit-isaacsim/`).

## Setup

- Container `isaac-lab-base` (Isaac Sim 5.1.0 + Isaac Lab 2.3.2), RTX 5090
- Martin's assets mounted at `envs_external/`, toolkit at `external_projects/`
- Task `Isaac-UR5e-DoorOpen-v0`, obs 43, actions 7 (6 UR5e arm joints + gripper)
- `TorchTD3-v0` via `isaac_vec_adapter.IsaacVecBridge`, 2 episodes × 40 steps each

## Scaling results

| `--num_envs` | Env-steps/s (ep 0, ep 1) | Speed-up vs 1 env |
|---|---|---|
| 1 | 15, 17 | baseline |
| 16 | 191, 180 | ~11× |
| 64 | 419, 134 | ~9–25× |
| 128 | 271, 181 | ~12–17× |

All runs reported `TorchTD3 on cuda`. No timeouts, no errors.

**Throughput rises steeply to 16 environments, then flattens.** That plateau is expected and is
explained by a known limitation of the bridge: the simulator steps all N environments together on the
GPU, but **action selection is still one forward pass per environment** in a Python loop. Past a
certain N, that loop — not the physics — dominates. Removing it needs a `batch_action` method on the
agent, which is a real change to Malachi's code rather than a wrapper.

The per-episode variance (419 then 134 at 64 envs) is large enough that these numbers should be read
as "roughly an order of magnitude, then flat", not as precise measurements. Two episodes per
configuration is not enough to average out shader-compilation and cache effects on first touch.

## Why parallelism matters here beyond speed

`cfgs/torch_td3.cfg` sets `warmup_size: 2500` — TD3 takes random actions until 2500 transitions are
buffered, and only then begins learning. At 1 environment a 40-step episode contributes 40
transitions; at 128 it contributes 5120. **The single-environment configuration cannot realistically
reach the point where training starts**, which is why its rewards stay flat regardless of how long it
runs. This is the substantive argument for the vectorised bridge, more than the raw throughput.

## Rewards

Mean reward sits around 1.5–1.9 across all configurations, with no trend. That is expected: these are
2-episode runs of an essentially untrained policy. **Nothing here demonstrates learning**, and no
claim about learning should be made from this table. It demonstrates that the data path works end to
end at every scale tested.

## Files

Copied into `_toolkits/toolkit-isaaclab/isaac_integration/` so the tracked copy is self-contained:

| File | Role |
|---|---|
| `isaac_gym_adapter.py` | single-env adapter (`num_envs=1` only) |
| `isaac_vec_adapter.py` | vectorised bridge — N envs step together, N transitions fanned out |
| `train_toolkit_td3.py` | single-env training script |
| `train_toolkit_td3_vec.py` | vectorised training script (used here) |
| `probe_door_env.py` | diagnostic — dumps the env's real shapes, dtypes and devices |
| `run_dt_scaling.sh` | the scaling sweep that produced the table above |

## One fix that made this possible

Martin's `ur5e_door_open_env_cfg.py` referenced the scene USD by bare filename
(`TrainingScene_flattened.usd`) while the file lives in a sibling directory. Changed to
`../ENV_OT_UR_door/TrainingScene_flattened.usd`. The line sits under a comment reading
"User-editable paths", so adjusting it per setup appears to be expected rather than a defect.
