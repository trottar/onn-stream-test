---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 6fcd2f23 (B63 built after B62 in /tmp/b_q15w_work; its diff against the after-B62 snapshot; applied to the tree third, uncommitted)
---

# B63 — PS1 multitap vs player 2: the multitap only for a multitap-capable title

**Classification: SETTLED + BUILT**, a **default-on host change** inside the hold-to-join path (disclosed);
`PRIVYHUB_PS1_MULTITAP_CAPABILITY=0` = today. No APK; two client items listed.
- **Tests:** `tests/b63_ps1_multitap` **11** green ×3; `players_session` 19, `relaunch_ports` 19 (B54 / B57),
  `pad_slots` 5, `ps2_session` 93, `n64_session` 28 green. Every host suite as the baseline, plus B61-B63's.
- **Mutations:** 4, all caught.
- **Proof:** the knob `0` = today (`b63_2026-11-08/proof_flag_absent.md`). Nothing committed or adopted.

Design `b63_2026-11-08/design_written_before_code.md`, sha256 `44754900…6eeb0e6b`, hashed **23:14:46Z, before any
B63 code**. The settle reads ran from 23:12Z; `started_at.txt` was written at 23:14Z with the design (disclosed).

## 0. Settled

- **T1 with the port-1 multitap: player 2 is dead,** after the relaunch and from boot (HOME-7 C17 and its
  diagnostic); with it off, player 2 works. With Beetle's port-1 multitap players 1-4 are on 1A-1D, so a title
  without multitap support reads 1A and port 2, and **1B (player 2) is never read**.
- **Which titles are capable:** the metadata `controller_overrides.json`, which holds 20 titles. **5 carry
  `ps1_multitap: "port1"`** (the Phase-A four-player set D087 / D088 validated) and 3 carry `"off"`. **T1's
  metadata is "off".**
- **The stored count lives on the onn** (B54's private preference `privyhub_players_joined`) and is sent as
  `players_joined` at every launch. So T1, stored at 3 since C17, launched with the multitap every time. The host
  cannot rewrite it.
- **The client (read, unchanged):** a hold beyond the ports relaunches only when `ports_set.multitap_available`;
  otherwise it shows "No multitap on this system — <n> players".

## 1. Built (`b63_2026-11-08/b63.diff`, 5 files)

- **`EmulatorManager.ps1_multitap_capable(game)`:** the metadata's `ps1_multitap == "port1"` or a new
  `ps1_multitap_capable: true`. Unknown = not.
- **`players_session.plan(..., capable)`:** a PS1 title with `capable` False → `multitap_available` false, 2 ports,
  `ps1_mode "off"` (the per-content Beetle `.opt` rewritten off), `capable` / `capped_from: 4`. `None` = today's plan
  byte for byte. SNES / PS2 / N64 unchanged.
- **The launch** passes the capability for PS1, and its game log says `PS1 ports capped: 4 -> 2 (not
  multitap-capable)`.
- **`ports_set`:**
  - the plan's echo gains `capable` / `capped_from`;
  - the metadata fallback's PS1 `multitap_available` is the capability (or the metadata's own multitap).
- **`relaunch_ports.run`:** a 4-port relaunch of an incapable PS1 title → refused, "This game supports 2 players",
  nothing stopped.
- **"The stored count never above the capability", and the migration:**
  - **the host caps at every launch,** so T1's stored 3 now starts 2 ports;
  - **T1's own host state** (its per-content `.opt` with the multitap on) **is rewritten off at its next launch, which
    is the recorded migration** (C26 reads the log line);
  - **the onn's stored value stays 3** until the client changes it. That is listed for the next APK; its effect is
    already neutralised by the cap;
  - **no separate one-time host pass:** the host stores no counts, and a pass over the hashed per-content stems would
    do nothing the next launch does not.
- **For the next APK (listed, not built):**
  1. the note "This game supports 2 players" in place of "No multitap on this system — 2 players" when
     `ports_set.capable` is false;
  2. the onn's stored joined count capped at the title's capability.
- **Default-on, disclosed:** a PS1 title not flagged capable can no longer get the multitap from a join or a pick, so
  three players there is not possible (player 2 would be dead anyway). The five `port1` titles keep the multitap at
  launch (D087's metadata path, untouched) and B54's relaunch. B46's chooser `players_chosen=4` is capped the same
  way.

## 2. Tests (`tests/b63_ps1_multitap`, 11)

- **`plan`:**
  - capable 4 → 4 ports + multitap;
  - incapable 4 → 2 ports, `multitap_available` false, mode off, `capped_from` 4, two `--device`;
  - 1 → 1;
  - `capable=None` → today's plan exactly; SNES / PS2 / N64 unchanged.
- **The capability:** `port1` / `ps1_multitap_capable` true; `off` / unknown / another system / a bad id false; the
  knob.
- **The echo:** a capped join → players 2, no multitap, `capable` false, `capped_from` 4; the metadata fallback for
  incapable / capable / multitap-on; the knob `0` → today (no `capable` key).
- **The relaunch:** incapable → "This game supports 2 players", nothing paused or stopped; capable → passes the rule.
- **A real PS1 launch through B59's fake RetroArch tree** (`players_joined` 3):
  - an incapable title → two `--device`, the `.opt` multitap `disabled`, `PS1 multitap: off`, the capped line,
    `ports_set` 2 / unavailable;
  - a capable title → four `--device`, multitap `enabled`, no capped line;
  - **the knob `0` → today's multitap on the incapable title.**
- **Mutations:** capability always true; the cap removed from `plan`; the relaunch refusal removed; the knob
  inverted. All four caught.

## 3. For A (HOME-8)

- **C26** (T1 with three pads):
  - the start's `ports_set` players 2, `multitap_available` false, `capable` false, `capped_from` 4;
  - the game log `PS1 multitap: off` and `PS1 ports capped: 4 -> 2`;
  - the third pad's hold → the onn's note (today's words: "No multitap on this system — 2 players"), **no
    `relaunch_ports` row**;
  - player 2 works (the user's line).
- **C27** (a `port1` title with three pads): B54's relaunch as before (or the multitap from the start if its stored
  count is 3), and players 1-3 working.

## 4. Files

`b63_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `.sha256` + `design_hashed_at.txt`;
- `b63.diff`, `applied_to_tree_at.txt`, `diff_check.txt`, `proof_flag_absent.md`;
- `tests_x3.txt`, `tests_mutations.txt`, `tests_host_baseline.txt`, `tests_host_b63.txt`, `tests_in_the_tree.txt`;
- `redact_check.py` + `.txt`, `title_check.py` + `.txt`, `manifest.sha256`.

Patch note: `patches/B63_PS1_MULTITAP_CAPABILITY.md`.

**One line for the user:** a PS1 game only gets the 4-player adapter if it is one of the games known to support it. On
your two-player game, a third controller now just shows a note and player 2 keeps working.
