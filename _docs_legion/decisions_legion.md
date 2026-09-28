# Decisions — `trossen-ai` (the Legion machine)

Companion to [`decisions.md`](../_docs/decisions.md), which is **not modified**. Append-only, newest last.
Each entry: what was chosen, why, and what it rules out.

---

## 2026-08-27 — Pin the kernel rather than chase the NVIDIA module

**Chose:** default-boot `6.17.0-14-generic` instead of the newest `6.17.0-35-generic`.

**Why:** no NVIDIA kernel module exists for `-35`, and the archive's module package has a
self-contradictory dependency on `nvidia-kernel-common-580` that apt cannot resolve. The older kernel
already has a working module. Point releases within the same series differ little for a workstation.

**Rules out:** kernel security updates beyond `-14` until this is revisited. **This is temporary** —
check periodically whether a matching module ships for a newer kernel. Details in
[`environment_legion.md`](environment_legion.md).

## 2026-08-28 — Fix the TF/Triton conflict by import ordering, not by pinning versions

**Chose:** pre-load Triton's native extension at package import, guarded so it does nothing when
TensorFlow is already loaded; plus lazy imports for the Keras agents, models and `Model` base class.

**Why:** the conflict is a load-order problem, not a version problem — either library works fine if
it loads first. Downgrading torch or TF would have been a larger, more disruptive change with its own
compatibility risk, and would not have helped the torch-only container case.

**Rules out:** nothing permanently; the patch is standalone in `_patches/` and reversible. Note the
guard is essential — without it, a caller that imports TF first (as several unit tests do) crashes.

**Side benefit:** cleared the blocker in [`strategy.md`](../_docs/strategy.md) Part 2 about the package not
importing in a torch-only container.

## 2026-08-28 — Do not fix `test_torch_td3.py`'s CPU assumption

**Chose:** document the 12 device-mismatch test failures rather than edit the tests.

**Why:** the agent is behaving correctly (it now genuinely uses the GPU); the tests assume CPU
tensors because they were written on a CPU-only laptop. There are two defensible fixes — make the
tests device-aware, or pin them to CPU — with a real trade-off (GPU coverage vs. minimal change).
That is Malachi's call on his own test suite, not a unilateral edit from here.

