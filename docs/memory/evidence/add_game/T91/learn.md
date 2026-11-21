# T91 — learn: PASS

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| spec usable | true | true | yes |
| the letters at one place in every save | "found" | "found" | yes |
| every held-out synthetic picture read (training's own bar; never counts toward a pass) | {"held out": 32, "read wrong or not read": 0, "trained on": 64} | "<= 0 (B192: the training's own bar \u2014 every held-out synthetic picture read; it never counts toward a pass)" | yes |
| begin: never ended | true | true | yes |
| begin: recognised within | 0.0 | "<= 8.0 s" | yes |
| end_P1: ended as itself | "end_P1" | "end_P1" | yes |
| end_P1: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P1_2: ended as itself | "end_P1" | "end_P1" | yes |
| end_P1_2: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P2: ended as itself | "end_P2" | "end_P2" | yes |
| end_P2: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P2_2: ended as itself | "end_P2" | "end_P2" | yes |
| end_P2_2: ended within | 2.0 | "<= 2.0 s" | yes |
| other: never ended | true | true | yes |
| a moving screen never ended (each end save's corners as they are, the rest of the picture taken in turn from the title's other saves every read) | "never" | "never" | yes |
| left out: end_P1 | ["end_P1", 1.5, ["---/WOW", "---/WOW"]] | "end_P1 within <= 2.0 s, never another, letters ---/WOW" | yes |
| left out: end_P1_2 | ["end_P1", 1.5, ["---/WOW", "---/WOW"]] | "end_P1 within <= 2.0 s, never another, letters ---/WOW" | yes |
| left out: end_P2 | ["end_P2", 1.5, ["WOW/W--", "WOW/W--"]] | "end_P2 within <= 2.0 s, never another, letters WOW/W--" | yes |
| left out: end_P2_2 | ["end_P2", 2.0, ["WOW/W--", "WOW/W--"]] | "end_P2 within <= 2.0 s, never another, letters WOW/W--" | yes |
| no two saves of one ending the same picture | [] | ">= 1.0 grey (64 x 48 grey, mean |difference| of the screens that stay; H7-V1: one state run twice, 391 of 400 frames under 1.0)" | yes |
