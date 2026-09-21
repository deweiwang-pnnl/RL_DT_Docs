# Environment — `trossen-ai` (the Legion machine)

Companion to [`environment.md`](../_docs/environment.md), which describes Dewei's laptop and the PNNL
workstation. **That file is not modified**; this one records the machine the 2026-08-27/29 work ran
on. Where the two disagree about paths or tooling, they are describing different computers.

## The machine

| | |
|---|---|
| Hostname | `trossen-ai` |
| OS | Ubuntu 24.04.2 LTS (Noble) |
| Kernel | **`6.17.0-14-generic`, pinned — see below** |
| CPU | Intel Core Ultra 9 275HX, 24 cores |
| RAM | 64 GB |
| GPU | **NVIDIA GeForce RTX 5090 Laptop**, 24 GB, Blackwell (`sm_120`) |
| Driver | 580.126.09, CUDA 13.0 |

## The kernel pin — do not undo this casually

`nvidia-smi` failed on arrival. The GPU was present and `nvidia-driver-580-open` was installed, but
**no NVIDIA kernel module existed for the running kernel** (`6.17.0-35-generic`). Installed module
packages covered only `6.17.0-14` and `6.14.0-37`.

Installing the matching module for `-35` is not currently possible: the archive's
`linux-modules-nvidia-580-open-6.17.0-35-generic` depends on `nvidia-kernel-common-580` in a version
range that contradicts what the archive actually ships (`>= 580.159.03` and `<= 580.159.03-1`, while
the archive has `580.173.02`). Apt cannot resolve it.

**Resolution applied:** permanently default-boot the older kernel, which already has a working module.

```bash
sudo grub-set-default 'Advanced options for Ubuntu>Ubuntu, with Linux 6.17.0-14-generic'
```

This alone was **not** enough: `/etc/default/grub` had `GRUB_DEFAULT=0`, which hard-codes booting
entry 0 and ignores the saved entry. It also needed:

```bash
sudo sed -i 's/^GRUB_DEFAULT=0/GRUB_DEFAULT=saved/' /etc/default/grub
sudo update-grub
```

**This is a "for now" fix, not permanent.** Periodically check whether Ubuntu ships a matching
`580-open` module for a newer kernel and move back, so the machine keeps receiving kernel security
updates. Check with `uname -r` and `dpkg -l | grep linux-modules-nvidia`.

## Network — what this machine can and cannot reach

On the `pnnl-devices` wifi. It has a PNNL-internal IP (130.20.215.70) and PNNL internal DNS, but is
firewalled off from internal services — it is an unregistered-device network.

| Target | Reachable |
|---|---|
| Internet (github.com, pypi, nvcr.io, NVIDIA downloads) | **yes** |
| `tanuki.pnnl.gov` (PNNL GitLab) | **no** — resolves to 172.26.60.16 but every port refuses |
| `\\pnl\users`, `\\pnl\projects` | **no** — does not resolve, SMB blocked |

**DNS resolution is not access.** `tanuki.pnnl.gov` resolving misled an early check here; a TCP
connect to 443/80/22 all fail. Test connectivity, not name lookup.

Consequences: repos cannot be cloned or pulled from tanuki, so `digital_twin_models-DT_reorg` and
`isaaclab_dt-main` exist here as **extracted copies, not git clones** — they cannot receive updates.
The Isaac Lab image had to be built locally rather than pulled from the GitLab registry. Syncing to
PNNL machines goes through a personal GitHub repo instead (see `WORKLOG_legion.md`).

## Disk layout

```
/home/aidev/RL_Twin/
├── RL_DT/                        the git repo (github.com/Dewei-Wang-xx/RL4DT-Toolkit)
│   ├── _docs/                    documentation, including these _legion files
│   ├── _patches/                 the TF/triton fix, standalone
│   └── _toolkits/
│       ├── toolkit-isaaclab/     copy for the Isaac Lab + Docker route
│       └── toolkit-isaacsim/     copy for the bare Isaac Sim route
├── SciOptControlToolkit/         the working toolkit clone (branch develop-dw)
├── digital_twin_models-DT_reorg/ Martin's USD assets (extracted, not a clone)
├── isaaclab_dt-main/             Alvika's Isaac Lab fork (extracted, not a clone)
└── _reference/                   papers, older copies (~4 GB)

/home/aidev/isaacsim/             Isaac Sim 5.1.0 workstation install (17 GB)
```

Disk: 1.9 TB total, ~1.3 TB free. Docker holds ~143 GB (of which ~62 GB is reclaimable build cache
via `docker builder prune`).

## Python and the toolkit

`uv` is used throughout (installed to `~/.local/bin/uv`, symlinked from a snap path).

```bash
cd <toolkit-copy>
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .
```

Resolved: Python 3.11.16, torch **2.13.0+cu130** (CUDA available, sees the RTX 5090), TF 2.21.0,
gymnasium 1.3.0, gymnasium-robotics 1.4.2.

**`gymnasium-robotics` is in neither `requirements.txt` nor `env.yaml`** but is required by
`envs/robotics_flat.py` and by `utests/test_registry.py::test_env`. Same category of gap as the
`pysindy` / `scikit-learn` one noted in `environment.md`.

**`pip install -e .` needs the packaging fix** (see `WORKLOG_legion.md`) — upstream `setup.py` omits
every subpackage, so a strict editable install exposes only the top-level package.

## Isaac Sim — two installations, deliberately

**1. Docker container** (`isaac-lab-base`, 34.7 GB image, built from Alvika's fork)

```bash
cd /home/aidev/RL_Twin/isaaclab_dt-main/docker
docker compose --env-file .env.base -f docker-compose.yaml --profile base up -d isaac-lab-base
docker exec -it isaac-lab-base bash
```

`.env.base` was repointed at this machine: `EXTERNAL_USD_PATH` → `digital_twin_models-DT_reorg`,
`EXTERNAL_PROJECT_PATH` → `SciOptControlToolkit`. Inside the container these appear as
`envs_external/` and `external_projects/`. `aidev` was added to the `docker` group.

**2. Workstation install** (`/home/aidev/isaacsim`, 17 GB, Isaac Sim **5.1.0**)

```bash
/home/aidev/isaacsim/isaac-sim.sh      # GUI
/home/aidev/isaacsim/python.sh <script>  # scripting
```

Version 5.1.0 deliberately: NVIDIA's download page defaults to 6.0.1, and Alvika flagged selecting
5.1.0 to match Martin's assets. The container is pinned to 5.1.0 too, so both agree. Downloaded
directly from `download.isaacsim.omniverse.nvidia.com` — no NGC login was needed.

Two packages had to be added to Isaac Sim's bundled Python for the toolkit to run there:

```bash
/home/aidev/isaacsim/python.sh -m pip install tensorboard gymnasium
```

Without `gymnasium` the agent reports *"Action space not valid for this agent"* — a misleading
message, since the real cause is the import failing inside a `try/except`.

## Line endings

The toolkit was copied from Windows, so every file had CRLF. On Linux this makes `git status` report
~80 files changed when only a handful are. The copies under `_toolkits/` were normalised to LF at
copy time; the working `SciOptControlToolkit` clone was **not**. When inspecting changes there, use:

```bash
git diff --ignore-cr-at-eol
```

and never `git add .`.
