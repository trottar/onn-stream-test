# B167 — the six runs of `rehearse T88 --collect other=2` (the queue's exception; each after `status` and
# `native-stream-status` showed nothing running and no client; headless, nothing streamed, no restart, no flag)

| run | the code | the tool's verdict | not met | what it showed |
| --- | --- | --- | --- | --- |
| 1 | HEAD (`df81c762`), `TMPDIR` private, RetroArch's log copied out before the cleanup | FAIL (4 cells) | learn ran, rehearse ran: "ProofError: RetroArch exited during startup" | both logs: `[Wayland] Failed to connect`, `[KMS] Error when switching mode`, `[Video] Cannot open video driver. Exiting...` — **no display given** |
| 2 | the hub's display, core, core options; reasons; logs kept | FAIL (5 cells) | learn: pictures made ("end_P1: exited … (OSError)"), rehearse's pictures made ("(SyntaxError)") | RetroArch started and ran; the begin's pictures made; a screenshot read while still being written (4x render) |
| 3 | + the screenshot read whole | FAIL (20 cells) | learn's separable / margin 0.0008 / unknown 1.0 / replays | **every picture made**; the real rules read the kept end_p1 / end_p2 pictures (no cheats loaded) as end_P1 / end_P2; start and end_P2 not separable |
| 4 | + the rules folder's begin (the kept begin was the plain one) | FAIL (20 cells) | margin 0.0303; end_P1 replay ended as end_P2 at 4.0 s | separable, 0 unknown |
| 5 | the same, the pictures copied off the repo for study | FAIL (20 cells, as run 4) | as run 4 | the kept end_p1 saved a moment before its end screen settled (the real rules: other for ~1-2 s, then end_P1); the labels took that frame |
| 6 | + labels anchored on the screen that stays | FAIL (20 cells) | separable [end_P1, end_P2]; margin 0.0164; unknown 0.6552; the endings' replays | the labels right; one still save per ending cannot separate T88's two end screens |

Every run: **the real rules folder 15 files, 0 changed** (the tool's cell, met); **the scratch removed** (met). The
tool's page in the repo (`add_game/T88/rehearse.*`) holds run 6's verdict (the first use's is in `df81c762`).
