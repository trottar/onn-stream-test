# T92 — learn: FAIL

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| spec usable | true | true | yes |
| the score places found | "found" | "found" | yes |
| every digit separable | [] | [] | yes |
| digit margin_needed | 0.2473 | ">= 0.0796 (T89's kept spec (the lower of T88 0.0921 / T89 0.0796))" | yes |
| held-out frames read as another class | 0 | 0 | yes |
| held-out frames read unknown (share) | 0.0 | "<= 0.105" | yes |
| other read as a screen | 0 | 0 | yes |
| begin: never ended | true | true | yes |
| begin: recognised within | 0.0 | "<= 8.0 s" | yes |
| end_P1: ended as itself | [2, 0] | [2, 0] | yes |
| end_P1: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P1_2: ended as itself | [5, 4] | [5, 4] | yes |
| end_P1_2: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P2: ended as itself | [2, 3] | [2, 3] | yes |
| end_P2: ended within | 2.0 | "<= 2.0 s" | yes |
| end_P2_2: ended as itself | [0, 2] | [0, 2] | yes |
| end_P2_2: ended within | 2.0 | "<= 2.0 s" | yes |
| other: never ended | true | true | yes |
| no two saves of one ending the same picture | [] | ">= 1.0 grey (64 x 48 grey, mean |difference| of the screens that stay; H7-V1: one state run twice, 391 of 400 frames under 1.0)" | yes |
| left out: end_P1 | ["02+_+_+_+_=02-00+_+_+_+_=00", 1.5] | "02+_+_+_+_=02-00+_+_+_+_=00 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | yes |
| left out: end_P1_2 | ["0?+_+_+_+_=0?-0?+_+_+_+_=0?", "1.5 (the full reader's)"] | "05+_+_+_+_=05-04+_+_+_+_=04 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | **no** |
| left out: end_P2 | ["02+_+_+_+_=02-0?+_+_+_+_=0?", "2.0 (the full reader's)"] | "02+_+_+_+_=02-03+_+_+_+_=03 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | **no** |
| left out: end_P2_2 | ["00+_+_+_+_=00-02+_+_+_+_=02", 2.0] | "00+_+_+_+_=00-02+_+_+_+_=02 (every number) within <= 2.0 s, never other numbers (a digit only it shows read with its own other glyphs; a column only it fills shown only here)" | yes |
| every digit that can occur up to 5 (0, 1, 2, 3, 4, 5) read by a reader learnt without each save that shows it | {"across-save spread": {"across": 0.3259, "bar": "across <= within + 0.05", "met": true, "pairs": [40, 8], "within": 0.3268}, "learnt from one save": {"3": "1 glyphs in end_P2, 0 read back \u2014 not learnt", "4": "1 glyphs in end_P1_2, 0 read back \u2014 not learnt", "5": "1 glyphs in end_P1_2, 0 read back \u2014 not learnt"}, "not expected (above the highest score)": ["6", "7", "8", "9"], "shown by fewer than two saves": ["1", "3", "4", "5"]} | {"shown by fewer than two saves": []} | **no** |

One more save: a match either player won whose line score shows 1, 3, 4 or 5 (in any quarter, overtime or final, either side); the more of them the better — save the screen after it to a free slot, then register T92 … --collect <role>=<slot> with the role of the player who won (end_P1_3 if P1 won, end_P2_3 if P2 won), label T92 and learn T92 again. 4 digits are still short (1, 3, 4 or 5); if one is still short after that match, learn asks for one more.
