# T92 — label: FAIL

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| every end save read | [] | [] | yes |
| end_P1: the two readings the same | ["2+_+_+_+_=2-0+_+_+_+_=0", "2+_+_+_+_=2-0+_+_+_+_=0"] | "the same numbers from both pictures" | yes |
| end_P1: the role's player ahead | [2, 0] | "P1 more than every other side" | yes |
| end_P1: the cells add up to the finals | [[2, 2], [0, 0]] | "each side's cells = its final" | yes |
| end_P1_2: the two readings the same | ["5+_+_+_+_=5-4+_+_+_+_=4", "5+_+_+_+_=5-4+_+_+_+_=4"] | "the same numbers from both pictures" | yes |
| end_P1_2: the role's player ahead | [5, 4] | "P1 more than every other side" | yes |
| end_P1_2: the cells add up to the finals | [[5, 5], [4, 4]] | "each side's cells = its final" | yes |
| end_P2: the two readings the same | ["2+_+_+_+_=2-3+_+_+_+_=3", "2+_+_+_+_=2-3+_+_+_+_=3"] | "the same numbers from both pictures" | yes |
| end_P2: the role's player ahead | [2, 3] | "P2 more than every other side" | yes |
| end_P2: the cells add up to the finals | [[2, 2], [3, 3]] | "each side's cells = its final" | yes |
| end_P2_2: the two readings the same | ["0+_+_+_+_=0-2+_+_+_+_=2", "0+_+_+_+_=0-2+_+_+_+_=2"] | "the same numbers from both pictures" | yes |
| end_P2_2: the role's player ahead | [0, 2] | "P2 more than every other side" | yes |
| end_P2_2: the cells add up to the finals | [[0, 0], [2, 2]] | "each side's cells = its final" | yes |
| the numbers at one place in every save | {"2.1": ["end_P1", "end_P2", "end_P2_2"]} | "found" | **no** |

Stop: end_P1 (P2's cell 1 does not fit where the other saves have it) after it was read again twice. Do not ask the user and do not ask for another match: take this line back to the chat (Cowork).
