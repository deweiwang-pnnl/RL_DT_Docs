# Toolkit vs Isaac Lab's built-in environments — 2026-08-29

**Question:** is `isaac_vec_adapter.py` a genuine toolkit↔Isaac Lab bridge, or does it only happen to
fit Martin's door task?

**Answer: it generalises.** Four built-in Isaac Lab tasks, spanning very different observation and
action shapes, all driven by `TorchTD3-v0` with **no per-task code**.

## Results

`--num_envs 16 --steps 30`, RTX 5090.

| Task | Obs | Actions | Mean reward | Throughput |
|---|---|---|---|---|
| `Isaac-Cartpole-v0` | 4 | 1 | −0.3505 | 659 env-steps/s |
| `Isaac-Ant-v0` | 60 | 8 | 0.0376 | 440 env-steps/s |
| `Isaac-Reach-Franka-v0` | 32 | 7 | −0.2214 | 257 env-steps/s |
| `Isaac-Open-Drawer-Franka-v0` | 31 | 8 | 0.6499 | 364 env-steps/s |

All four ran on `cuda`. **4/4 passed.**

Observation dimension ranges 4→60 and actions 1→8 across these tasks; the adapter handled every
combination unchanged. That is the evidence the bridge is real rather than door-task-shaped.

The rewards are meaningless as performance figures — 30 steps of a barely-initialised policy. They
are recorded only to show the reward path is live rather than returning zeros.

**`Isaac-Open-Drawer-Franka-v0` is the interesting one**: NVIDIA's cabinet-opening task, structurally
the same problem as Martin's door — articulated object, grasp a handle, pull it open. It is almost
certainly what the door task was modelled on, and it is worth reading alongside
`ur5e_door_open_env_cfg.py` to see which parts are NVIDIA convention and which are Martin's choices.

## A harness bug worth recording

The first version of this test looped over all four tasks **inside one Python process**, calling
`env.close()` then `gym.make()` for the next one. It **hung for 7 hours 40 minutes** — GPU pinned at
0% utilisation with 2.5 GB VRAM held, process sleeping, no output after Cartpole.

Isaac Sim does not reliably support tearing down an environment and creating another within a single
session. The task loop belongs in the shell, not in Python.

Fixed by splitting into:
- `test_one_builtin.py` — runs exactly one task, then exits
- `run_builtin_tests.sh` — loops over tasks, **one Isaac Sim process each**, with a 600 s `timeout`
  per task so a hang costs minutes rather than hours

Same four tasks then completed in a few minutes.

Two lessons, both mine rather than the toolkit's:
1. Never loop over Isaac Sim environment creation in one process.
2. Always put a timeout on a long-running background job. The 7h40m was invisible because nothing
   would ever have stopped it.

A minor related quirk: even the single-task processes linger during shutdown after writing their
results. Results are complete and correct before that point, so the wrapper's `timeout` handles it.

## Practical use beyond this test

`Isaac-Cartpole-v0` starts in seconds and has a 4-dimensional observation, which makes it a far
better debugging loop for adapter changes than waiting on the full lab scene. When something breaks
in the wiring, reproduce it there first.

## Files

- `digital_twin_models-DT_reorg/RL_CloudTesting/test_one_builtin.py`
- `digital_twin_models-DT_reorg/RL_CloudTesting/run_builtin_tests.sh`
- `isaac_vec_adapter.py` — the adapter under test, unchanged from the door-task work
