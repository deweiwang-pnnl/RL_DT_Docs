"""Build the two reading packets as PDFs: RL_Twin-Learning.pdf and RL_Twin-Review.pdf.

Markdown -> styled HTML -> Edge headless print-to-pdf (the same route the meeting-notes PDF used;
no LaTeX engine or weasyprint on this machine).

Run from the project root:  python _build_packets.py
Temporary .html files are written beside the PDFs and deleted at the end.
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(ROOT, "RL_DT")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

SHA, DATE = "29f9573", "2026-08-21"

# --------------------------------------------------------------------------------------------
# What goes in each packet, in reading order. `note` is the one-line frame printed above the file.
# --------------------------------------------------------------------------------------------

LEARNING = [
    ("_docs/learn/README.md", "How to use this packet",
     "The tracks, the prerequisite chain, and the honest gaps. The review list at the end of this "
     "section is the other packet."),
    ("_docs/learn/4-door-task.md", "Stop 1 of 5 — why",
     "Part 1 is a faithful conversion of the brief and does not go stale. Parts 2-4 are "
     "interpretation; anything marked [dated] was written before we read the code."),
    ("_docs/learn/1-rl-and-td3.md", "Stop 2 of 5 — how",
     "The heavy one. Parts 1-2 are the sitting; Parts 3-4 and the appendix are lookup - do not try "
     "to absorb them in one pass."),
    (None, "Stop 3 of 5 — run the demo", None),          # placeholder page, script not included
    ("_docs/learn/3-isaac-and-rl-games.md", "Stop 4 of 5 — the task",
     "Part 1 is reading; Part 2 is a day at the keyboard. Nothing in it has been run - no RTX GPU on "
     "the laptop, so its verify-while-reading items are checks, not findings."),
    ("_docs/learn/2-toolkit.md", "Stop 5 of 5 — the codebase",
     "Read this when you next touch toolkit code. Use the reading order in its section 8 over a day "
     "at the keyboard."),
]

REVIEW = [
    ("CLAUDE.md", "Hop 1 of 5 — where the project stands",
     "The review list calls for section Current state, then section Roadmap. The rest is included "
     "because this file is the map and it is short."),
    ("_docs/PUBLICATION_MATERIALS.md", "Hop 2 of 5 — every number and every defect",
     "Scan the findings index first, then read only the entries that matter to you. The most "
     "valuable file in the repo."),
    ("_docs/WORKLOG.md", "Hop 3 of 5 — what was done, round by round",
     "The three round files it links to are NOT in this packet - open them in the repo only when you "
     "need provenance for a specific claim."),
    ("_docs/strategy.md", "Hop 4 of 5 — scope and the open architecture choice",
     "The review list calls for Parts 2 and 5. Part 4's A/B/C architecture choice is still open."),
    ("_docs/team-discussion.md", "Hop 5 of 5 — present, ask, propose",
     "The only file with an action attached. Its defect table deliberately repeats hop 2 - it is a "
     "handout for someone who will not follow links."),
]

DEMO_PAGE = """
# Stop 3 — run `td3_pendulum_demo.py`

Not included in this packet: you are running it separately. It is one self-contained file, 333
lines, at `RL_DT/_docs/learn/td3_pendulum_demo.py`.

```
python td3_pendulum_demo.py                 # ~60 episodes, should reach about -200
python td3_pendulum_demo.py --episodes 30   # shorter
python td3_pendulum_demo.py --seed 1        # different seed
python td3_pendulum_demo.py --eval-every 5  # evaluation cadence
```

**Read Stop 2 against this running.** The point of the demo is that the whole algorithm fits in one
file you can read top to bottom, with the hyperparameters as inline constants instead of in a cfg.

**Four things to watch for, each of which Stop 2 explains:**

- The **avg-20 training reward** climbing past -200 somewhere around episode 40-50. If it is still
  near -1200 after 30 episodes, something is wrong.
- The **two critic losses** moving together but not identically - they are independent estimators,
  and that is the whole point of clipped double-Q.
- The **actor loss going more negative** as the policy improves. It is `-Q(s, pi(s))`, so a falling
  number is a rising Q. It is not a loss in the usual sense and it does not converge to zero.
- **Every episode is 200 steps.** `terminated` is always `False` on Pendulum - the episode always
  truncates. A green run here does *not* validate termination handling, which is why the ported
  agent needed mutation testing.

