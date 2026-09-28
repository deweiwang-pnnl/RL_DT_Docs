# `_patches/` — changes to the toolkit, kept separately

Patches against `SciOptControlToolkit` (upstream: <https://github.com/JeffersonLab/SciOptControlToolkit>,
branch `develop-dw`, base commit `5c928ff`). Kept here so the changes survive independently of any
particular working copy, and so the delta from Malachi's original stays explicit and reversible.

## `toolkit-tf-triton-fix.patch`

**What it fixes:** `TorchTD3-v0` segfaulted before running a single training step on the `trossen-ai`
machine (RTX 5090). The crash was inside `torch.optim.Adam` construction.

**Root cause:** TensorFlow and Triton (PyTorch's GPU compiler, pulled in lazily when an optimizer is
built) ship conflicting native libraries. **Whichever loads second segfaults.** The toolkit's import
order loaded TensorFlow first — via the Keras agents, and via `torch.utils.tensorboard`, which imports
TF — so Triton lost.

Two-line reproduction:

```python
import tensorflow          # then
import triton._C.libtriton  # -> segfault
```

Reverse the order and both load fine.

A second symptom, worth knowing independently: importing TF installs CUDA stub libraries that make
`torch.cuda.is_available()` return `False` with `Error 302: Error loading CUDA libraries`. The torch
agents therefore fell back to CPU silently, even when they did not crash.

**The fix — 5 files:**

| File | Change |
|---|---|
| `jlab_opt_control/__init__.py` | Pre-load `triton._C.libtriton` at package import, **guarded** by `if 'tensorflow' not in sys.modules`. This is the actual fix. |
| `agents/__init__.py` | Lazy (PEP 562) imports of the 7 Keras agents |
| `models/__init__.py` | Lazy imports of the 9 TF/Keras models |
| `core/__init__.py` | Lazy import of the TF-backed `Model` base class |
| `drivers/run_continuous.py` | TF imported only when a TF agent is requested; TensorBoard writer picks torch or TF backend to match |

**Why the guard matters:** if the *caller* imports TensorFlow before importing the toolkit (several
files in `utests/` do exactly that), TF has already won the race, and forcing Triton in afterwards is
precisely the crashing order. Without the guard, `utests/test_models.py` goes from 27-passed to
segfaulting.

**Bonus effect:** the lazy imports cleared the blocker recorded in
[`../_docs/strategy.md`](../_docs/strategy.md) Part 2 — *"the package will not import in a torch-only
container"*. The Isaac Lab container ships PyTorch but **no TensorFlow at all**, so an eager TF import
made `import jlab_opt_control` fail outright there. That is what made the digital-twin wiring possible.

**Verified on `trossen-ai` (2026-08-28):**
- `TorchTD3-v0` on `Pendulum-v1`, 100 episodes: crosses avg-20 of −200 at episode 61, ends **−132.3**,
  5m20s, on GPU (`Device: cuda`). The documented Keras baseline crosses at ep 47 and ends −163.0.
- `KerasTD3-v0` still trains — no regression to Malachi's existing agents.
- Test suite: 281 passed. The `test_torch_td3.py` failures that remain are a **separate, pre-existing
  issue** — see below.

**Applying it:**

```bash
cd <toolkit>
git apply /path/to/toolkit-tf-triton-fix.patch
```

**Portability note:** the fix should be harmless on machines that never had this bug (the guard means
it does nothing when TF is already loaded), so carrying it across machines is safe.

## Known issue this fix exposes (not caused by it)

With the fix applied, 12 tests in `utests/test_torch_td3.py` fail with:

```
Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!
```

Those tests build plain CPU tensors (`torch.randn(...)`, no device argument) while the agent's
networks now correctly live on the **GPU**. Before the fix, TF was breaking torch's CUDA detection, so
the agent silently fell back to CPU and everything accidentally matched. The tests were written and
validated on a CPU-only laptop, where the mismatch was impossible.

Evidence this is not a regression: on the **unmodified** toolkit these same tests do not merely fail,
they **segfault** — they could not run at all on this machine. And forcing the agent to CPU
(`"device": "cpu"` in `cfgs/torch_td3.cfg`) makes **all 47 pass**.

The agent is behaving correctly; the tests are not GPU-aware. Two ways to fix, worth a conversation
with Malachi rather than a unilateral edit:

1. Make the tests device-aware (build tensors on `agent.device`) — keeps GPU coverage, more edits.
2. Pin the tests to CPU explicitly — smallest change, but the GPU path then goes untested.

A separate, unrelated pre-existing failure: `utests/test_registry.py::test_env` needs
`gymnasium-robotics`, which is in neither `requirements.txt` nor `env.yaml`.
