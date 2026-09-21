# Round 2026-08-27 → 2026-08-29 — Legion machine: GPU fix and digital-twin integration

**Goal:** stand the project up on a new machine, then connect the RL toolkit to the digital twin.

**Status:** done. Three integration routes working; the toolkit runs on Blackwell GPUs; Isaac Sim
installed both as a container and as a workstation build.

Narrative record. Numbers and defects live in
[`../PUBLICATION_MATERIALS_legion.md`](../PUBLICATION_MATERIALS_legion.md).

---

## Day 1 (08-27) — the machine did not work

The project folder had been copied to `trossen-ai`, an Ubuntu box with an RTX 5090. Very little was
runnable:

- `nvidia-smi` failed. The GPU was physically present and the driver installed, but **no kernel module
  existed for the running kernel**. The archive's module package for `6.17.0-35-generic` has a
  self-contradictory dependency that apt cannot resolve, so the fix was to default-boot
  `6.17.0-14-generic`, which already had one. That needed `GRUB_DEFAULT=saved` as well —
  `grub-set-default` alone silently does nothing while `GRUB_DEFAULT=0` is set.
- The toolkit's `.venv` was a **Windows** virtualenv, unusable on Linux. Rebuilt with `uv`.
- `git-lfs` was missing; `isaaclab_dt-main/docker/.env.base` pointed at another machine's paths.
- The machine **cannot reach tanuki or the PNNL shared drives** — internal DNS resolves but every
  port refuses. So both DT repos exist here as extracted copies rather than clones, and the Isaac Lab
  image had to be built locally instead of pulled from the GitLab registry.

**A process note worth recording.** Early in this round several changes were made under what read as
a broad grant of overnight autonomy, and the user interrupted to stop it. The working mode for the
rest of the round became: propose a bounded plan, get explicit approval, then execute — which is how
everything after that point was done.

## Day 2 (08-28) — the toolkit could not run at all

`TorchTD3-v0` segfaulted a few milliseconds after start, before a single training step.

**A wrong turn first.** The crash was traced to Triton, PyTorch's GPU compiler, and web search turned
up genuine open PyTorch issues about Triton codegen segfaulting on `sm_120` (Blackwell) GPUs. That
looked like a match, and it was written up as an unfixable-locally upstream bug. **It was wrong.**

What corrected it was the user pointing out that the same code runs fine on their other machines. A
proper bisect then found the real cause: **TensorFlow and Triton ship conflicting native libraries,
and whichever loads second segfaults.** Two lines reproduce it. The toolkit's import order loaded TF
first — via the Keras agents, and via `torch.utils.tensorboard` — so Triton lost.

A second symptom turned out to matter independently: importing TF installs CUDA stubs that make
`torch.cuda.is_available()` return `False`. **Torch agents had been running on CPU while reporting
nothing wrong.**

The fix is five files: pre-load Triton at package import (guarded, so it does nothing if TF is
already loaded), and make the Keras agents, models and the TF-backed `Model` base class import
lazily. Keras agents were regression-tested and still train.

**The side effect was worth more than the fix.** Making the TF imports lazy cleared the blocker
already recorded in [`../strategy.md`](../../_docs/strategy.md) Part 2 — *"the package will not import in a
torch-only container"*. The Isaac Lab container has PyTorch but no TensorFlow at all. Without this,
none of the Isaac work would have been possible.

Also on day 2: the Isaac Lab image was built locally (34.7 GB), the container started with GPU
passthrough, and Martin's door task loaded and trained for one iteration — proving the digital twin
itself works. One trivial fix was needed: the scene USD was referenced by bare filename while living
one directory across.

A false alarm worth recording: the scene load warns about a missing
`C:/Users/prat615/.../OpentronsDoorAdapter_large.usdc`. It looked serious — that is the door handle
the robot must grasp — but the geometry was baked into the flattened USD and the prim is present and
valid. Checked rather than assumed, after initially raising it as a problem.

## Day 3 (08-29) — the seven-item list

With the toolkit working, the user set a list. Worked in the agreed order, committing after each.

**Step 0 — capture the fix.** The five-file change was uncommitted and existed only in a working
directory. Saved as a standalone patch with a full write-up in `_patches/`.

