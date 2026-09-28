# Well-plate stacking — weekly meeting 2026-09-28

*Dewei Wang · Legion laptop (RTX 5090) · round 09-22 → 09-28 · evidence copies in [`../../evidence/`](../../evidence/), code in the `RL_DT` repo*

## Slides

| File | How to open |
|---|---|
| [`slides.html`](slides.html) | **Present from this.** Double-click, it opens in any browser, works offline. ← / → to move, F for full screen, P to print (one slide per page → "Save as PDF"). The videos play in the slides. |
| [`slides.md`](slides.md) | The same slides for Marp: VS Code extension "Marp for VS Code" → preview, and "Export Slide Deck" to **PowerPoint** or PDF. Videos are links there. |
| [`assets/`](assets/) | The 15 stills and charts used in the slides (reusable in any deck). |
| [`videos/`](videos/) | The 9 presentable videos (65 MB), copied from the results (all results: [`../../evidence/wellplate/results/`](../../evidence/wellplate/results/)): V1 gripper sweep, V2 grasp before/fixed, V3 lift before/after (two views), V4 2-plate stack, V5 centred before/after, V5b centred final, V6 / V7 three plates (overview / close-up). |

This folder is self-contained: the slides play the videos from `videos/`.

## What has been done (for the team, in five lines)

1. **The lift blocker was our gripper setup, not Martin's asset** — four defects (pad joint sign, grasp height, closing
   axis, contact settings), each measured and fixed; the grasp now holds 16 of 16 plates. Lift went from 0 % to 87.5 %.
2. **2-plate stack** 50.8 %, then **centred stacking** — within 5 mm, 3° twist, 3° tilt, released — **90.6 %**.
3. **Three plates** stacked, every plate starting loose, the bottom plate loose too, with a **realistic arm** (gravity
   on + compensation torques like a real UR controller): **54.7 %**.
4. What made it work: a twist observation; tolerance, stack-height and mass curricula; two skills (first / second
   placement) instead of one policy; training from recorded hand-offs; honest deterministic evaluation.
5. **Other libraries** on the same task: skrl, rl_games, Stable-Baselines3 (PPO, SAC). Only skrl PPO learned the
   harder stage from scratch; why is still open.

All numbers are deterministic evaluations over 128 episodes, one training seed each.

## What can be done later

| Next step | Why |
|---|---|
| 3 seeds per result, report variance | single seeds are the largest gap in the evidence |
| Reduce the final setting's 36 % time-outs and 9 % drops | the main room for improvement |
| One policy that chains both placements itself | today the environment switches the two skills |
| Domain randomisation (plate mass, friction, pick poses, base pose) | toward transfer to the real robot |
| Camera-based plate detection (Alvika's TubeRacking work) | the policy uses exact simulator poses now |
| skrl PPO vs rsl_rl: value normalisation, 3 seeds, along the ladder | decide whether switching library is worth it |

## Questions for the team

- **Martin:** the bottom plate renders black in our container although it uses the same mesh as the other two — known?
  One self-contained robot USD with the working gripper would still help.
- **Alvika:** can camera-based plate detection be reused from TubeRacking?
- **All:** are 5 mm / 3° / 3° the right tolerances for the real task? What is the next task after stacking?

## Where to read more

- Detailed report with all evidence: [`../../reports/wellplate-round-2026-09-28.md`](../../reports/wellplate-round-2026-09-28.md)
- How to show the recordings and TensorBoard: [`../../guides/SHOWING_PROGRESS.md`](../../guides/SHOWING_PROGRESS.md)
- Learning package (concepts behind this round, with slides): [`../../learn/`](../../learn/)
- Previous meeting: [`../2026-09-21-wellplate-status/`](../2026-09-21-wellplate-status/)
