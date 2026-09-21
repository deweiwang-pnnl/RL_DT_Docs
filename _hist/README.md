# `_hist` — verified results

Where `/trace` writes a piece of work that has actually been **run**, so the claim can be re-checked
instead of taken on trust. Empty until the first trace; created 2026-08-19 because `CLAUDE.md` and
`_docs/README.md` both point here.

One directory per verified result, named for what it settles:

```
_hist/
└── <YYYY-MM-DD>_<slug>/          the name /trace generates — date, underscore, short slug
    ├── <script>            the exact script or command that was run, unedited
    ├── output.txt          its raw stdout/stderr, unedited
    └── NOTES.md            what question this settles, and the answer in one paragraph
```

Rules, and the reason for each:

- **Raw output is never cleaned up.** The value of this folder is that the numbers were not retyped.
- **`NOTES.md` states the question first.** A result with no question attached is unusable six weeks
  later.
- **Record the environment**: machine hostname, Python version, and the commit SHA of whatever was
  measured. `_docs/environment.md` explains why hostname matters here — the project path is
  OneDrive-synced and identical on both machines.
- **No checkpoints, logs, run directories, USD assets or datasets** — see `.gitignore`. A trace holds a
  script and its text output, nothing heavy.

**Relationship to the other two records.** `_hist/` is the evidence layer: it holds the artefact.
[`../_docs/PUBLICATION_MATERIALS.md`](../_docs/PUBLICATION_MATERIALS.md) is the findings layer — it
states what a number *means* and links here for proof. [`../_docs/WORKLOG.md`](../_docs/WORKLOG.md) is
the work layer — what was done, round by round. A measurement that matters ends up in all three: run
here, interpreted there, dated in the worklog.
