# B53 — PCSX2's log per launch, kept 30 days, copied by the keeper, counted by diag_read (design, hashed before code)

Queue: `handoffs/QUEUE_2026-11-08S.md` §B53. PS2-R1: PCSX2 rewrites `emulog.txt` at every start, so a session's drive
reads, bindings, card lines and TLB misses are gone after the next launch. Built in `/tmp/b_q11s_b53` **on top of
B52** (both touch the PS2 launch; B53's diff is taken against B52's copy). Runtime: **inside `PRIVYHUB_PS2=1`; absent =
today byte for byte**. Tools: a log tree with no PCSX2 log reads and copies as today.

## 0. Settled (the 2.8.2 binary's strings; nothing run)

- **`-logfile <path>: Writes the application log to path instead of emulog.txt.`** (its `-help` text in the binary).
  So the CLI carries it, and no copy at exit is needed.
- **The drive messages PCSX2 logs:** `Read Abort`, `CDVD read err, retrying... (attempt …)`, `SUB CHANNEL READ ERROR`,
  `DVD Read Bad Parameter Error` / `CDDA Read Bad Parameter Error`, `DVD Read when CD Error`. **It logs no slow-read
  line,** so "disc read waits" can be counted only as these errors and retries. Disclosed.
- **The other lines counted:**
  - `Invalid binding:`;
  - the card lines `McdSlot N [File]: … [8 MB, Formatted|UNFORMATTED]`;
  - `TLB Miss`;
  - `Saved state to slot N.` / `Loaded state from slot N.`;
  - `ELF Loading:`.
- **The timestamps** are seconds since PCSX2's start (`[  12.3456] …`); the launch's UTC time is in the file name.

## 1. The code

- **The launch** (`EmulatorManager._launch_pcsx2`):
  - `-logfile <abs data/games/ps2/logs/<YYYYmmddTHHMMSSZ>-pcsx2.log>` (the UTC launch time; no title or id) is added to
    the command before `--`;
  - the session's `log_path` (B52's ELF / TLB checks) is that file;
  - the game log gains `PS2 pcsx2-log: <file name>`.
- **Retention:** at each PS2 launch, `*-pcsx2.log` files in that folder whose name is older than 30 days are removed
  (the queue's 30-day retention; a deletion the code makes, disclosed). The folder is under `data/` (gitignored), never
  the drive.
- **The keeper** (`tools/trip_log_keeper.py`, used by `diag_keeper`): a second source,
  `<repo>/data/games/ps2/logs/`, files named `^\d{8}T\d{6}Z-pcsx2\.log$`.
  - Each new one becomes a tail from its first byte, kept as `raw/ps2logs__<name>/…` like the game logs and redacted by
    the same redactor. Those present at the keeper's start count as seen.
  - `diag_keeper`'s saved state resumes those tails too.
  - These copies are local diagnostics under `~/privyhub_diag/` and carry the title and serial as PCSX2 writes them (as
    RetroArch's game logs already do). They never go into git or a record.
- **`tools/diag_read.py`:**
  - `Logs` reads the PCSX2 logs, live from `data/games/ps2/logs/` and from a keeper dir's `raw/ps2logs__*`;
  - each line's UTC time = the name's time + its seconds;
  - a PS2 session's row gains `pcsx2_log`: the counts of the lines between the previous session's end (or the launch)
    and this session's end: `read_errors`, `invalid_binding`, `card_formatted`, `card_unformatted`, `tlb_miss`,
    `state_saved`, `state_loaded`, `elf`;
  - a Markdown section `## PCSX2 logs (B53)` appears only when a PS2 session has a log;
  - a row with no PCSX2 log, and every RetroArch row, is as before.

## 2. Tests

- the name from a fake launch time;
- the command carries `-logfile <that path>` before `--`;
- the retention (a 31-day-old name removed, a 29-day-old kept, other names untouched);
- the keeper copies a new PCSX2 log from a fake tree into `raw/ps2logs__…`, and not one present at its start;
- `diag_read`'s counts from a fake log, beside a fake PS2 session, mapped by time;
- absent / no PCSX2 log → `diag_read`'s output and the keeper's copies as today (the existing suites).
