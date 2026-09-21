# Overnight session summary — 2026-08-28

Plain-language status. Updated live as each step happens.

## Approved plan
1. Check the toolkit's PyTorch build sees the RTX 5090
2. Fix it if it doesn't
3. Run a small Gymnasium training test (TD3 on Pendulum) to prove the toolkit works on this machine
4. Try to connect the toolkit to the Isaac Sim digital-twin environment (exploratory — may not fully succeed tonight, that's expected)
5. Keep this file updated throughout

## Progress

- **Step 1 (check GPU) — done, all good.** The toolkit's PyTorch (2.13.0, CUDA 13.0 build) already
  sees the GPU correctly: "NVIDIA GeForce RTX 5090 Laptop GPU". No fix needed.
- **Step 2 (reinstall torch) — skipped, not needed**, since step 1 already worked.
- **Step 3 (Gymnasium smoke test) — FAILED. Found a real bug, stopped here.**
  The first run looked like it succeeded (exit code 0), but that was misleading — it was piped
  through `tail` and the real process had actually crashed. Re-running directly showed the truth:
  the training script **crashes every time** (a segfault, not a normal error) a few milliseconds
  after starting, before a single training step runs.

  I traced it to an exact spot: in Malachi's toolkit, `jlab_opt_control/agents/torch_td3.py` line 171
  creates an Adam optimizer, and building that optimizer triggers PyTorch to load some of its internal
  "compiler" machinery — and *that* is what crashes. I tried four ways to work around it (hiding the
  GPU from the process entirely, disabling PyTorch's compiler flag) and it crashed the same way every
  time. That points to a real incompatibility between this specific PyTorch version (2.13, built for
  CUDA 13) and this GPU (RTX 5090 / "Blackwell" — a very new chip), not a mistake in how I ran it.

  **This is not something I fixed, and I stopped rather than guess further** — the likely real fix
  (using an older/different PyTorch version, or changing how the optimizer is created in Malachi's
  code) is a decision for you and Malachi, since it affects his toolkit's pinned dependencies.
  Confirmed **not** a TensorFlow conflict — a plain "import both, run a tiny PyTorch op" test worked
  fine; only the toolkit's actual optimizer setup crashes.

  **What this means for tonight's plan:** since this blocks the toolkit from training at all on this
  machine, I did **not** move on to step 4 (building the Isaac Sim image / trying to wire the toolkit
  to the digital twin) — that would reuse this same broken code path, so there was nothing to gain by
  building a 20GB image on top of a foundation that doesn't work yet.

- **Step 4, part A (digital twin setup) — very close, one small bug found and fixed.**
  Isaac Lab image built (34.7GB), container `isaac-lab-base` running, `nvidia-smi` confirmed working
  inside it (RTX 5090 via Vulkan), both mount points correct. **Isaac Sim itself launched
  successfully** — real milestone, the whole engine boots and sees the GPU correctly in this setup.
  First attempt to load the door-opening scene failed on something trivial: Martin's
  `ur5e_door_open_env_cfg.py` pointed at the scene file (`TrainingScene_flattened.usd`) by bare
  filename, but it actually lives in a different folder (`ENV_OT_UR_door/`, not `RL_CloudTesting/`
  where the task scripts are). You approved editing Martin's file too (confirmed it's local-only) —
  fixed the one-line path (it was already marked "User-editable paths" in his file, so this looks
  like an expected per-setup adjustment, not a bug in his design).

- **DIGITAL TWIN IS WORKING.** After the path fix, the door-opening task ran end to end: scene
  loaded (1.19s), the Ridgeback + UR5e robot spawned as a proper physics articulation, PPO training
  connected, ran on the GPU, and saved a checkpoint. Verified by finding the actual checkpoint file
  on disk, not just a clean exit code.
- **Wrote you a guide: `DIGITAL_TWIN_HOWTO.md`** (in `RL_Twin/`) — how to start/stop the container,
  run the door task, what the options mean, which scary-looking warnings are harmless, where
  everything lives, troubleshooting, and a list of things to try in rough order of difficulty.

## THE HEADLINE: the RL toolkit is now driving the digital twin

Malachi's `TorchTD3` agent successfully trained against Martin's door-opening robot inside Isaac
Sim, on the GPU, with no errors:

```
observation space : Box(-inf, inf, (43,), float32)     <- 43 numbers describing robot + door state
action space      : Box(-1.0, 1.0, (7,), float32)      <- 6 arm joints + 1 gripper
agent             : TorchTD3 on cuda
Episode 0: steps=30 reward=1.308
Episode 1: steps=30 reward=1.416
```

**This answers the "Option A" question you posed: yes, the toolkit can talk to the digital twin.**
It is not proven *efficient* yet (see the honest caveat below), but it is proven *possible*, which
is what we set out to determine.

### How the two were connected

Isaac Lab and the toolkit expect different things, so a small translation layer sits between them:

| | Isaac Lab gives you | The toolkit expects |
|---|---|---|
| Observations | GPU tensor, shape (1, 43), wrapped in a dict | plain CPU array, shape (43,) |
| Reward | GPU tensor with 1 element | a plain Python number |
| Done flags | GPU tensors | plain True/False |
| Actions | wants a GPU tensor, shape (1, 7) | produces a CPU array, shape (7,) |

`isaac_gym_adapter.py` (new file, in `RL_CloudTesting/`) does exactly that translation and nothing
else. Critically, **the agent needed no Isaac-specific code** — which was the design goal recorded in
`RL_DT/_docs/strategy.md` ("keep the agent/buffer/model layer free of any Isaac dependency").

### The honest caveat

This runs **one** robot at a time. Isaac Sim's whole advantage is simulating hundreds or thousands
in parallel on the GPU (Alvika/Martin's PPO setup defaults to 512). So this configuration is right
for *proving the connection works*, and wrong for *training at realistic speed*.

Making it fast means teaching TD3 and its replay buffer to handle batched data from many robots at
once — a real piece of work on the toolkit, and the natural next decision for you and Malachi. The
good news is the hard part (does it connect at all?) is now answered, and the remaining work is a
known, ordinary engineering task rather than an unknown.

### Addressing the "only one robot" limitation

I also built a second adapter that keeps the simulator parallel. The insight: nothing in the
toolkit's agent actually needs a *single* environment — it needs transitions handed over *one at a
time*. So N robots can step together on the GPU, and the N resulting transitions get fed to
`agent.memory()` one after another. The simulator runs at full speed; the replay buffer fills N
times faster per simulator step; **Malachi's agent code is untouched.**

Remaining inefficiency, stated honestly: choosing actions still costs N separate forward passes
instead of one batched pass. For this task (small networks, heavy physics) the simulator should
dominate, so this is likely still a big win — but it's the obvious next optimisation, and unlike
everything else here it would need a real change to the agent (a `batch_action` method).

**Benchmarked, and it works.** Same script, same machine, only `--num_envs` changed:

| Parallel robots | Throughput | Speed-up |
|---|---|---|
| 1 | 12–13 env-steps/s | baseline |
| 64 | 104–185 env-steps/s | **~9x** |

Not the full 64x, because action selection is still one-at-a-time (the known cost above) — but a 9x
gain for zero changes to Malachi's agent code. Pushing `--num_envs` higher (256, 512) will likely
help further; I stopped at 64 to leave headroom.

**Why this matters more than the raw speed:** TD3 only starts learning after `warmup_size` (2500)
transitions are collected. The single-env run stored just 1800 across 15 episodes, so **it never
actually trained** — it collected random actions the whole time. That's exactly why its rewards were
flat (~5.2-5.6, no trend). The 64-env run stored 15,360 transitions and cleared warmup comfortably,
so the agent genuinely trained. Parallelism isn't just a speed optimisation here; without it the
agent can't realistically reach the point where learning begins.

### New files (all in `digital_twin_models-DT_reorg/RL_CloudTesting/`)
- `isaac_gym_adapter.py` — single-env translation layer. Proven working.
- `train_toolkit_td3.py` — runs the toolkit's TD3 on the door task, one robot. **Proven working.**
- `probe_door_env.py` — a diagnostic that prints exactly what the Isaac env hands back. Useful
  whenever something doesn't line up; it's how the mismatch table above was measured.
- `isaac_vec_adapter.py` — the many-robot bridge described just above. Written, needs benchmarking.
- `train_toolkit_td3_vec.py` — the parallel training script, reports env-steps/second so you can
  compare directly against the single-env version. Written, needs benchmarking.

---

## RL toolkit crash — SOLVED (this was the blocker for all of the above)

**The toolkit now works on this machine, on the GPU.** TD3 trains, rewards improve, exit code 0.

**What was actually wrong:** TensorFlow and Triton (PyTorch's GPU compiler, which PyTorch loads
automatically when you build an Adam optimizer) each ship their own native libraries, and they
conflict. Whichever loads **second** crashes the process. The toolkit's import order made TensorFlow
load first, so Triton lost and died with a segfault.

Proof: `import TF, then triton` → crash. `import triton, then TF` → fine. Same machine, same versions.

**Why it works on your other computers:** they presumably load these in a different order, or have
different versions of the two libraries installed.

**The fix — four small edits, all in Malachi's toolkit:**
1. `jlab_opt_control/__init__.py` — pre-load Triton's native library at package import, before
   anything can pull in TensorFlow. This is the actual fix; the rest are supporting cleanups.
2. `jlab_opt_control/agents/__init__.py` — import the 7 Keras agents lazily instead of eagerly, so a
   torch-only run never loads TensorFlow at all.
3. `jlab_opt_control/core/__init__.py` — same lazy treatment for the TF-backed `Model` base class.
4. `jlab_opt_control/drivers/run_continuous.py` — TensorFlow is now only imported when a Keras agent
   is actually requested; TensorBoard logging picks the torch or TF writer to match the agent.

All four are commented in-place explaining why. **Keras agents were regression-tested and still
work** (`KerasTD3-v0` trains fine), so this doesn't break Malachi's existing agents.

**A regression I introduced and then fixed — worth knowing about.** My first version of the triton
pre-load broke the existing test suite: `utests/test_models.py` went from 27-passed to segfaulting.
Cause: those tests `import tensorflow` *before* importing the toolkit, so TF had already won the
race, and forcing triton in afterwards was exactly the crashing order. Fixed by guarding the
pre-load with `if 'tensorflow' not in sys.modules` — if TF got there first, leave well alone. Tests
now pass again (105 passed across registry/models/cli_kwargs), and the torch agent and the digital
twin wiring both still work.

### Full test suite: 281 passed, 13 failed, 10 skipped (39 min)

Two distinct groups of failures, neither of which is a bug I introduced:

**1. `test_registry.py::test_env` (1 failure)** — needs `gymnasium-robotics`, which isn't in
`requirements.txt` (same category of gap `_docs/environment.md` already records for `pysindy` /
`scikit-learn`). Pre-existing; verified against the original unmodified code.

**2. `test_torch_td3.py` (12 failures) — a real finding, and arguably good news.**
All fail with `Expected all tensors to be on the same device, but found cuda:0 and cpu`.

What's happening: the tests build plain CPU tensors (`torch.randn(...)`, no device argument), while
the agent's networks now correctly live on the **GPU**. Before tonight's fix, TensorFlow was breaking
torch's CUDA detection, so the agent silently fell back to CPU and everything accidentally matched.
These tests were written and validated on Dewei's CPU-only laptop, where a GPU mismatch was
impossible.

Proof it isn't a regression I caused: on the **original** code these same tests don't merely fail,
they **segfault** — they couldn't run at all on this machine. My fix made them runnable and, in doing
so, exposed a latent assumption. And forcing the agent back to CPU (`"device": "cpu"` in
`cfgs/torch_td3.cfg`) makes **all 47 pass**, which confirms the diagnosis exactly. I set that config
back to `"auto"` afterwards.

**The agent is behaving correctly; the tests just aren't GPU-aware.** I did not rewrite them, because
this is Malachi's test suite and there's a genuine design choice in how to fix it:
- make the tests device-aware (build tensors on `agent.device`) — keeps GPU coverage, more edits; or
- pin the tests to CPU explicitly — smallest change, but then the GPU path is never tested.

Worth a short conversation with Malachi rather than a unilateral edit from me.

**Bonus fix:** the torch agent now correctly reports `Device: cuda` instead of silently falling back
to `Device: cpu`. TensorFlow's CUDA stubs had been breaking torch's GPU detection, so even before the
crash, the torch agent was never actually using the GPU.

**A fifth edit, needed for the container:** `jlab_opt_control/models/__init__.py` got the same lazy
treatment. The Isaac Lab container ships PyTorch but **no TensorFlow at all**, so importing the
toolkit there failed outright with `ModuleNotFoundError: No module named 'tensorflow'`. This is
precisely the blocker already written up in `RL_DT/_docs/strategy.md` Part 2 ("the package will not
import in a torch-only container") — **that blocker is now cleared**, which is what made the digital
twin wiring possible.

### Full Pendulum baseline, for the record

Ran the documented 100-episode benchmark to confirm the fix produces real learning, not just a
non-crashing process:

| | This run (`TorchTD3-v0`, GPU) | Documented Keras baseline (CPU) |
|---|---|---|
| avg-20 crosses −200 | episode 61 | episode 47 |
| final avg-20 | **−132.3** | −163.0 |
| wall time | 5m20s | 4m34s |

Learning curve (avg-20, every 10 episodes): −1226 → −1221 → −1320 → −1325 → −727 → −253 → −233 →
−152 → −128 → −150. Slower to converge than the Keras arm but reaches a better final score. Single
seed, so treat as a smoke-test result and not a benchmark — the ≥3-seed work in the roadmap still
applies.

---

## Heads-up before you commit anything in the toolkit

`git status` in `SciOptControlToolkit` shows **80 files changed, ~10,000 lines**. That is almost
entirely misleading. The repo was copied from Windows, so every file has Windows-style line endings
(CRLF) that now read as changed on Linux. **I only actually changed 5 files:**

```
jlab_opt_control/__init__.py                 (+19)   <- the triton pre-load, the real fix
jlab_opt_control/agents/__init__.py          (+49)   <- lazy Keras agent imports
jlab_opt_control/core/__init__.py            (+24)   <- lazy TF Model import
jlab_opt_control/drivers/run_continuous.py   (+66)   <- TF only loaded for TF agents
jlab_opt_control/models/__init__.py          (+50)   <- lazy Keras model imports
```

To see just the real changes: `git diff --ignore-cr-at-eol`. **Do not `git add .`** here — it would
commit 75 files of pure line-ending churn along with the 5 real ones. This predates tonight; I did
not create it. Worth sorting out separately (a `.gitattributes` line-ending policy) before anything
goes upstream to Malachi.

Nothing has been committed anywhere. All changes sit in the working tree for you to review.

Also edited, outside the toolkit (both local-only, with your permission):
- `digital_twin_models-DT_reorg/RL_CloudTesting/ur5e_door_open_env_cfg.py` — one line, the scene path.
- 3 new files in that same folder (adapter, experiment, probe) — additions only, nothing overwritten.

---

## (OUTDATED — kept for the record) Earlier, incorrect diagnosis

I initially concluded this was a known upstream PyTorch bug affecting Blackwell/RTX 50-series GPUs
([pytorch/pytorch#176426](https://github.com/pytorch/pytorch/issues/176426)). **That was wrong** —
those issues are real but were not what was happening here. Your point that the same code works on
your other machines is what prompted a proper bisect, which found the real cause (see above). Left
here as a record of the wrong turn.
- **Applied a partial fix**: `jlab_opt_control/agents/torch_td3.py` lines ~171-179 now force
  `capturable=False, fused=False, foreach=False` on the three `Adam` optimizers, which stops PyTorch
  from choosing the buggy compiled fast-path. This is a real edit to Malachi's toolkit, done with your
  permission (uncommitted — sitting in the working tree only, not committed to git).
- **Result: only partially works.** The *first* `Adam` construction (actor optimizer) now succeeds.
  The *second* one (first critic optimizer) still segfaults, even with the same flags. So there's
  something about repeated optimizer construction in the same process that still trips this bug —
  not fully root-caused tonight.
- **Not yet done:** didn't chase this further tonight in order to prioritize getting the digital twin
  itself running, per your request. This still needs more digging or an upstream PyTorch fix before
  the toolkit can train on this GPU.
- **Step 4 (Isaac Sim / digital twin wiring with the toolkit)** — still blocked on the above, since
  it needs a working `TorchTD3-v0` agent.
- **Toolkit generalization scope** — still an open conversation with you and Malachi, not touched tonight.

## Everything else from tonight (for reference)
- GPU driver is fixed and confirmed working (RTX 5090, CUDA 13.0) — see kernel note below.
- Fixed the Isaac Lab Docker config (`isaaclab_dt-main/docker/.env.base`) to point at this machine's
  actual folder locations after your reorg — not yet tested end-to-end since step 4 didn't start.
- Machine is now permanently set to boot kernel `6.17.0-14-generic` (the one with a working NVIDIA
  driver module) instead of the newest one — worth switching back once Ubuntu ships a matching driver
  module for a newer kernel.
- Leftover from crash-testing tonight, safe to delete whenever, didn't clean these up myself without asking:
  `SciOptControlToolkit/results/Pendulum_smoketest/`, `Pendulum_debug/`, `Pendulum_debug2/`,
  `Pendulum_debug3/`, `Pendulum_debug4/` — all just near-empty config folders from crashed runs, no
  real results in any of them.
