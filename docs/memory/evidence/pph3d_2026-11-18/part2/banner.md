# PP-H3d — B: the band in the practice's encoder command only

`tail -n +$((N_ENC+1)) logs/games/native_video_alpha.log | grep -a '^encoder argv:'` → **9 argv lines**, each after its
`Capture:` line (the window: the board's, or the title's). The words checked: `PRACTICE — press Start to go back`.

| # | capture | the sitting | the band |
| --- | --- | --- | --- |
| 1 | the board | the board's first launch (06:46Z) | no |
| 2 | the board | the board relaunched (06:49Z) | no |
| 3 | the board | the board relaunched (06:56Z) | no |
| 4 | the title | the self-proof's switch (a real go) | no |
| 5 | the board | the self-proof's way back | no |
| 6 | the title | **the practice's switch** (after `minigame_go` `"practice": true`) | **yes** |
| 7 | the board | the practice's way back | no |
| 8 | the title | the real match's switch | no |
| 9 | the board | the real match's end | no |

**Met:** the band in the practice's command and in no other (count 1 = the practices). The user: "The practice band was
there (maybe a little too high, it was partially cut off)" — recorded for B, no bar.
