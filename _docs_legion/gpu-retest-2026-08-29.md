# GPU re-test of the previously validated environments — 2026-08-29

Re-ran `TorchTD3-v0` on the environments recorded in
[`PUBLICATION_MATERIALS.md`](../_docs/PUBLICATION_MATERIALS.md), on the `trossen-ai` RTX 5090, after the
TF/triton fix ([`../_patches/README.md`](../_patches/README.md)) made the GPU actually usable.

## Why the old and new numbers are not directly comparable

Three things differ from the published runs, and all of them matter:

1. **The old runs were CPU-bound.** Before the fix, importing TensorFlow broke torch's CUDA
   detection, so the torch agent silently fell back to `Device: cpu` even on a GPU machine. The
   published numbers came from Dewei's CPU-only laptop anyway, but the mechanism is worth stating:
   any pre-fix "GPU" run was not using the GPU.
2. **The driver seeds from wall-clock time** (`run_continuous.py`), so no run is reproducible,
   old or new. Single seed per arm, as the roadmap already flags.
3. **Different machine, different library versions.** Notably `gymnasium-robotics` is 1.4.2 here.

Treat the table below as *"the toolkit still trains correctly on this machine"*, not as a
benchmark comparison.

## Results

Matched each environment's original episode/step counts.

| Environment | Episodes × steps | Final avg-20 | Wall time |
|---|---|---|---|
| `Pendulum-v1` | 100 × 200 | **−160.30** | 111 s |
| `MountainCarContinuous-v0` | 100 × 999 | **−1.02** | 477 s |
| `Hopper-v5` | 300 × 1000 | **187.10** | 71 s |
| `AdroitHandDoor-v1` | 20 × 200 | **−42.31** | 23 s |
| `FetchReachDense-Flat-v0` | 500 × 50 | **failed to start** | — |

All four successful runs reported `Device: cuda`.

## The FetchReach failure — a library problem, not a toolkit problem

```
gymnasium_robotics/utils/mujoco_utils.py:142 in set_joint_qpos
    assert joint_type in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE)
AssertionError
```

It fails in `gymnasium-robotics`' own Fetch setup code, before the toolkit is involved at all — the
environment cannot even be constructed. Versions here: `gymnasium-robotics 1.4.2`, `mujoco 3.12.0`,
`gymnasium 1.3.0`.

Confirmed Fetch-specific: `AdroitHandDoor-v1` constructs and trains fine on the same install, so
`envs/robotics_flat.py` and the flattening wrapper are not implicated. The whole Fetch family is
affected.

Likely fixes, untested: pin an older `gymnasium-robotics`, or an older `mujoco` matching what 1.4.2
expects. Worth resolving if the Fetch results matter for publication, since it is the one
environment from the published set that cannot currently be reproduced here.

## A second version caveat, on AdroitHandDoor

`gymnasium-robotics` prints on import:

> `AdroitHandDoorDense-v1` ... reward functions were updated in v1.2.1 without an environment
> version update. Therefore, use `gymnasium-robotics==1.2.0` for v1 reproducibility or use v2 in
> `gymnasium-robotics>=1.4.3`.

So the AdroitHandDoor reward function here may differ from the one behind the published numbers,
with no version-id change to signal it. The −42.31 above should not be compared against the
published AdroitHandDoor figure without first pinning the same library version.

## Dependency gap this exposed

`gymnasium-robotics` is in neither `requirements.txt` nor `env.yaml`, yet `envs/robotics_flat.py`
depends on it and `utests/test_registry.py::test_env` fails without it. Same category as the
`pysindy` / `scikit-learn` gap already noted in [`environment.md`](../_docs/environment.md). Installed here
as `gymnasium-robotics==1.4.2`; adding it (pinned) to `requirements.txt` would be a small, useful
upstream contribution.

## Where the runs live

`_toolkits/toolkit-isaaclab/results/<env-id>/index090_*` — reward curves (`results.npy`), configs,
and the final checkpoint per run. Replay buffers and TensorBoard event files are excluded from the
repo by size.
