# HOME-8 stage 1 (2026-11-08 23:36-23:40Z, unattended)

- The read line at ~23:36Z. HEAD `3c705130` (queue W committed: B61-B64), the tree clean.
- **Preconditions** (`check_before.json`, `client_before.json`, `properties_before.txt`, `tmp_free.txt`): `/tmp` 6.6 GB;
  seventeen lines, `--check` ok; **`9aa00ba2…` CONFIRMED, read back on the onn**, paired; the eleven properties empty;
  the two units; no game, no movie.
- **The companion restart** 23:36:5xZ (start after the queue W commit at 23:35:33Z: B61-B64 live): seventeen lines,
  `--check` ok, the journal clean; no keeper restart.
- **The N64 remap, before any launch** (`n64_core_check_remap.json`): bundled, 12 / 12 keys, remap **absent (the first
  N64 launch writes it)**, shadowed 0, writable, layout default `face_c`. T6's details label (the host's, read):
  "A = ⨉, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2".
- **T6's reproduction** (B item 4; B61's `b61_repro.py --content <T6, read in place>`, temp folders under `~/.cache/` on
  the main disk, DISPLAY / XAUTHORITY from the companion; `t6_repro_output.jsonl`, paths stripped): up 0.62 s (PLAYING);
  baseline running 5.2 s: 12 answered, 0 timeouts, longest silence 0.27 s; **the running save: ack null after 3003 ms;
  then 0 answered, 8 timeouts, longest silence 4.0 s**; threads: the main `AppRun` thread `R` (spinning, wchan 0), the
  others in futex waits; **SIGKILL** at 22.8 s (returncode -9). The paused save not reached (the hang came first).
  **Recorded: running save hangs T6: yes.** The temp folder (608 KB) removed; nothing left running; the drive read only.
- **The drive before** (`drive_before.txt`; listings gitignored): the N64 and PS1 folders' listing hashes.
- **Pre-registration** `../preregistration.md` hashed (`../preregistration.sha256`).
