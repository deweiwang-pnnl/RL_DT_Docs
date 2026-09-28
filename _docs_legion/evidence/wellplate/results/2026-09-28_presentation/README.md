# Assets for the 2026-09-28 weekly meeting

| File | What | Made by |
|---|---|---|
| `A1_three_plates_storyboard.png` | 6 stills of one successful three-plate episode (V6 frames 2022–2238, overview camera) | `scripts/make_presentation_assets.py` |
| `A2_three_plates_closeup.png` | white plate centred on the black one, yellow on top (V7 frames 2094, 2214) | same |
| `T1_training_curves.png` | training success per iteration (TensorBoard's view, noisy) vs each stage's deterministic evaluation, for the centred curriculum, the second-placement skill and the loose-bottom first-placement skill | `scripts/plot_training_curves.py` (host matplotlib) |
| `curves/*.csv` | the training-success series behind T1, one file per run | `make_presentation_assets.py` (reads the git-ignored TensorBoard logs) |

The slides, report, demo guide and learning package that use these are in
`RL_DT_docs/_docs_legion/` (`presentations/2026-09-28-weekly/`, `reports/wellplate-round-2026-09-28.md`,
`guides/SHOWING_PROGRESS.md`, `learn/`). A curated TensorBoard bundle (40 runs, 14 MB, not in git) is at
`RL_Twin/_exports/tensorboard_wellplate_2026-09-28.tar.gz` on the Legion laptop.
