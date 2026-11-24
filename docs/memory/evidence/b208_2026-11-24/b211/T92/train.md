# T92 — train: FAIL

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| gate 1: every glyph of a symbol two or more saves show, read right without its save | "all" | "all" | yes |
| margin_needed | 0.1039 | ">= 0.0796" | yes |
| every symbol two saves show separable | "all" | "all" | yes |
| gate 2: 3, one real picture | {"not counted": {"bar": 0.0995, "other symbols' real glyphs read as it": 0, "rigid": 0.6465, "synthetic read as itself": "7 of 8"}} | "counted when rigid, every variant read as itself, no other glyph read as it \u2014 else asked" | yes |
| gate 2: 4, one real picture | "seen once" | "counted when rigid, every variant read as itself, no other glyph read as it \u2014 else asked" | yes |
| gate 2: 6, one real picture | {"not counted": {"bar": 0.0995, "other symbols' real glyphs read as it": 0, "rigid": 0.6465, "synthetic read as itself": "7 of 8"}} | "counted when rigid, every variant read as itself, no other glyph read as it \u2014 else asked" | yes |
| gate 3: every symbol the result can show learnt (none never seen) | ["1", "3", "6"] | "all" | **no** |
| the screens: start and end thresholds | {"end": 0.1868, "start": 0.1651} | "both set" | yes |
| begin: never ended | true | true | yes |
| begin: recognised within | 0.0 | "<= 8.0 s" | yes |
| end_P1: ended as itself | ["02", "00"] | ["02", "00"] | yes |
| end_P1: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P1_2: ended as itself | ["05", "04"] | ["05", "04"] | yes |
| end_P1_2: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P2: ended as itself | null | ["02", "03"] | **no** |
| end_P2: ended within | null | "<= 2.0 s" | **no** |
| end_P2_2: ended as itself | ["00", "02"] | ["00", "02"] | yes |
| end_P2_2: ended within | 2.0 | "<= 2.0 s" | yes |
| end_P2_3: ended as itself | null | ["05", "06"] | **no** |
| end_P2_3: ended within | null | "<= 2.0 s" | **no** |
| other: never ended | true | true | yes |

Still needed: a final score with a 1 in it and a final score with a 3 in it and a final score with a 6 in it (either player; one match may show more than one).
