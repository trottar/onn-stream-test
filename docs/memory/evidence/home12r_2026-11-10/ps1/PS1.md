# The PS1 check — T85 (2026-11-10 22:17-22:20Z) — MET → B85 on the confirmed path

The user (verbatim, `user_lines.txt`): "1. Yes" (the list there, tidy, Launch at the top) / "2. Okay (filter worked)"
/ "3. Cheat works" / "4. Player one was invincible and player 2 was not. Game ended successfully".

| read | value |
| --- | --- |
| `cheat-catalog` T85 (22:17:15Z) | `clean` true; one source, 12 shown (stage 1), no "must be on" entry |
| the launch (22:18:01Z) | `cheat_source=0`, **one** cheat index → 200 |
| the staged file (the watcher) | under `cheat_runtime/` the PS1 core's folder, 12 cheats, none forced on in the file; gone at the end |
| RetroArch's log | **"Load game-specific cheatfile" 1**; the navigation lines for every entry (off) and the picked index **on twice** (the toggle, then the hub's read-back) — names not copied |
| the session | `activation_verified` **true** (the status, live) |
| the end | 22:19:54Z, nothing running, the staging dir cleaned |

**Met:** the list opened through the picker (Launch at the top, the filter), the cheat worked — player 1 only, as its
section says. **The PS1 cheat path is not broken by B84 / B85.** (For C49's N64 failure, compare: here RetroArch's
cheat-file line comes before the hub's first toggle.)
