# IMPORT-1: pre-registration (written and hashed before `inspect` / `plan`, 2026-11-08)

Sources: `handoffs/SESSION_B_DONE_2026-11-08T.md` §"A — then IMPORT-1" (B's commands, rows I1-I6 and checks, used as
B states them), `handoffs/IMPORT-1_DRIVE_PS1_TASK.md`, `B56_IMPORT_SLICE_1A_2026-11-08.md`, `docs/IMPORT.md`,
`architecture/H0_IMPORT_CONTRACT_DESIGN_2026-11-06.md`.

**The source is the external movies drive, not a USB stick** (the user: "the external HD has a bunch of games and
bios"; "Point at drive and see the plan, import whatever is new"): the drive's PS1 folder (the sibling of the PS2
folder) presented to `tools/import_usb.py` through `/tmp/privyhub_import_root/PrivyHub-Import/games/ps1` (a symlink;
the tool unchanged). **The drive's PS1 BIOS: not found** — no `games/ps1/bios/`, no `bios/ps1/` or `bios/` at the tree's
top, no PS1 `scph*` name anywhere on the drive (the only BIOS files are the PS2 folder's); so no `bios/ps1` link, and the
run is games only.

**The state:** sixteen adopted lines + the bench drop-in `b56-import.conf` (`PRIVYHUB_IMPORT=1`) = seventeen; `--check`
not ok on the environ only (the bench flag); `cfe0211c…` CONFIRMED; the eleven properties empty; no game, no movie. The
drive is mounted read-only. The library's PS1 folder before: 419 files, 46963917095 B; the games list "PlayStation
(OpenBIOS) (80)"; the core's BIOS folder empty.

## The expectation (stated before `plan`)

- **The server already holds copies of the user's PS1 games, so most titles should read DUPLICATE** ("already in the
  library"). ACCEPT only what the library lacks.
- **An ACCEPT of a title the library already has is a duplicate-check miss:** a B item, **not imported** (left out at
  stage 2 and named to B).
- REJECTs carry the tool's reasons (e.g. an archive is not a disc image).

## The rows (B's)

- **I1 inspect:** exit 0; the T labels with kinds and file counts; every rejection with its reason; the BIOS line
  (here: none on the source).
- **I2 plan:** exit 0; each T ACCEPT / DUPLICATE / REJECT with its reason; space ok; the plan file and the log on the hub.
- **I3 apply / verify** (only if anything is accepted and the user says so): exit 0 both; each accepted T `placed`; no
  `.import-*` temp left; `data/import/marks.json` one `new` per placed title; **the drive's listing hash before = after**.
- **I4 the log:** `data/import/logs/` holds no title, file name, hash or mount (a grep against the plan's names; the names
  stay out of the record).
- **I5 the onn:** HOME-7's C19 (the user is not at the TV); the bench drop-in stays on until then.
- **I6 idempotent:** `plan` again → every title DUPLICATE, exit 0; `apply` → nothing copied.

Nothing written to the drive; nothing adopted; nothing committed.
