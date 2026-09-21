# Environment & machine setup

> Update this whenever paths, hardware, or the toolchain change. This is the file that lets
> you (or Alvika) pick the project up on a different computer.

## Getting running on a new machine

1. **Clone the repo**
   ```bash
   git clone https://tanuki.pnnl.gov/dewei.wang/rl-dt.git
   cd rl-dt
   git checkout develop
   ```
   Auth: PNNL GitLab requires a **personal access token** (scope `write_repository`), not a
   password. Git Credential Manager stores it after the first push. Set `user.email` to your
   PNNL address so GitLab attributes commits correctly.

2. **Re-obtain the reference material** (not in git — see "Reference material" below).

3. **Create the Python environment** (see "Python / PyTorch").

4. **Install Isaac Sim + Isaac Lab** if doing robot work (see "Isaac").

## Project layout on disk

The repo is a **subfolder** of a larger project directory. The parent holds the bulky reference
material, which is deliberately not version-controlled:

```
<PROJECT_ROOT>/
├── RL_DT/                  ← the git repo (this), branch develop
│   └── _docs/              ← all project documentation, see _docs/README.md
├── SciOptControlToolkit/   ← clone of JeffersonLab/SciOptControlToolkit, branch develop-dw
│                             a live working copy, NOT in this repo. Holds its own .venv.
└── _reference/             ← digital_twin_models-main, papers (~2 GB, NOT in git)
```

A clone gives you `_docs/`.
It does **not** give you `_reference/` or the toolkit clone.

### Known machines

`<PROJECT_ROOT>` is the **same string on both machines** because the folder is OneDrive-synced.
The path therefore does not tell you which machine you are on.
Check the hostname, or `torch.cuda.is_available()`.

| Machine | Hostname | GPU | Notes |
|---|---|---|---|
| Dewei, laptop | `WF10878` | Intel Arc, **no CUDA** | HP Elite x360 G11. Fine for Pendulum-scale TD3 on CPU. |
| Dewei, PNNL workstation | *(record it)* | NVIDIA RTX 5080 | Windows 11. The only machine that can run Isaac Sim. |

> **Do not hardcode `Z:\RL_Twin`.** A `Z:` alias resolved to this path on 2026-08-03 but by
> 2026-08-04 `Z:` was remapped to the network share `\\pnl\users\wang109`, which has no
> `RL_Twin`. Dead paths in config files were the result. Use the OneDrive path.

## Hardware

The workstation, not the laptop:

| | |
|---|---|
| GPU | **NVIDIA RTX 5080** (Blackwell, `sm_120`) |
| OS | Windows 11 |

**Blackwell caveat:** requires a **CUDA 12.8+ / `cu128`** PyTorch build. Older wheels either
fail to see the GPU or crash at the first kernel launch. Verify with:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Isaac Lab training on Linux is smoother than Windows; Windows is fine for inspection and
small runs. Record here if/when a Linux box or cluster becomes available.

## Python / PyTorch

- Target Python **3.10 / 3.11**
- PyTorch with the `cu128` index on the workstation (see above). CPU wheels on the laptop.

### Toolkit environment, installed 2026-08-12 and working

Lives in the toolkit clone, not here: `<PROJECT_ROOT>/SciOptControlToolkit/.venv`.

```bash
cd "<PROJECT_ROOT>/SciOptControlToolkit"
uv venv --python 3.11
uv pip install -r requirements.txt
uv pip install -e .
```

Resolved versions: Python 3.11.9, TensorFlow 2.21.0, torch 2.13.0+cpu, gymnasium 1.3.0,
numpy 2.4.6, pandas 3.0.5.
TF and torch coexist in the one env, and both report 0 GPUs on this laptop.
So `env.yaml`'s `python=3.13` pin is not a hard floor.

`pysindy` and `scikit-learn` are imported by the toolkit's notebooks but are in **neither**
`requirements.txt` nor `env.yaml` - install them separately.

## Isaac Sim / Isaac Lab

