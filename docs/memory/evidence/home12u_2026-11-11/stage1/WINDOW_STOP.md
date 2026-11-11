# HOME-12U stage 1 — stopped at the time window (2026-11-11 04:54Z)

The read line arrived 04:54:00Z, **inside 04:30-05:30Z**, which the task excludes for stage 1. Only reads were made
before the stop (HEAD, `git status`, `/tmp`, `--check`, the client read-back, the twenty properties, the drop-ins, the
units, the drive listing, the profiles' hash, the keeper) — no restart, no install, no test run, no catalog call.
At that read: queue AG `81ccd731` committed, the tree clean; `/tmp` 5.1 GB; eighteen lines, `--check` ok,
`85220f99…` CONFIRMED, paired; the twenty properties empty; the two units. Stage 1 resumes on the next read line
after 05:30Z, from the top.