**#2 — Isaac Sim workstation install.** A 5.0.0 build had been downloaded from a PNNL machine, but
Alvika had flagged that 5.1.0 is required to match Martin's assets. 5.1.0 turned out to download
directly from this machine with no NGC login, so no flash-drive transfer was needed. Installed to
`/home/aidev/isaacsim`; verified it opens Martin's scene headlessly and that the **GUI reaches "app
ready" in ~16 s with no errors**. Wrote `ISAAC_SIM_UI_GUIDE.md` for exploring the twin visually,
marking explicitly which steps were verified and which could not be (nothing here can see the screen).

**#1 — re-test the published environments on GPU.** Four of five reproduced.
`FetchReachDense-Flat-v0` cannot start: an assertion inside gymnasium-robotics' own Fetch setup
against `mujoco 3.12.0`, before the toolkit is involved. Also found that `AdroitHandDoor`'s reward
function changed in gymnasium-robotics 1.2.1 *without a version bump*, so that number is not
comparable to the published one without pinning the same library version.

**#4 — toolkit against Isaac Lab built-ins.** Four tasks, observation dimensions from 4 to 60,
actions 1 to 8, all driven by the same adapter with no per-task code. This is the result that shows
the adapter is a real bridge rather than something shaped around the door task.

*A mistake of mine cost most of a day here.* The first harness looped over all four tasks inside one
Python process, closing and recreating environments. It **hung for 7 hours 40 minutes** — GPU at 0%,
process asleep, and nothing would ever have stopped it because I had set no timeout. Isaac Sim does
not support recreating an environment in one session. Restructured to one process per task with a
600 s timeout each; the same four tasks then finished in minutes.

**#5 — digital twin via Isaac Lab, scaled.** 1 → 128 environments. Throughput climbs ~11× to 16
environments then plateaus, because action selection is still one forward pass per environment in a
Python loop while the simulator steps them all together.

**#3 — the major task: digital twin via bare Isaac Sim.** No Isaac Lab, no Docker. `door_env_direct.py`
reimplements what Isaac Lab was providing — scene loading, observation assembly, action application,
reward, termination, reset. It works: 35 observations, 7 actions, on the GPU.

Rather than trust that "no crash" meant "correct", the signal path was verified against physics:
every prim path resolves, the articulation exposes 15 DOF with the expected names, and commanding the
hinge to −30°/−90°/−170° reads back within 2°. That check caught a real bug — **the door opens in the
negative direction**, so the first implementation scored a fully-opened door as zero reward.

**Scope stated rather than glossed:** the reward here is three terms against Martin's roughly ten
tuned terms across 1140 lines. Structurally equivalent task, not a reproduction.

**#6 — comparison.** Bare Isaac Sim is ~10× faster per step at one environment, but that gap is Isaac
Lab doing the work that makes many environments possible; Isaac Lab at 64 environments is ~3× the
direct route's best. The decisive point is not speed: `warmup_size` is 2500, so a single-environment
configuration **cannot practically reach the point where TD3 starts learning**. Recommendation is to
keep both routes — Isaac Lab for training, bare Isaac Sim for GUI exploration and as the starting
point if real hardware becomes the target.

**#7 — sync.** Dewei's own step. `RL_DT` now pushes to a private personal GitHub repo, since tanuki
is unreachable from here.

## Mistakes made in this round

Recorded because they cost real time and the reasoning is worth not repeating:

1. **Diagnosed the segfault wrong** and wrote it up confidently as an upstream PyTorch bug. Corrected
   only because the user said it works elsewhere. Lesson: when a user reports different behaviour on
   another machine, bisect rather than pattern-match to a plausible open issue.
2. **A 7h40m hang** from looping Isaac Sim environment creation in one process, made invisible by
   setting no timeout on the background job.
3. **Deleted `jlab_opt_control/buffers/`** with an rsync `--exclude='buffers'` intended for result
   data, which also matched the source package. Caught by a file-count comparison against the source.
4. **Raised a false alarm** about the missing door-handle asset before checking whether the prim
   actually resolved.

## Open at the end of this round

- Neither route has been shown to **learn** the door task. Every run was minutes long.
- `batch_action` on the agent is the highest-value next change — it is what caps throughput on both
  routes, and it is a change to Malachi's code rather than a wrapper.
- The kernel pin is temporary and should be revisited when Ubuntu ships a matching NVIDIA module.
- Three toolkit bugs are written up but not sent upstream — see
  [`../team-discussion_legion.md`](../team-discussion_legion.md).
- `FetchReach` remains unreproducible on this machine.