**Rules out:** nothing. Recorded as [D5](PUBLICATION_MATERIALS_legion.md#d5) for the conversation.

## 2026-08-29 — Install Isaac Sim 5.1.0, not the 5.0.0 that was downloaded

**Chose:** download and install 5.1.0 directly on this machine.

**Why:** Martin's USD assets were authored in 5.1, and the Docker container is pinned to 5.1.0. A
5.0.0 workstation install would be *older* than the assets — the riskier direction for USD schema
mismatches — and would mean two different Isaac Sim versions reading the same files. Alvika had
specifically flagged selecting 5.1.0 over the download page's default. 5.1.0 turned out to be
downloadable directly from this machine, so no flash-drive transfer was needed.

**Rules out:** nothing. The 5.0.0 zip is untouched in `~/Downloads` if it is ever wanted.

## 2026-08-29 — Keep both integration routes rather than choosing one

**Chose:** maintain the bare-Isaac-Sim route and the Isaac Lab + Docker route in parallel, in
separate toolkit copies.

**Why:** they serve different jobs and are not really competing.
[R5](PUBLICATION_MATERIALS_legion.md#r5) shows the direct route is faster per step at one environment
but cannot scale without reimplementing the parallelism Isaac Lab provides — and
[R3](PUBLICATION_MATERIALS_legion.md#r3) shows a single environment cannot even reach TD3's
`warmup_size`, so it cannot train. Conversely the direct route has a working GUI, no Docker
dependency, and is closer to a hardware-style control loop if the real robot becomes the target.

**Rules out:** consolidating on one route for now. Revisit if the direct route gains parallelism, or
if the hardware target firms up.

## 2026-08-29 — Separate toolkit copy per integration approach

**Chose:** `_toolkits/toolkit-isaaclab/` and `_toolkits/toolkit-isaacsim/`, each a full copy without
git history, line endings normalised to LF.

**Why (Dewei's reasoning):** the approaches will diverge — different imports, different device
handling, possibly incompatible adapters — and forcing one copy to serve both means constant merge
pain for no benefit. Separate copies are isolation, not duplication. Copies were taken from the
*working* toolkit rather than the pristine USB copy because the TF/Triton fix is required for the
toolkit to run on this machine at all; the standalone patch keeps the delta from upstream explicit.

**Rules out:** a single shared copy. Note this puts toolkit code inside `RL_DT`, which the root
`CLAUDE.md` rule (*"toolkit code goes there, notes go here"*) would otherwise forbid — a deliberate
exception, made viable because the upstream toolkit is public on GitHub.

## 2026-08-29 — Untrack `CLAUDE.md`

**Chose:** `git rm --cached CLAUDE.md` plus a `.gitignore` entry, so each machine keeps its own.

**Why:** it is machine-specific — paths, remotes, and GPU details differ between this box and the
PNNL workstation, and the PNNL machine can reach tanuki while this one cannot.

**Rules out:** a shared project map. **Cost worth watching:** `CLAUDE.md` is the file every session
reads first, so the two machines' maps will now drift silently. If that becomes a problem, the
alternative is a shared `CLAUDE.md` plus a gitignored `CLAUDE.local.md` for machine specifics.

## 2026-08-29 — Sync via a private personal GitHub repo

**Chose:** `github.com/Dewei-Wang-xx/RL4DT-Toolkit` (private) as the transport between this machine
and the PNNL computers.

**Why:** this machine cannot reach tanuki or the PNNL shared drives (see
[`environment_legion.md`](environment_legion.md)), OneDrive login fails here, and USB is inconvenient
for routine syncing. Git also gives history and honest diffs, which a file share would not.

**Rules out:** nothing technically. **Standing caveat:** this places PNNL work and colleagues' code
on personal infrastructure. The repo is private and the upstream toolkit is public, which limits the
exposure, but where the work should ultimately live is a question for Dewei, Malachi and Martin
rather than a settled decision.

## 2026-08-29 — Do not copy replay buffers or TensorBoard logs into the repo

**Chose:** keep every reward curve, config and the *final* checkpoint per run; exclude
`buffers/*.npy` and `events.out.tfevents*`.

**Why:** `results/` was 5.3 GB, dominated by replay buffers (regenerable training state) and
TensorBoard event files, with one 188 MB log exceeding GitHub's 100 MB file limit. The actual
scientific content — reward curves and configs — is under 1 MB; final checkpoints add ~20 MB.
Result: 617 MB → 42 MB, and a repo that clones in seconds on both machines.

**Rules out:** resuming training from a mid-run epoch on the other machine, and re-opening the
interactive TensorBoard curves there. Both remain available on this machine and on the USB copy.

## 2026-09-22 — Martin's robot only; fix the lift blocker on our side (Dewei)

**Chose:** keep Martin's Ridgeback + UR7e + Robotiq 2F-140 (`Ridgeback_UR7e_2f140.usd`); no Isaac Lab built-in robot.
Martin's GRIPPERFIX layer was checked and not used ([D16](PUBLICATION_MATERIALS_legion.md#d16)).

**Why:** the task is Martin's twin; a different robot would train a policy that does not transfer. The measured cause
turned out to be our own gripper setup ([D12](PUBLICATION_MATERIALS_legion.md#d12),
[D13](PUBLICATION_MATERIALS_legion.md#d13)), fixed in our Python with Martin's files untouched.

**Rules out:** swapping the gripper asset as the fix; waiting on Martin for a new robot file.

## 2026-09-26 — Robot gravity off for training; realistic arm as a later stage (Dewei)

**Chose:** `disable_gravity` on the robot's links (plates keep gravity); arm gains kept at 400 / 80. Commit 52616ad
(09-26 12:42).

**Why:** the stiff PD arm without compensation stalled 0.3–0.4 m short of IK targets (410 mm measured); a real UR
controller compensates gravity. Revisited on 09-27: gravity on + compensation torques tracks identically and the
trained policies transfer unchanged ([R10](PUBLICATION_MATERIALS_legion.md#r10)).

**Rules out:** training on an uncompensated gravity-on arm.

## 2026-09-26 — Bottom plate fixed first, loose later (Dewei)

**Chose:** the stack target kinematic for the 2-plate and centred stages; a loose (dynamic) bottom plate as its own
stage (E3, 09-27).

**Why:** stage the hardest contact physics last. E3 confirmed it needed its own curriculum (mass 20 kg → 50 g).

**Rules out:** nothing permanently — E3 now runs with a loose bottom plate.

## 2026-09-26 — Gate every stage on a deterministic evaluation (Claude)

**Chose:** stage gates and reported numbers come from `eval_policy.py` (mean action, 128 episodes), not from training
logs. Commit 387ef5b (09-26 14:06).

**Why:** with a binary gripper, exploration noise opens the grip at random: lift trained at 19.9 % but scored 87.5 %
deterministically ([M3](PUBLICATION_MATERIALS_legion.md#m3)).

**Rules out:** reporting training-log success as a result.

## 2026-09-26 — Centred-stack criteria 5 mm / 3° / 3°, released, 40 % gate (Dewei)

**Chose:** PLAN v4 (commit d91d264, 09-26 22:09): centring ≤ 5 mm, twist ≤ 3° (either end), tilt ≤ 3°, released
and at rest; ≥ 40 % of 128 deterministic episodes. The same per-plate criteria for three plates.

**Why:** a plate stack a lab can use; the gate leaves room for sampling noise while requiring a clear majority skill.

**Rules out:** reporting the looser 3 cm stack (50.8 %) as the stacking result.

## 2026-09-27 — Two skills instead of one policy for three plates (Claude, under the PLAN v5 autonomy rules)

**Chose:** the first placement by the C3 policy (later fine-tuned for a loose bottom plate), the second by a separate
policy trained from it; the evaluator switches by the environment's phase. Commit 0f69624 (09-27 08:14).

**Why:** three single-policy attempts failed with measured causes — a normaliser spike, the first skill overwritten
(swap test), then learned avoidance of grasping ([M5](PUBLICATION_MATERIALS_legion.md#m5)).

**Rules out, for now:** a single policy that decides when the first plate is done. Worth revisiting once the
two-skill baseline is solid.