- **Isaac Sim 5.1+** (the DT assets were collected from 5.1 — older versions risk schema mismatches)
- **Isaac Lab** on top, launched via `isaaclab.sh -p <script>` (not bare `python`)

<!-- Record install path, version, and any patches once installed. -->

## Reference material (not in git)

Re-obtain these on a new machine and place them beside the repo as `_reference/`. Verified contents as
of 2026-08-19:

| Item | What it is | Source |
|---|---|---|
| `digital_twin_models-main/` | Isaac Sim USD assets (`AIRoboticsLab/`) + the preliminary `RL_CloudTesting/` door task | DT developer `prat615` |
| `T2_RoboticProjectA.pdf` | The project brief — the authority for the task | Malachi Schram |
| `Rajput_2025_…pdf`, `Colen_2026_…pdf` | The two MLST papers behind the physics-informed method | Malachi Schram / journal |
| `SciOptControlToolkit-wiki/`, `SciOptControlToolkit_Walkthrough.pdf` | Toolkit documentation | JLab |
| `TD3_Robotic_Arm_RL_Guide.pdf` | Background reading for [`learn/1-rl-and-td3.md`](learn/1-rl-and-td3.md) | — |

These are hundreds of MB (USD assets alone) — `.gitignore` blocks `*.usd*` deliberately.

`_reference/` also accumulates locally-produced material that is **not** part of the re-obtain list —
meeting notes, the `FAI Access` folder. Nothing depends on it; it is a scratch shelf outside the repo.

**The toolkit itself is not here.** It is a live clone at `<PROJECT_ROOT>/SciOptControlToolkit`
(`https://github.com/JeffersonLab/SciOptControlToolkit`, branch `develop-dw`) with its own `.venv`. An
older read-only copy used to sit in `_reference/` and no longer does; any path citing it is stale.

---

## Appendix — billing the VS Code Claude extension to FAI (AWS Bedrock)

How to route the Claude Code extension and CLI through the **FAI** AWS Bedrock account instead of the
personal `claude-pro` subscription, and back. FAI is **not** an Anthropic login — it is Amazon Bedrock
via an AWS SSO profile, turned on by environment variables rather than by `/login`.

**Prerequisites.** AWS CLI v2 on `PATH` (`aws --version`), and an SSO profile in `~/.aws/config`. There
is no static key in `~/.aws/credentials`; auth is a short-lived token cached under `~/.aws/sso/cache/`.

```ini
[profile fai]
sso_start_url  = https://pnnl.awsapps.com/start/#/
sso_region     = us-west-2
sso_account_id = 961272394507
sso_role_name  = PowerUserAccess
region         = us-west-2
```

**One-time setup.** The billing switch is a project-scoped `env` block in
`<PROJECT_ROOT>/.claude/settings.local.json` — already present. It applies to every session, terminal
or extension, whose working directory is under the project root, and it overrides the personal
`claude-pro` shell default there. `env` is read **at session start**, so add it before opening a
session, not during one. Leave the existing `permissions.allow` array untouched.

```json
"env": {
  "CLAUDE_CODE_USE_BEDROCK": "1",
  "AWS_PROFILE": "fai",
  "AWS_REGION": "us-west-2"
}
```

**Every working day.** Refresh the token in a normal terminal — *not* inside a Claude session:
`aws sso login --profile fai`. A browser opens for PNNL SSO. The refreshed token is shared across all
processes, so this is once per day, not once per session.

**Verify.** Open **the project root** in VS Code (starting from `RL_DT/` will not pick up the `env`
block), start a *fresh* session, and run `/status` — it should show a Bedrock endpoint, not the personal
Anthropic login.

**If the token expires mid-work** the session does not silently fall back to `claude-pro`; the next
request fails with an expired-credentials error and the transcript is intact. Run
`aws sso login --profile fai` in a terminal and resend the failed message — no restart needed.

**To go back to `claude-pro`:** delete the three Bedrock keys from `settings.local.json` (keeping
`permissions`), start a fresh session, and confirm with `/status`. Since `claude-pro` is the global
default, removing the override is all it takes.