The shipped agent is `jlab_opt_control/agents/torch_td3.py` in the toolkit clone, with its
hyperparameters in `cfgs/torch_td3.cfg`. This demo is a teaching artifact and a smoke test, not the
port.
"""

CSS = """
@page { size: Letter; margin: 0.8in 0.85in; }
body { font-family: "Calibri","Segoe UI",sans-serif; font-size: 10pt; line-height: 1.4; color:#1a1a1a; }

/* cover */
.cover { page-break-after: always; }
.cover h1 { font-size: 26pt; margin: 1.6in 0 6pt 0; line-height: 1.15; }
.cover .sub { font-size: 12pt; color:#555; margin: 0 0 28pt 0; }
.cover .meta { font-size: 9pt; color:#777; margin-top: 34pt; }
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
             f'<p class="meta">Generated {DATE} from RL_DT@{SHA}. Assembled from the markdown '
             f'sources named in each section header; nothing was rewritten for this packet. '
             f'Chromium print does not support page numbers, so the section banners are the '
             f'navigation.</p></div>']
    total = 0
    for path, label, note in items:
        if path is None:
            body, src, lines = render(DEMO_PAGE), "(not included - run it separately)", 0
        else:
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
    htmlpath = os.path.join(ROOT, f"_{name}.html")
    io.open(htmlpath, "w", encoding="utf-8").write(html)
    pdfpath = os.path.join(ROOT, f"{name}.pdf")
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdfpath}", "file:///" + htmlpath.replace("\\", "/")],
                   check=True, capture_output=True)
    os.remove(htmlpath)
    pages = len(re.findall(rb"/Type\s*/Page[^s]", io.open(pdfpath, "rb").read()))
    print(f"{name}.pdf  {os.path.getsize(pdfpath):>7,} bytes  {pages:>2} pages  "
          f"{len(items)} sections  {total:,} source lines")
    return pdfpath


LEARNING_INTRO = """
## What this is

The five learning stops, in reading order, combined into one document. Track 4 first for motivation,
then track 1 for the mechanics, then the demo, then the task, then the toolkit.

| | Stop | Source | Lines | Assumes |
|---|---|---|---|---|
| 1 | Why — the door task and the research framing | `learn/4-door-task.md` | 221 | - |
| 2 | How — RL and TD3, plus a PyTorch-vs-TensorFlow appendix | `learn/1-rl-and-td3.md` | 451 | - |
| 3 | **Run the demo** — not in this packet | `learn/td3_pendulum_demo.py` | 333 | Stop 2 |
| 4 | The task — Isaac Sim, Isaac Lab, and the existing rl_games door task | `learn/3-isaac-and-rl-games.md` | 218 | Stop 2 |
| 5 | The codebase — finding your way around `jlab_opt_control` | `learn/2-toolkit.md` | 181 | Stop 2 |

**The only hard rule is stop 2 before stops 4 and 5.** Stop 1 stands alone and can be read first for
motivation. If you would rather go strictly by track number, 4 -> 1 -> 2 -> 3 also satisfies every
prerequisite.

**Not included, and where to find it:** the runnable demo (you are running it separately),
`environment.md` if you need to get a machine going, and the three round files, which are provenance
rather than learning material.

**Where a track disagrees with a live file, the live file wins** - and where it disagrees with
gymnasium.farama.org, pytorch.org or the Isaac Lab docs, the docs win. Measured numbers and code
defects are not repeated in the tracks; they live in `PUBLICATION_MATERIALS.md`, which is in the
review packet.
"""

REVIEW_INTRO = """
## What this is

The whole record of what has been done, as five hops in order. No sixth file is needed, and none of
the learning tracks are on the list.

| | Hop | Source | Lines | Read for |
|---|---|---|---|---|
| 1 | Where the project stands | `CLAUDE.md` | 220 | Current state, then Roadmap. Start here so the rest has a frame. |
| 2 | Every measured number and every code defect | `_docs/PUBLICATION_MATERIALS.md` | 327 | The findings index, then the entries you care about. |
| 3 | What was done, round by round | `_docs/WORKLOG.md` | 150 | The index table, then the round entries. |
| 4 | Scope, and the architecture choice still open | `_docs/strategy.md` | 292 | Parts 2 and 5. |
| 5 | Present, ask, propose | `_docs/team-discussion.md` | 232 | All of it - it is short. |

**Two things to expect while reading.** Hops 2 and 3 overlap by design: the worklog says what was
done, publication materials says what is worth telling someone else. And the fifth environment
(`AdroitHandDoor-v1`) is marked as an estimate awaiting a measured result in exactly one place, in
hop 3 - if you see that marker, it has not been replaced yet.

**Not included, and deliberately.** The three round files under `_docs/rounds/` (838 lines) are
provenance - open them in the repo when a specific claim needs backing, not as part of this read.
`_docs/decisions.md` is not one of the five hops either; hops 4 and 5 cite the decisions that matter.
`_docs/environment.md` is setup, not record.
"""

if __name__ == "__main__":
    if not os.path.exists(EDGE):
        sys.exit(f"Edge not found at {EDGE}")
    build("RL_Twin-Learning", "Learning packet",
          "RL for a lab-automation digital twin - five stops, in reading order",
          LEARNING_INTRO, LEARNING)
    build("RL_Twin-Review", "Review packet",
          "RL for a lab-automation digital twin - the done work, in five hops",
          REVIEW_INTRO, REVIEW)
