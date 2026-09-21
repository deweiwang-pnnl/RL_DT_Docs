# Playing with the Digital Twin in the Isaac Sim GUI

A hands-on guide for exploring the digital twin visually — no Docker, no Isaac Lab, no RL.
Just you, the simulator, and Martin's robot and lab models.

**Verified on `trossen-ai`, 2026-08-29.** Isaac Sim 5.1.0, RTX 5090. Where a step could not be
verified without a person watching the screen, it says so explicitly.

---

## What this is

You have **two separate ways** to run Isaac Sim on this machine, and they do not interfere:

| | Where | Best for |
|---|---|---|
| **Docker container** | `isaac-lab-base` image | RL training (has Isaac Lab on top) |
| **Workstation install** | `/home/aidev/isaacsim` | **Looking at things** — this guide |

This guide covers the second. It is the one to use when you want to *see* the twin, click on it,
and understand how it is put together.

---

## Starting it

```bash
cd /home/aidev/isaacsim
./isaac-sim.sh
```

Takes ~16 seconds to reach "app ready". The first launch after install may take longer while shaders
compile — this is normal, not a hang.

Verified: launches cleanly, no errors, RTX renderer active on the RTX 5090.

To stop: close the window, or Ctrl-C in the terminal.

> If the window does not appear but the terminal shows startup messages, the display variable may be
> wrong. Try `DISPLAY=:1 ./isaac-sim.sh` — that is the display this machine uses.

---

## Opening the digital twin

**File → Open**, then navigate to:

```
/home/aidev/RL_Twin/digital_twin_models-DT_reorg/
```

Good places to start, easiest first:

| What | Path |
|---|---|
| **A single robot** (start here) | `RidgebackWithURGripper/RidgebackWithURGripper.usd` |
| **Just the gripper** | `Robotiq/2F140_reworked.usd` |
| **The door task scene** | `ENV_OT_UR_door/TrainingScene_flattened.usd` |
| **The full lab** | `ENV_ESCBench/ESCBench.usd` |
| **Tube racking task** | `ENV_TubeRacking_UR/TubeRacking.usd` |

The complete catalogue — every robot, scene, gripper and piece of labware — is in
`digital_twin_models-DT_reorg/README.md`. Worth reading; it is Martin's own description of what
each file is.

**Start with a single robot, not the full lab.** The lab scene has far more geometry and takes
longer to load; a lone robot makes it much easier to understand what you are looking at.

---

## Moving around

Standard Omniverse camera controls:

| Action | Control |
|---|---|
| Orbit | Left-drag |
| Pan | Middle-drag |
| Zoom | Right-drag, or scroll wheel |
| Focus on an object | Select it, press **F** |
| Look around from where you are | Hold right mouse, move |

**F is the one to remember.** Lost in space with nothing on screen? Click something in the Stage
tree, press F, and the camera flies to it.

---

## The panels that matter

- **Stage** (usually top-right) — the scene tree. Every object, nested. This is the most useful
  panel for understanding structure: expand the robot and you see its links and joints.
- **Property** (usually bottom-right) — details of whatever is selected. Position, physics
  settings, joint limits.
- **Viewport** — the 3D view itself.
- **Console** — messages and errors. Worth opening when something behaves oddly.

If you close something by accident: **Window → \<panel name\>** brings it back.

---

## Pressing Play

The **Play** button (▶, or the Spacebar) starts the physics simulation. **Stop** (■) resets it.

Important distinction, and a common source of confusion:
- **Not playing** — you are looking at a static scene. Moving things has no consequences.
- **Playing** — physics is live. Gravity applies, things fall, joints move, collisions happen.

Try this on a robot: press Play and watch. If it sags or settles slightly, that is gravity acting
on the joints — the simulation is working.

**Always press Stop before editing the scene.** Editing while playing produces confusing results,
and Martin's own gripper-test instructions in his README explicitly say to stop the sim first.

---

## Warnings you can safely ignore

These appear on a healthy load. They are noise, not problems:

- **`Could not open asset @file:/C:/Users/prat615/...OpentronsDoorAdapter_large.usdc@`**
  A stale reference to Martin's own Windows machine, left inside the flattened USD. **The door
  handle is genuinely present anyway** — verified: the prim
  `/World/OpenTronsFlex/OpentronsDoorAdapter_large/LooRoll/Handle` exists and is valid, with its
  mesh and revolute joint. The geometry was baked in when the scene was flattened, so the missing
  external reference does not matter. A red herring worth knowing about, because it looks alarming.
- **`ConvexMeshCookingTask: failed to cook GPU-compatible mesh ... fall back to CPU`**
  A few collision shapes are too complex for the GPU shortcut. Slower, still correct.
- **`Not all actuators are configured! ... 7 != 15`**
  Only some joints are motorised. Intended.
- **`Unhandled attribute type VtArray<std::string>`** — cosmetic material metadata.
- **`omni.isaac.dynamic_control is deprecated`** — an old API name. Harmless.

---

## Things to try, roughly in order

1. **Open one robot and orbit around it.** Get comfortable with the camera. Press F on different
   parts.
2. **Expand it in the Stage tree.** Find `base_link`, the arm links, the gripper fingers. This is
   how a robot is actually structured — a tree of links connected by joints.
3. **Click a joint, look at the Property panel.** Find its limits and its type (revolute = rotates,
   prismatic = slides).
4. **Press Play.** Watch gravity act. Press Stop.
5. **Open the door scene** (`ENV_OT_UR_door/TrainingScene_flattened.usd`). Find the OpenTrons
   machine, its door, and the handle the robot is supposed to grab. This is the exact scene the RL
   training uses — worth seeing what the agent is working with.
6. **Find the handle prim** at `/World/OpenTronsFlex/OpentronsDoorAdapter_large/LooRoll/Handle` in
   the Stage tree. Its `RevoluteJoint` is what "opening the door" physically means.
7. **Try Martin's gripper test.** His README has a Script Editor procedure for making the gripper
   grasp a cube. Follow it exactly — it assumes the GUI, and it is the best way to see the gripper
   actually work.
8. **Open the full lab** (`ENV_ESCBench/ESCBench.usd`) once the smaller scenes make sense.

---

## What I could not verify

Everything above about *launching* is tested: the app starts, reaches "app ready" in ~16s, loads
Martin's scene, finds the robot articulation, and steps physics without errors.

**The visual behaviour is not verified** — panel positions, exact menu labels, how the controls
feel, whether the scene looks right. Those come from Omniverse's standard interface and may differ
slightly in detail. If a menu is somewhere other than described, it is almost certainly present
under a nearby menu rather than missing.

---

## Where things are

| What | Path |
|---|---|
| Isaac Sim (workstation) | `/home/aidev/isaacsim/` |
| Launch script | `/home/aidev/isaacsim/isaac-sim.sh` |
| Its bundled Python | `/home/aidev/isaacsim/python.sh` |
| Martin's assets | `/home/aidev/RL_Twin/digital_twin_models-DT_reorg/` |
| Asset catalogue | `digital_twin_models-DT_reorg/README.md` |
| The Docker/RL path instead | [`DIGITAL_TWIN_HOWTO.md`](DIGITAL_TWIN_HOWTO.md) |

---

## Version note

This install is **5.1.0**, deliberately. NVIDIA's download page defaults to a newer version, and
Alvika specifically flagged selecting 5.1.0 — Martin's assets were authored in 5.1, and older or
newer runtimes risk USD schema mismatches. The Docker container is pinned to 5.1.0 too, so both
paths agree.

If you ever reinstall, check the version selector on the download page rather than taking the
default.
