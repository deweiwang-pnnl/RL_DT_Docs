# Playing with the Digital Twin — a beginner's guide

Everything here is about the **digital twin only** (Isaac Sim + the robot scenes). Nothing here
touches the RL toolkit. Written for someone new to Ubuntu and Docker.

Status as of 2026-08-28: **working.** Isaac Sim runs, the door-opening scene loads, the robot
spawns, and training runs on the GPU.

---

## The mental model (read this once)

Isaac Sim is a huge program (~35 GB) that's awkward to install directly, so it lives inside a
**container** — a sealed box holding the program and everything it needs. Your files stay on your
computer and are "mounted" (made visible) inside that box.

Three pieces:

| Piece | Where it lives on your computer | What it is |
|---|---|---|
| Isaac Lab | `RL_Twin/isaaclab_dt-main/` | The container recipe + robot-learning framework (Alvika's) |
| The scenes and robots | `RL_Twin/digital_twin_models-DT_reorg/` | The 3D models — robots, labs, doors (Martin's) |
| The RL toolkit | `RL_Twin/SciOptControlToolkit/` | Not used here. Ignore for now. (Malachi's) |

Inside the container those appear at:
- `/workspace/isaaclab/` — Isaac Lab itself
- `/workspace/isaaclab/envs_external/` — the scenes and robots
- `/workspace/isaaclab/external_projects/` — the RL toolkit

**Important:** the container is a *running* thing, like an open application. Starting it is not the
same as installing it. Installing is already done; you just start and stop it.

---

## Everyday commands

### Is it running?
```bash
docker ps
```
If you see `isaac-lab-base` listed, it's running. If nothing lists, it's stopped.

### Start it
```bash
cd /home/aidev/RL_Twin/isaaclab_dt-main/docker
docker compose --env-file .env.base -f docker-compose.yaml --profile base up -d isaac-lab-base
```
(`-d` means "run in the background and give me my terminal back")

### Get inside it
```bash
docker exec -it isaac-lab-base bash
```
Your prompt changes — you're now "inside" the container. Type `exit` to leave. Leaving does **not**
stop it.

### Stop it
```bash
cd /home/aidev/RL_Twin/isaaclab_dt-main/docker
docker compose --env-file .env.base -f docker-compose.yaml down
```

---

## Run the door-opening task

This is the mobile robot (Ridgeback base + UR5e arm + gripper) learning to open an OpenTrons Flex door.

**From outside the container**, one line:
```bash
docker exec isaac-lab-base bash -c "cd /workspace/isaaclab/envs_external/RL_CloudTesting && /workspace/isaaclab/isaaclab.sh -p train_rl_games.py --task Isaac-UR5e-DoorOpen-v0 --num_envs 1 --max_iterations 1 --headless"
```

Breaking that down:
- `--task Isaac-UR5e-DoorOpen-v0` — which scenario. This is the only one set up so far.
- `--num_envs 1` — how many copies of the robot to simulate at once. **1 is for testing.** Real
  training uses 256–4096 copies in parallel (that's the whole point of Isaac Sim — massive
  parallelism). Start at 1 while learning, raise it later.
- `--max_iterations 1` — how many training rounds. 1 just proves it works. Real training: hundreds
  or thousands.
- `--headless` — don't draw graphics. Faster. See below for how to actually watch it.

Expect ~40 seconds even for this tiny run — Isaac Sim takes a while to start up every time. That's
normal, not a hang.

### What "it worked" looks like
Near the end you should see the robot spawn and physics start:
```
[INFO]: Time taken for scene creation : 1.19 seconds
[INFO]: Starting the simulation. This may take a few seconds. Please wait...
```
And a checkpoint file appears in
`digital_twin_models-DT_reorg/RL_CloudTesting/logs/rl_games/ur5e_door_open/<date>/nn/`.

### Warnings you can safely ignore
These all appear on a healthy run:
- `Not all actuators are configured! ... 7 != 15` — only some robot joints are motorized. Intended.
- `failed to cook GPU-compatible mesh, collision detection will fall back to CPU` — a few collision
  shapes are too complex for the GPU shortcut. Slower, still correct.
- `torch.cuda.amp.GradScaler is deprecated` — an old-style call inside a library. Harmless.
- `failed to open the default display. Can't verify X Server version` — expected in headless mode.
- `IOMMU is enabled` / `CPU performance profile is set to powersave` — performance hints, not errors.

---

## Actually watching the robot (the fun part)

Headless means "no picture." To *see* it, drop `--headless`:

```bash
docker exec -it isaac-lab-base bash -c "cd /workspace/isaaclab/envs_external/RL_CloudTesting && /workspace/isaaclab/isaaclab.sh -p train_rl_games.py --task Isaac-UR5e-DoorOpen-v0 --num_envs 1 --max_iterations 10"
```

**This may not work on the first try.** Graphics from inside a container need the container to be
allowed to draw on your screen, which usually means running this on your computer first:
```bash
xhost +local:docker
```
If the window still doesn't appear, the fallback is livestreaming instead (`--headless
--livestream 2`, then connect with NVIDIA's Isaac Sim WebRTC streaming client). I have not tested
either path yet — worth trying together when you have time, since seeing the robot move is the
best way to build intuition.

### Replaying a trained robot
Once you've trained something worth watching:
```bash
docker exec -it isaac-lab-base bash -c "cd /workspace/isaaclab/envs_external/RL_CloudTesting && /workspace/isaaclab/isaaclab.sh -p play_rl_games.py --task Isaac-UR5e-DoorOpen-v0 --checkpoint logs/rl_games/ur5e_door_open/<DATE>/nn/ur5e_door_open.pth"
```
Replace `<DATE>` with the actual folder name from your training run.

---

## Things to try, roughly easiest first

1. **Re-run the 1-iteration test.** Get comfortable with the start/stop/run cycle.
2. **Turn up the numbers.** `--num_envs 64 --max_iterations 50`. Watch it get slower but learn more.
   Then try 256. If you run out of GPU memory, lower it — 24 GB is plenty for this task, but not
   infinite.
3. **Watch TensorBoard.** Training writes graphs to the `summaries/` folder. From the toolkit's
   environment: `tensorboard --logdir /home/aidev/RL_Twin/digital_twin_models-DT_reorg/RL_CloudTesting/logs`
   then open http://localhost:6006 in a browser.
4. **Read the task definition.** `digital_twin_models-DT_reorg/RL_CloudTesting/ur5e_door_open_env_cfg.py`
   — this is where the scene, the robot, the rewards, and the reset behavior are all defined. It's
   the single most useful file for understanding how an Isaac Lab task is built.
5. **Open a scene in the Isaac Sim GUI** to look around without any RL. Requires the graphics setup
   from the section above.
6. **Explore the other scenes.** `envs_external/` has a tube-racking task, several lab environments,
   and various robots. Only the door task has RL code written for it so far.

---

## Running the RL toolkit against the digital twin

This is the newer path — Malachi's TD3 agent instead of the built-in `rl_games` PPO. Confirmed
working 2026-08-28.

```bash
docker exec isaac-lab-base bash -c "cd /workspace/isaaclab/envs_external/RL_CloudTesting && /workspace/isaaclab/isaaclab.sh -p train_toolkit_td3.py --num_envs 1 --nepisodes 2 --nsteps 30 --headless"
```

Expected output:
```
observation space : Box(-inf, inf, (43,), float32)
action space      : Box(-1.0, 1.0, (7,), float32)
agent             : TorchTD3 on cuda
Episode 0: steps=30 reward=1.308
```

**`--num_envs` must be 1 here.** The adapter that connects the two deliberately handles only the
single-robot case. This is fine for testing that things work, but it's slow — Isaac Sim is designed
to run hundreds of robots at once, and this uses one. Making the toolkit handle many robots in
parallel is the next real piece of work.

### How to inspect the environment yourself
If something doesn't line up, this prints exactly what the simulator hands back — shapes, types,
which device the data is on:
```bash
docker exec isaac-lab-base bash -c "cd /workspace/isaaclab/envs_external/RL_CloudTesting && /workspace/isaaclab/isaaclab.sh -p probe_door_env.py --num_envs 1 --headless"
```

### The three files involved
- `probe_door_env.py` — the inspector above. Read-only, changes nothing.
- `isaac_gym_adapter.py` — translates between Isaac Lab's format (batched GPU tensors) and the
  toolkit's (plain CPU arrays). Well commented; a good file to read to understand the mismatch.
- `train_toolkit_td3.py` — the actual experiment that runs TD3 on the door task.

---

## Where things are

| What | Path |
|---|---|
| Task code (door opening) | `digital_twin_models-DT_reorg/RL_CloudTesting/` |
| Task definition — scene, rewards, resets | `.../RL_CloudTesting/ur5e_door_open_env_cfg.py` |
| Training settings (learning rate, batch size…) | `.../RL_CloudTesting/rl_games_ppo_cfg.yaml` |
| The 3D scene file | `digital_twin_models-DT_reorg/ENV_OT_UR_door/TrainingScene_flattened.usd` |
| Training output and checkpoints | `.../RL_CloudTesting/logs/rl_games/ur5e_door_open/` |
| Container config (paths, versions) | `isaaclab_dt-main/docker/.env.base` |
| Asset catalog — every robot and scene | `digital_twin_models-DT_reorg/README.md` |

---

## Troubleshooting

**"permission denied ... docker.sock"** — your user needs to be in the `docker` group. Already done
on this machine, but it only takes effect after a logout or reboot.

**"nvidia-smi has failed"** (outside the container) — the GPU driver isn't loaded. This machine is
pinned to kernel `6.17.0-14-generic` because that's the one with a working NVIDIA driver module.
If a system update changes the boot kernel, this breaks. Check with `uname -r`.

**Changed `.env.base` and nothing happened** — mounts are fixed when the container is *created*.
Stop it (`down`), then start it again to pick up changes.

**"USD file not found"** — a scene path in a config file is wrong. Paths in
`ur5e_door_open_env_cfg.py` are relative to the folder you run the command from.

**Everything is slow** — the CPU is in powersave mode (there's a warning about this at startup).
Fine for testing; worth changing before long training runs.

---

## One thing that's edited from the original

`ur5e_door_open_env_cfg.py` line 30 originally read:
```python
USD_PATH = r"TrainingScene_flattened.usd"
```
It's now:
```python
USD_PATH = r"../ENV_OT_UR_door/TrainingScene_flattened.usd"
```
The scene file lives in a different folder than the task scripts, and the original path assumed
they were together. If you ever re-sync Martin's repo, this change may need reapplying. That line
sits under a comment reading "User-editable paths," so adjusting it per-setup appears to be expected.
