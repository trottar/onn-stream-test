# T90 — learn: PASS

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| spec usable | true | true | yes |
| the score places found | "found" | "found" | yes |
| every digit separable | [] | [] | yes |
| digit margin_needed | 0.2047 | ">= 0.0796 (T89's kept spec (the lower of T88 0.0921 / T89 0.0796))" | yes |
| held-out frames read as another class | 0 | 0 | yes |
| held-out frames read unknown (share) | 0.0 | "<= 0.105" | yes |
| other read as a screen | 0 | 0 | yes |
| begin: never ended | true | true | yes |
| begin: recognised within | 0.0 | "<= 8.0 s" | yes |
| end_P1: ended as itself | [15, 2] | [15, 2] | yes |
| end_P1: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P1_2: ended as itself | [35, 28] | [35, 28] | yes |
| end_P1_2: ended within | 2.0 | "<= 2.0 s" | yes |
| end_P2: ended as itself | [0, 22] | [0, 22] | yes |
| end_P2: ended within | 2.0 | "<= 2.0 s" | yes |
| end_P2_2: ended as itself | [0, 29] | [0, 29] | yes |
| end_P2_2: ended within | 2.0 | "<= 2.0 s" | yes |
| end_P2_3: ended as itself | [14, 24] | [14, 24] | yes |
| end_P2_3: ended within | 1.5 | "<= 2.0 s" | yes |
| other: never ended | true | true | yes |
| no two saves of one ending the same picture | [] | ">= 1.0 grey (64 x 48 grey, mean |difference| of the screens that stay; H7-V1: one state run twice, 391 of 400 frames under 1.0)" | yes |
| left out: end_P1 | ["9+2+2+2+_+_=15-0+0+2+0+_+_=2", 1.5] | "9+2+2+2+_+_=15-0+0+2+0+_+_=2 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | yes |
| left out: end_P1_2 | ["7+7+7+7+*+_=35-7+7+7+7+*+_=28 (shown only here: P1 column 5, P2 column 5)", 2.0] | "7+7+7+7+7+_=35-7+7+7+7+0+_=28 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | yes |
| left out: end_P2 | ["0+0+0+0+_+_=0-2+9+2+9+_+_=22", 2.0] | "0+0+0+0+_+_=0-2+9+2+9+_+_=22 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | yes |
| left out: end_P2_2 | ["0+0+0+0+_+_=0-9+9+2+9+_+_=29", 2.0] | "0+0+0+0+_+_=0-9+9+2+9+_+_=29 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | yes |
| left out: end_P2_3 | ["0+6+0+8+_+_=14-9+3+6+6+_+_=24", "1.5 (the full reader's)"] | "0+6+0+8+_+_=14-9+3+6+6+_+_=24 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | yes |
| every digit 0-9 read by a reader learnt without each save that shows it | {"across-save spread": {"across": 0.4009, "bar": "across <= within + 0.05", "met": true, "pairs": [182, 48], "within": 0.4183}, "learnt from one save": {"4": "2 glyphs in end_P2_3, 2 read back", "6": "3 glyphs in end_P2_3, 3 read back", "7": "9 glyphs in end_P1_2, 9 read back"}, "shown by fewer than two saves": []} | {"shown by fewer than two saves": []} | yes |
