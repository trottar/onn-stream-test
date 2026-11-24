# T90 — train: FAIL

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| gate 1: every glyph of a symbol two or more saves show, read right without its save | "all" | "all" | yes |
| margin_needed | 0.2345 | ">= 0.0796" | yes |
| every symbol two saves show separable | "all" | "all" | yes |
| gate 2: 3, one real picture | "seen once" | "counted when rigid, 8 valid variants all read as itself, no other glyph read as it \u2014 else asked" | yes |
| gate 2: 4, one real picture | "seen once" | "counted when rigid, 8 valid variants all read as itself, no other glyph read as it \u2014 else asked" | yes |
| gate 2: 8, one real picture | {"not counted": {"bar": 0.0995, "draws": 8, "other symbols' real glyphs read as it": 0, "rigid": 0.5693, "variants read as": {"8": 4, "?": 4}, "variants read as itself": "4 of 8"}} | "counted when rigid, 8 valid variants all read as itself, no other glyph read as it \u2014 else asked" | yes |
| gate 2: 9, one real picture | "seen once" | "counted when rigid, 8 valid variants all read as itself, no other glyph read as it \u2014 else asked" | yes |
| gate 3: every symbol the result can show learnt (none never seen) | ["6", "7", "8"] | "all" | **no** |
| the screens: start and end thresholds | {"end": 0.1512, "start": 0.1507} | "both set" | yes |
| begin: never ended | true | true | yes |
| begin: recognised within | 0.0 | "<= 8.0 s" | yes |
| end_P1: ended as itself | ["15", "2"] | ["15", "2"] | yes |
| end_P1: ended within | 1.5 | "<= 2.0 s" | yes |
| end_P1_2: ended as itself | null | ["35", "28"] | **no** |
| end_P1_2: ended within | null | "<= 2.0 s" | **no** |
| end_P2: ended as itself | ["0", "22"] | ["0", "22"] | yes |
| end_P2: ended within | 2.0 | "<= 2.0 s" | yes |
| end_P2_2: ended as itself | ["0", "29"] | ["0", "29"] | yes |
| end_P2_2: ended within | 2.0 | "<= 2.0 s" | yes |
| end_P2_3: ended as itself | ["14", "24"] | ["14", "24"] | yes |
| end_P2_3: ended within | 1.5 | "<= 2.0 s" | yes |
| other: never ended | true | true | yes |

Still needed: a final score with a 6 in it and a final score with a 7 in it and a final score with a 8 in it (either player; one match may show more than one).
