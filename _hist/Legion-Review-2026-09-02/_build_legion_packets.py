"""Build three printable packets from RL_DT/_docs_legion/.

    1  Legion-1-Story.pdf     the narrative + the asks — read this to present
    2  Legion-2-HandsOn.pdf    at the keyboard on Legion — the GUI and Docker guides
    3  Legion-3-Evidence.pdf   every number, defect, decision — reference, not a read

Markdown -> styled HTML -> Edge headless print-to-pdf. Same route as
_hist/Archived_08212026/_build_packets.py, which this is adapted from; no LaTeX or
weasyprint on this machine.

Run from anywhere:  python _build_legion_packets.py
Temporary .html files are written beside the PDFs and deleted at the end.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))          # …/RL_DT/_hist/Legion-Review-2026-09-02
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))      # …/RL_DT
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

SHA, DATE = "d827a53", "2026-09-02"

# --------------------------------------------------------------------------------------------
# What goes in each packet, in reading order. `note` is the one-line frame printed above the file.
# --------------------------------------------------------------------------------------------

STORY = [
    ("_docs_legion/README.md", "Stop 1 of 5 — the map, and the one caveat",
     "Two pages. Read its closing section 'The one thing to keep in mind' twice — it is the claim "
     "most easily lost when skimming, and the one most easily overclaimed in a meeting."),
    ("_docs_legion/session-2026-08-27-legion.md", "Stop 2 of 5 — the session report",
     "The core document, and the one written to be presented. Sections 1-7 are the spine of any "
     "talk. Note the honest-note block in section 1: a wrong diagnosis was recorded rather than "
     "quietly corrected."),
    ("_docs_legion/long-run-learning-2026-08-30.md", "Stop 3 of 5 — the headline result",
     "Written after stop 2 and it supersedes stop 2's open question. This is the most defensible "
     "result of the round: the task is not solvable as configured, measured rather than inferred."),
    ("_docs_legion/comparison-isaacsim-vs-isaaclab.md", "Stop 4 of 5 — the two routes, head to head",
     "Read its opening 'Read this before the numbers' first. The recommendation is keep both for "
     "different jobs — Isaac Lab to train, bare Isaac Sim to look and to map onto real hardware."),
    ("_docs_legion/team-discussion_legion.md", "Stop 5 of 5 — the asks, grouped by who can act",
     "The only file with actions attached: three items for Malachi, a blocking question for Martin, "
     "three notes for Alvika. STALE: its closing 'Team-wide' section predates stop 3 and still says "
     "every run was minutes long. Stop 3 wins."),
]

HANDSON = [
    ("_docs_legion/environment_legion.md", "Step 1 of 3 — the machine, and what will bite you",
     "Read the kernel-pin section before you touch a system update: the GPU driver module only "
     "exists for the pinned kernel, and a routine upgrade will take the GPU out. Also the disk "
     "layout, so the paths in steps 2 and 3 mean something."),
    ("_docs_legion/ISAAC_SIM_UI_GUIDE.md", "Step 2 of 3 — look at the twin (start here)",
     "The workstation Isaac Sim install, no Docker and no RL. Its 'Things to try' list, items 1-8 in "
     "order, is the actual session. Two sections to read before you start: the warnings you can "
     "safely ignore, and what could not be verified."),
    ("_docs_legion/DIGITAL_TWIN_HOWTO.md", "Step 3 of 3 — run the twin through Docker",
     "The training route. The 1-iteration smoke test is the thing to get working first. Watching it "
     "render from inside the container is the one part that was never made to work — xhost or "
     "WebRTC livestream, both untested."),
]

EVIDENCE = [
    ("_docs_legion/PUBLICATION_MATERIALS_legion.md", "Reference 1 — every number and every defect",
     "The single home for all of it: 6 results R1-R6, 11 defects D1-D11, 2 method notes. Scan the "
     "findings index, then read only what you need. Do not re-derive a number from anywhere else — "
     "if another document disagrees with this one, this one wins."),
    ("_docs_legion/WORKLOG_legion.md", "Reference 2 — what was done, round by round",
     "Two entries. The newest is the learning runs; below it the three-day integration round."),
    ("_docs_legion/rounds/Round-2026-08-27-legion-gpu-fix-and-dt-integration.md",
     "Reference 3 — the three days, hour by hour",
     "Provenance. Worth reading one section for its own sake: 'Mistakes made in this round'."),
    ("_docs_legion/decisions_legion.md", "Reference 4 — nine decisions, each with what it rules out",
     "Read this when you want to reopen something. Two of the nine now affect this machine: sync "
     "via GitHub rather than tanuki, and untracking CLAUDE.md."),
    ("_docs_legion/gpu-retest-2026-08-29.md", "Reference 5 — the Gymnasium re-test in detail",
     "Backs R1. Its 'why the old and new numbers are not directly comparable' section is the part "
     "that matters — do not put the old and new tables side by side in a slide."),
    ("_docs_legion/isaaclab-builtin-tests-2026-08-29.md", "Reference 6 — four Isaac Lab built-in tasks",
     "Backs R2. This is the evidence that the adapter is a general bridge rather than shaped around "
     "Martin's scene, which is the strongest reusability claim available."),
    ("_docs_legion/dt-via-isaaclab-2026-08-29.md", "Reference 7 — the 1 to 128 environment sweep",
     "Backs R3. Its 'why parallelism matters beyond speed' argument is the one worth carrying into "
     "a talk: at one environment TD3 cannot practically reach its own warmup threshold."),
]

CSS = """
@page { size: Letter; margin: 0.8in 0.85in; }
body { font-family: "Calibri","Segoe UI",sans-serif; font-size: 10pt; line-height: 1.4; color:#1a1a1a; }

/* cover */
.cover { page-break-after: always; }
.cover h1 { font-size: 26pt; margin: 1.3in 0 6pt 0; line-height: 1.15; }
.cover .sub { font-size: 12pt; color:#555; margin: 0 0 24pt 0; }
.cover .meta { font-size: 9pt; color:#777; margin-top: 30pt; }
.cover table { font-size: 9.5pt; }

/* section banner before each source file */
.banner { page-break-before: always; border-top: 2.5pt solid #14324f; padding-top: 5pt;
          margin-bottom: 12pt; }
.banner .lbl { font-size: 12pt; font-weight: bold; color:#14324f; }
.banner .src { font-family: Consolas, monospace; font-size: 8.5pt; color:#777; }
.banner .note { font-size: 9pt; color:#444; margin-top: 4pt; font-style: italic; }

h1 { font-size: 15pt; margin: 0 0 8pt 0; page-break-after: avoid; }
h2 { font-size: 12pt; margin: 15pt 0 5pt 0; padding-bottom: 2pt;
     border-bottom: 1px solid #ccc; page-break-after: avoid; }
h3 { font-size: 10.5pt; margin: 12pt 0 4pt 0; page-break-after: avoid; }
p, li { margin: 0 0 5pt 0; }
ul, ol { margin: 0 0 6pt 0; padding-left: 17pt; }
li { margin-bottom: 2.5pt; }
blockquote { margin: 0 0 8pt 0; padding: 6pt 9pt; background:#f6f7f9;
             border-left: 2.5pt solid #9bb0c4; font-size: 9.5pt; }
blockquote p:last-child { margin-bottom: 0; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background:#f2f2f2; padding:0 2px; }
pre { background:#f6f7f9; border:1px solid #e0e0e0; padding: 6pt 8pt; font-size: 8.5pt;
      line-height: 1.3; overflow-wrap: break-word; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.5pt; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 0 0 8pt 0;
        page-break-inside: avoid; }
th, td { border: 1px solid #d0d0d0; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background:#eef1f4; }
hr { border: none; border-top: 1px solid #ddd; margin: 12pt 0; }
"""


def delink(md: str) -> str:
    """Print artifact: relative links become plain labels, external links keep the URL once."""
    def repl(m):
        label, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://")):
            return f"{label} ({target})" if label.strip("`") != target else label
        return label
    return re.sub(r"\[([^\]]*)\]\(([^)\s]+)\)", repl, md)


def strip_frontmatter(md: str) -> str:
    m = re.match(r"^---\n.*?\n---\n", md, re.S)
    return md[m.end():] if m else md


def render(md: str) -> str:
    return markdown.markdown(
        strip_frontmatter(delink(md)),
        extensions=["extra", "sane_lists", "admonition"],
    )


def build(name: str, title: str, subtitle: str, intro_md: str, items) -> str:
    parts = [f'<div class="cover"><h1>{title}</h1><p class="sub">{subtitle}</p>',
             render(intro_md),
             f'<p class="meta">Generated {DATE} from RL_DT@{SHA}, which is the commit that pulled '
             f'the Legion work onto the PNNL machine. Assembled verbatim from the markdown sources '
             f'named in each section header; nothing was rewritten for this packet, and the framing '
             f'notes under each header are the only added text. Chromium print does not emit page '
             f'numbers, so the section banners are the navigation.</p></div>']
    total = 0
    for path, label, note in items:
        raw = io.open(os.path.join(REPO, path), encoding="utf-8").read()
        lines = raw.count("\n") + 1
        total += lines
        body, src = render(raw), f"RL_DT/{path} - {lines} lines"
        parts.append(f'<div class="banner"><div class="lbl">{label}</div>'
                     f'<div class="src">{src}</div>'
                     + (f'<div class="note">{note}</div>' if note else '')
                     + '</div>' + body)
    html = (f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>'
            f'<style>{CSS}</style></head><body>' + "\n".join(parts) + '</body></html>')
    htmlpath = os.path.join(HERE, f"_{name}.html")
    io.open(htmlpath, "w", encoding="utf-8").write(html)
    pdfpath = os.path.join(HERE, f"{name}.pdf")
    if os.path.exists(pdfpath):
        os.remove(pdfpath)

    # A fresh --user-data-dir per call, otherwise a second launch attaches to the still-shutting-down
    # instance from the previous one and exits 0 without writing anything.
    profile = tempfile.mkdtemp(prefix="edgepdf-")
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--user-data-dir={profile}",
                    f"--print-to-pdf={pdfpath}", "file:///" + htmlpath.replace("\\", "/")],
                   check=True, capture_output=True)
    for _ in range(60):                       # Edge can return before the file is flushed
        if os.path.exists(pdfpath) and os.path.getsize(pdfpath) > 0:
            break
        time.sleep(0.5)
    shutil.rmtree(profile, ignore_errors=True)
    if not os.path.exists(pdfpath):
        sys.exit(f"{name}: Edge exited without writing a PDF")
    os.remove(htmlpath)

    blob = io.open(pdfpath, "rb").read()
    pages = blob.count(b"/Type /Page\n") or blob.count(b"/Type/Page") or len(
        re.findall(rb"/Type\s*/Page(?![s/])", blob))
    print(f"{name}.pdf  {os.path.getsize(pdfpath):>8,} bytes  {pages:>3} pages  "
          f"{len(items)} sections  {total:,} source lines")
    return pdfpath


STORY_INTRO = """
## What this is

The Legion machine's work as a narrative, in five stops, for someone who has to **present it
tomorrow**. Read in this order — each stop assumes the one before.

| | Stop | Source | Lines |
|---|---|---|---|
| 1 | The map, and the one caveat | `README.md` | 76 |
| 2 | The session report — the core document | `session-2026-08-27-legion.md` | 250 |
| 3 | The headline result: neither route learns the task | `long-run-learning-2026-08-30.md` | 168 |
| 4 | The two integration routes, head to head | `comparison-isaacsim-vs-isaaclab.md` | 112 |
| 5 | The asks, grouped by who can act on them | `team-discussion_legion.md` | 190 |

## The three sentences to have ready

**What was built:** the RL toolkit now drives Martin's digital twin through two independent stacks
on the GPU — bare Isaac Sim and Isaac Lab + Docker — and the Isaac Lab adapter is general, since it
drove four Isaac Lab built-in tasks unchanged with observation dimensions from 4 to 60.

**What was found:** neither route learns to open the door, and the task **is not solvable as
configured**. The handle sits 0.834 m from an arm with roughly 0.85 m of reach, the mobile base is
not actuated, and every episode starts from the same pose. This was measured, not inferred.

**What is needed:** a decision from Martin on base actuation or start pose. Nothing else on the door
task matters until the gripper can reach the handle.

## The trap to avoid on stage

One route's reward **tripled** (105.8 → 334.3) and converged cleanly. That is real optimisation —
of the approach terms, which are the ones that pay. Replayed deterministically, the trained policy
moves the door in **0 of 6 episodes**. The 1.2% of training episodes where the door did move were
exploration noise, and the recorded peak of exactly 3.1416 rad is the hinge's −180° hard stop, i.e.
the door being *knocked* rather than pulled.

Presenting that curve as "learned to open the door" would be wrong in precisely the way the
project brief's no-brute-force rule exists to prevent. **A rising reward curve is not evidence of
task success** — logging door angle alongside reward is what made the diagnosis possible, and it is
the transferable lesson of the whole round.

## Two things to decide before you present

- **How to describe how this was produced.** The investigation, code and documents in this round
  were produced with an AI coding agent working under direction, over three days. Stop 2 raises this
  explicitly and leaves the decision open.
- **Whether the negative result leads or follows.** It is the most defensible thing here, and it is
  also the thing that sounds worst in a one-line summary. Leading with it and framing the plumbing
  as what made it findable is the stronger read.

## Not included

`session-2026-08-28-gpu-fix-and-dt-wiring.md` (297 lines) — the live progress log, explicitly
superseded by stop 2 and retained only because it records a wrong diagnosis being corrected. The
supporting per-experiment detail and every measured number are in the Evidence packet; the two
hands-on guides are in the Hands-on packet.
"""

HANDSON_INTRO = """
## What this is

The three documents you want **at the keyboard on Legion**, in order. Goal: open the digital twin,
look at it, click on it, press Play, then run the door task.

| | Step | Source | Lines |
|---|---|---|---|
| 1 | The machine, its paths, and the kernel pin | `environment_legion.md` | 154 |
| 2 | **Isaac Sim GUI — look at the twin** | `ISAAC_SIM_UI_GUIDE.md` | 190 |
| 3 | Docker + Isaac Lab — run the door task | `DIGITAL_TWIN_HOWTO.md` | 235 |

## Start here, literally

```bash
cd /home/aidev/isaacsim
./isaac-sim.sh
```

~16 seconds to "app ready". Then **File → Open** and load
`/home/aidev/RL_Twin/digital_twin_models-DT_reorg/RidgebackWithURGripper/RidgebackWithURGripper.usd`
— one robot, not the full lab. Orbit with left-drag. Select something in the Stage tree and press
**F** to fly the camera to it; that single key is the difference between exploring and being lost.

Then work down step 2's "Things to try" list, items 1 to 8. Item 5 opens
`ENV_OT_UR_door/TrainingScene_flattened.usd`, which is the exact scene the RL training uses, and
item 6 finds the prim that *is* the task:

```
/World/OpenTronsFlex/OpentronsDoorAdapter_large/LooRoll/Handle
```

Its `RevoluteJoint` is what "opening the door" physically means. Worth looking at, given the
measurement that the gripper cannot get within 20 cm of it.

## Four things that will confuse you, all expected

- **A scary asset warning on every load** — `Could not open asset @file:/C:/Users/prat615/…
  OpentronsDoorAdapter_large.usdc@`, a stale path to Martin's own Windows machine. **The handle is
  genuinely there anyway**; the geometry was baked in when the scene was flattened. This caused a
  false alarm on Legion before anyone checked properly.
- **`Not all actuators are configured! 7 != 15`** — intended. Only some joints are motorised, and
  that is the same fact as the reachability problem: the base DOF are not among them.
- **Play vs Stop.** Not playing, you are looking at a static scene. Playing, physics is live. Always
  press Stop before editing, per Martin's own README.
- **Two Isaac Sims on the box, deliberately.** The workstation install at `/home/aidev/isaacsim` is
  for looking; the Docker container is for training. Both pinned to **5.1.0**, because Martin's
  assets were authored in 5.1 and the download page defaults to something newer.

## Before you touch a system update

The GPU works only on the pinned kernel `6.17.0-14-generic`, which is the one with a matching NVIDIA
driver module. A routine Ubuntu upgrade that changes the boot kernel **takes the GPU out** —
`nvidia-smi` starts failing and nothing Isaac-related runs. Check with `uname -r`. Step 1 explains
the pin and how to revisit it.

## The one part that was never made to work

Rendering from *inside* the Docker container. Step 3 gives two candidate paths — `xhost +local:docker`
and `--headless --livestream 2` with NVIDIA's WebRTC client — and marks both untested. If you want to
watch a robot move, use the workstation GUI in step 2 instead; that route is verified.
"""

EVIDENCE_INTRO = """
## What this is

The provenance layer: every measured number, every code defect, every decision. **This is reference,
not a read.** Scan the findings index in Reference 1 and then look up only what you need — most
likely because someone in the meeting asked "how do you know that?".

| | Reference | Source | Lines |
|---|---|---|---|
| 1 | Every number and defect — R1-R6, D1-D11, M1-M2 | `PUBLICATION_MATERIALS_legion.md` | 361 |
| 2 | What was done, round by round | `WORKLOG_legion.md` | 103 |
| 3 | The three days, hour by hour | `rounds/Round-2026-08-27-…md` | 148 |
| 4 | Nine decisions, each with what it rules out | `decisions_legion.md` | 124 |
| 5 | The Gymnasium GPU re-test in detail | `gpu-retest-2026-08-29.md` | 80 |
| 6 | Four Isaac Lab built-in tasks | `isaaclab-builtin-tests-2026-08-29.md` | 67 |
| 7 | The 1 to 128 environment sweep | `dt-via-isaaclab-2026-08-29.md` | 67 |

**Single-sourcing rule.** A measured number or a code defect lives in Reference 1 and nowhere else.
If any other document disagrees with it, Reference 1 wins.

## The five findings most likely to be challenged

- **D10 — the handle is unreachable.** The blocking one. 0.834 m to the handle, ~0.85 m of reach,
  0.207 m closest approach over 300 sampled arm poses, base DOF not actuated, start pose fixed.
- **D9 — replay-buffer sampling is O(buffer).** `np.random.choice(…, replace=False)` permutes the
  whole buffer every call: 460× slower than `randint` at 200k entries, with the GPU at 3% while the
  CPU pegged. **This retroactively affects the published Gymnasium results** — short runs never fill
  the buffer enough to notice, long ones were throttled.
- **D1 — the TensorFlow/Triton conflict.** Two lines reproduce a segfault. The silent second symptom
  is worse: importing TF makes `torch.cuda.is_available()` return `False`, so torch agents have been
  running on CPU while reporting nothing wrong.
- **D11 — the fingertip prims do not resolve.** `left_inner_finger` and `right_inner_finger` return
  the same world transform as `wrist_3_link`, so the straddle test is `x > h AND x < h` — false for
  every input — which gated every door-opening reward term to zero.
- **M1 — why these numbers are not comparable to the published ones.** Different machine, CPU vs
  GPU, and the driver seeds from wall clock so nothing is reproducible either way. Read this before
  putting an old and a new table on the same slide.

## Two caveats that apply to nearly every number here

**Single seed, and the driver seeds from wall-clock time.** Nothing in this packet is reproducible
run to run, in either direction. Getting to three seeds with reported variance is the largest
outstanding weakness in the project's evidence.

**Throughput figures are order-of-magnitude.** Two episodes per configuration, with large
per-episode variance — 419 then 134 env-steps/s at the same 64 environments.
"""

if __name__ == "__main__":
    if not os.path.exists(EDGE):
        sys.exit(f"Edge not found at {EDGE}")
    build("Legion-1-Story", "Legion — the story",
          "What was built on the Legion machine, what it showed, and what to ask for",
          STORY_INTRO, STORY)
    build("Legion-2-HandsOn", "Legion — hands on the twin",
          "Opening, looking at, and running the digital twin on the Legion machine",
          HANDSON_INTRO, HANDSON)
    build("Legion-3-Evidence", "Legion — evidence and provenance",
          "Every measured number, every code defect, every decision",
          EVIDENCE_INTRO, EVIDENCE)
