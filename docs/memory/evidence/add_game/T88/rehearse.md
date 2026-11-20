# T88 — rehearse: FAIL

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| learn: spec usable | true | true | yes |
| learn: every class separable | ["end_P1", "end_P2"] | [] | **no** |
| learn: margin_needed | 0.0164 | ">= 0.0796 (T89's kept spec (the lower of T88 0.0921 / T89 0.0796))" | **no** |
| learn: held-out frames read as another class | 0 | 0 | yes |
| learn: held-out frames read unknown (share) | 0.6552 | "<= 0.105" | **no** |
| learn: other read as a screen | 0 | 0 | yes |
| learn: begin: never ended | true | true | yes |
| learn: begin: recognised within | 0.0 | "<= 8.0 s" | yes |
| learn: end_P1: ended as itself | null | "end_P1" | **no** |
| learn: end_P1: ended within | null | "<= 2.0 s" | **no** |
| learn: end_P2: ended as itself | null | "end_P2" | **no** |
| learn: end_P2: ended within | null | "<= 2.0 s" | **no** |
| learn: other: never ended | true | true | yes |
| learn's verdict in the scratch | "FAIL" | "PASS" | **no** |
| end_P1: the scratch rules read it as the real rules | [null, ["end_P1", null]] | "the same, ended, its own ending" | **no** |
| end_P2: the scratch rules read it as the real rules | [null, ["end_P2", null]] | "the same, ended, its own ending" | **no** |
| end_p1_b: the scratch rules read it as the real rules | [null, null] | "the same, ended, its own ending" | **no** |
| end_p2_b: the scratch rules read it as the real rules | [null, null] | "the same, ended, its own ending" | **no** |
| the real rules folder: every file's sha256 before = after | [15, 15, 0] | "the same files, 0 changed" | yes |
| the scratch removed | true | true | yes |

Roles (kept file -> role): the rules folder's begin -> begin, end_p1.state -> end_P1, end_p2.state -> end_P2, slot 2 -> other. Missing: none. Endings read, not a role: end_p1_b, end_p2_b.
