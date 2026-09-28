# 2026-09-26 — gripper fix evidence (PLAN v3, Part A)

**Result: the grasp works.** Gripper variant G2 + the reference contact physics holds 16/16 plates, lifted 10 cm,
tilt 0.6°, closing on the plate's 85 mm side (`grasp_G2_ilphys.json`, repeated with the new defaults and no overrides:
`grasp_G2_default.json`).

| File | What it shows |
|---|---|
| `F1_pad_height_during_close.png` | pad bottoms vs pad gap in each setup's grasp pose: G0 reaches the plate 1 mm above the table with the pads in a V; the fix touches 3 mm above with parallel pads |
| `F2_pad_tilt.png` | pad tilt while closing in the air: G0 up to 24°, G1/G2 0.0° |
| `F3_pad_gap.png` | pad gap vs finger angle; G1/G2 match the four-bar prediction, 85 mm at 0.35 rad |
| `V1_sweep_G0_vs_G1.mp4` (+ `_frame200.png`) | the same close in the air, same camera: V vs parallel |
| `V2_grasp_G0_vs_fixed.mp4` (+ `_frame520.png`) | grasp and lift, 09-20 setup vs the fix |
| `S1_grasp_sequence.png` | pre-grasp → closing → closed → lifted (fixed setup) |
| `sweep_G*.csv/.mp4/.log` | raw sweep data (probe_gripper_sweep.py, robot gravity off, no plate) |
| `grasp_G*.json/.log/.mp4` | grasp probe runs (probe_grasp_ab.py) — see the chronology below |

Chronology of the grasp runs (all 09-26, scripted joint-space positioning unless noted):
1. `grasp_G0/G1/G2` first versions — invalid positioning (align policy 4–9 cm off, then relative-IK plateau); overwritten.
2. `grasp_G1*.png` straddling the 128 mm side → `CLOSING_AXIS_INDEX` was wrong since 09-20 21:45 (measured plate body x = 127.6 mm, y = 85.4 mm). Fixed to 1.
3. `grasp_G1.json`, `grasp_G2.json`, `grasp_G0.json` — pads glide through the plate once both touch it (a single pad pushes it fine). `grasp_G1_{depen5,effort2,vel02,mass02}.json`: none of those knobs alone fixes it.
4. `grasp_G1_ilphys*` — Isaac Lab's reference contact settings: pads stop at the plate, but G1's hard all-joint drives spin the plate out.
5. `grasp_G2_ilphys*` — **16/16 held, level. Gate passed.** Adopted as the default (`scene.py`: GRIPPER_VARIANT G2, REFERENCE_PHYSICS).
