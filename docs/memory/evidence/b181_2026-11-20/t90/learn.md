# T90 — learn: FAIL

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| spec usable | true | true | yes |
| the score places found | "found" | "found" | yes |
| every digit separable | [] | [] | yes |
| digit margin_needed | 0.2085 | ">= 0.0796 (T89's kept spec (the lower of T88 0.0921 / T89 0.0796))" | yes |
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
| other: never ended | true | true | yes |
| no two saves of one ending the same picture | [] | ">= 1.0 grey (64 x 48 grey, mean |difference| of the screens that stay; H7-V1: one state run twice, 391 of 400 frames under 1.0)" | yes |
| left out: end_P1 | null | "9+2+2+2+_+_=15-0+0+2+0+_+_=2 (every number) within <= 2.0 s, never other numbers" | **no** |
| left out: end_P1_2 | null | "7+7+7+7+7+_=35-7+7+7+7+0+_=28 (every number) within <= 2.0 s, never other numbers" | **no** |
| left out: end_P2 | ["0+0+0+0+_+_=0-2+9+2+9+_+_=22", 2.0] | "0+0+0+0+_+_=0-2+9+2+9+_+_=22 (every number) within <= 2.0 s, never other numbers" | yes |
| left out: end_P2_2 | ["0+0+0+0+_+_=0-9+9+2+9+_+_=29", 2.0] | "0+0+0+0+_+_=0-9+9+2+9+_+_=29 (every number) within <= 2.0 s, never other numbers" | yes |
| every digit 0-9 read by a reader learnt without each save that shows it | {"shown by fewer than two saves": ["1", "3", "4", "6", "7", "8"]} | {"shown by fewer than two saves": []} | **no** |

One more save: a match either player won whose line score shows 1, 3, 4, 6, 7 or 8 (in any quarter, overtime or final, either side); the more of them the better — save the screen after it to a free slot, then register T90 … --collect <role>=<slot> with the role of the player who won (end_P1_3 if P1 won, end_P2_3 if P2 won), label T90 and learn T90 again.
