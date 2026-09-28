# Evidence — copies of the results the documents cite

Every report, presentation, round file and learning page in `_docs_legion/` links here, not into the code repo, so
this repo stands on its own. These are **snapshots** of the detailed record in `RL_DT` (PNNL GitLab), taken
**2026-09-28** from `RL_DT` commit `52bd669`.

| Folder | Copied from `RL_DT/…` | What |
|---|---|---|
| [`wellplate/results/`](wellplate/results/) | `_isaaclab_wellplate/results/` | every well-plate results folder: READMEs, charts, stills, videos, evaluation JSONs, stage tables — all except raw `*.log` files |
| [`wellplate/PROGRESS.md`](wellplate/PROGRESS.md) | `_isaaclab_wellplate/PROGRESS.md` | the complete chronology: every run, diagnosis and decision |
| [`wellplate/PLAN.md`](wellplate/PLAN.md) | `_isaaclab_wellplate/PLAN.md` | plans v3 → v5 with their definitions of done |
| [`wellplate/tensorboard/`](wellplate/tensorboard/) | selected `_isaaclab_wellplate/WellPlate_RL/logs/**/events.out.tfevents.*` | the 40 runs behind the reported results; `tensorboard --logdir wellplate/tensorboard` (its README maps runs to stages) |
| [`tuberacking/results/2026-09-14_rsl_rl_300it/`](tuberacking/results/2026-09-14_rsl_rl_300it/) | `_isaaclab_tuberacking/results/…` | the tube-racking run cited in Round-2026-09-14 |
| [`patches/`](patches/) | `_patches/` | the 2026-08-28 TensorFlow/Triton toolkit fix (README + patch), cited by the 08-27 round and reports |

**Not copied** (they stay in `RL_DT` as the detailed record): raw driver / training / evaluation logs (`*.log`), the
full TensorBoard logs of every run, and the code. Checkpoints are in neither repo — they stay on the Legion laptop;
the ones behind reported results are named in the results READMEs and `stages.md` files.

**Refresh** after new results (from the folder that holds both repos):

```bash
rsync -a --exclude '*.log' --exclude 'logs/' RL_DT/_isaaclab_wellplate/results/ RL_DT_docs/_docs_legion/evidence/wellplate/results/
cp RL_DT/_isaaclab_wellplate/{PROGRESS,PLAN}.md RL_DT_docs/_docs_legion/evidence/wellplate/
```
