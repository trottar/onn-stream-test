| source | request | baseline | flag absent | v2 (the gate) |
| --- | --- | --- | --- | --- |
| lan | `GET /vod/movie.mp4` | 28551ff8f740 | identical | (below) |
| loopback | `GET /vod/movie.mp4` | 28551ff8f740 | identical | (below) |
| overlay | `GET /vod/movie.mp4` | 28551ff8f740 | identical | (below) |
| lan | `GET /vod/movie.mp4` `bytes=0-1023` | 2d429aa76b74 | identical | (below) |
| loopback | `GET /vod/movie.mp4` `bytes=0-1023` | 2d429aa76b74 | identical | (below) |
| overlay | `GET /vod/movie.mp4` `bytes=0-1023` | 2d429aa76b74 | identical | (below) |
| lan | `GET /vod/movie.mp4` `bytes=70000-` | f0ef7d4d63ae | identical | (below) |
| loopback | `GET /vod/movie.mp4` `bytes=70000-` | f0ef7d4d63ae | identical | (below) |
| overlay | `GET /vod/movie.mp4` `bytes=70000-` | f0ef7d4d63ae | identical | (below) |
| lan | `GET /vod/movie.mp4` `bytes=-500` | e953152a70c9 | identical | (below) |
| loopback | `GET /vod/movie.mp4` `bytes=-500` | e953152a70c9 | identical | (below) |
| overlay | `GET /vod/movie.mp4` `bytes=-500` | e953152a70c9 | identical | (below) |
| lan | `GET /vod/movie.mp4` `bytes=999999-` | e2081c3951c1 | identical | (below) |
| loopback | `GET /vod/movie.mp4` `bytes=999999-` | e2081c3951c1 | identical | (below) |
| overlay | `GET /vod/movie.mp4` `bytes=999999-` | e2081c3951c1 | identical | (below) |
| lan | `HEAD /vod/movie.mp4` | bcefae6f6e5b | identical | (below) |
| loopback | `HEAD /vod/movie.mp4` | bcefae6f6e5b | identical | (below) |
| overlay | `HEAD /vod/movie.mp4` | bcefae6f6e5b | identical | (below) |
| lan | `GET /live/stream.m3u8` | fd7bedb6176f | identical | (below) |
| loopback | `GET /live/stream.m3u8` | fd7bedb6176f | identical | (below) |
| overlay | `GET /live/stream.m3u8` | fd7bedb6176f | identical | (below) |
| lan | `GET /artwork/game.png` | 271229c9aa65 | identical | (below) |
| loopback | `GET /artwork/game.png` | 271229c9aa65 | identical | (below) |
| overlay | `GET /artwork/game.png` | 271229c9aa65 | identical | (below) |
| lan | `GET /vod/missing.mp4` | c360def67edc | identical | (below) |
| loopback | `GET /vod/missing.mp4` | c360def67edc | identical | (below) |
| overlay | `GET /vod/missing.mp4` | c360def67edc | identical | (below) |
| lan | `GET /vod/../secret.txt` | c360def67edc | identical | (below) |
| loopback | `GET /vod/../secret.txt` | c360def67edc | identical | (below) |
| overlay | `GET /vod/../secret.txt` | c360def67edc | identical | (below) |
| lan | `GET /live/` | ce83e7ea3c4b | identical | (below) |
| loopback | `GET /live/` | ce83e7ea3c4b | identical | (below) |
| overlay | `GET /live/` | ce83e7ea3c4b | identical | (below) |
| lan | `GET /vod/movie.mp4?media_token=fixture-value` `bytes=0-99` | 6d16cbfa79d5 | identical | (below) |
| loopback | `GET /vod/movie.mp4?media_token=fixture-value` `bytes=0-99` | 6d16cbfa79d5 | identical | (below) |
| overlay | `GET /vod/movie.mp4?media_token=fixture-value` `bytes=0-99` | 6d16cbfa79d5 | identical | (below) |
| lan, loopback | all of the above, no token | — | — | identical to the baseline |
| lan | `GET /vod/movie.mp4?media_token=fixture-value` (not issued) | — | — | 401 `media-token-unknown` (no fallback) |
| overlay | `GET /vod/movie.mp4` no token | — | — | 401 `legacy-overlay` |
| overlay | `GET /vod/movie.mp4` `bytes=0-1023` + header | — | — | 206, the baseline's bytes |
| overlay | `GET /vod/movie.mp4?media_token=…` `bytes=0-1023` | — | — | 206, the baseline's bytes; the log masks the value |
| overlay | `GET /vod/movie.mp4?media_token=forged` | — | — | 401 `media-token-unknown` |
