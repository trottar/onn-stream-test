# T91 — learn: FAIL

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| spec usable | false | true | **no** |
| every class separable | [] | [] | yes |
| margin_needed | 0.1564 | ">= 0.0796 (T89's kept spec (the lower of T88 0.0921 / T89 0.0796))" | yes |
| held-out frames read as another class | 0 | 0 | yes |
| held-out frames read unknown (share) | 1.0 | "<= 0.105" | **no** |
| other read as a screen | 0 | 0 | yes |
| begin: never ended | true | true | yes |
| begin: recognised within | null | "<= 8.0 s" | **no** |
| end_P1: ended as itself | null | "end_P1" | **no** |
| end_P1: ended within | null | "<= 2.0 s" | **no** |
| end_P1_2: ended as itself | null | "end_P1" | **no** |
| end_P1_2: ended within | null | "<= 2.0 s" | **no** |
| end_P2: ended as itself | null | "end_P2" | **no** |
| end_P2: ended within | null | "<= 2.0 s" | **no** |
| end_P2_2: ended as itself | null | "end_P2" | **no** |
| end_P2_2: ended within | null | "<= 2.0 s" | **no** |
| other: never ended | true | true | yes |
| no two saves of one ending the same picture | [] | ">= 1.0 grey (64 x 48 grey, mean |difference| of the screens that stay; H7-V1: one state run twice, 391 of 400 frames under 1.0)" | yes |
| left out: end_P1 | null | "end_P1 within <= 2.0 s, never another" | **no** |
| left out: end_P1_2 | null | "end_P1 within <= 2.0 s, never another" | **no** |
| left out: end_P2 | null | "end_P2 within <= 2.0 s, never another" | **no** |
| left out: end_P2_2 | null | "end_P2 within <= 2.0 s, never another" | **no** |

One more save: end_P1_3 — the screen after a match player 1 won, from a match not saved yet (other characters or another stage than its saves kept); save it to a free slot, then register T91 … --collect end_P1_3=<slot> and learn T91 again.
