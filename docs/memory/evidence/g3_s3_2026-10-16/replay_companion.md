| source | request | baseline | flag absent | v2, legacy LAN |
| --- | --- | --- | --- | --- |
| source (d6-r1) | `GET /plugins/games/native-stream-status` | b2e1ab88811b | identical (b2e1ab88811b) | identical |
| loopback (d6-r1) | `GET /plugins/games/native-stream-status` | b2e1ab88811b | identical (b2e1ab88811b) | identical |
| source (d6-r1) | `GET /plugins/games/status` | 930b34358530 | identical (930b34358530) | identical |
| loopback (d6-r1) | `GET /plugins/games/status` | 930b34358530 | identical (930b34358530) | identical |
| source (client) | `POST /plugins/games/launch?id=fixture-game` | cddf3bb0c49a | identical (cddf3bb0c49a) | same + `X-PrivyHub-Session` header |
| loopback (client) | `POST /plugins/games/launch?id=fixture-game` | ac6e872cdf6e | identical (ac6e872cdf6e) | identical |
| source (client) | `POST /plugins/games/native-stream-start?port=50000` | 3c49cc3de05a | identical (3c49cc3de05a) | same + `X-PrivyHub-Session` header |
| loopback (client) | `POST /plugins/games/native-stream-start?port=50000` | 1151f0993dcf | identical (1151f0993dcf) | identical |
| source (client) | `POST /plugins/games/native-stream-heartbeat?seq=1` | c97d12cde052 | identical (c97d12cde052) | identical |
| loopback (client) | `POST /plugins/games/native-stream-heartbeat?seq=1` | 4b6bed68489f | identical (4b6bed68489f) | identical |
| source (client) | `GET /status` | 8724919dd900 | identical (8724919dd900) | identical |
| loopback (client) | `GET /status` | 8724919dd900 | identical (8724919dd900) | identical |
| source (client) | `GET /plugins/nosuch/status` | e3acd6332165 | identical (e3acd6332165) | identical |
| loopback (client) | `GET /plugins/nosuch/status` | e3acd6332165 | identical (e3acd6332165) | identical |
| source (g3-s3) | `GET /plugins/tv_state/state` | a5ca37e926bb | identical (a5ca37e926bb) | identical |
| loopback (g3-s3) | `GET /plugins/tv_state/state` | a5ca37e926bb | identical (a5ca37e926bb) | identical |
| source (g3-s3) | `GET /plugins/epg/guide?channels=a,b&hours=6` | 097b8e5fd62f | identical (097b8e5fd62f) | identical |
| loopback (g3-s3) | `GET /plugins/epg/guide?channels=a,b&hours=6` | 097b8e5fd62f | identical (097b8e5fd62f) | identical |
| source (g3-s3) | `GET /plugins/epg/prefetch?channels=a` | f4c428604ebe | identical (f4c428604ebe) | identical |
| loopback (g3-s3) | `GET /plugins/epg/prefetch?channels=a` | f4c428604ebe | identical (f4c428604ebe) | identical |
| source (g3-s3) | `GET /sources` | 1b89bed77d3b | identical (1b89bed77d3b) | identical |
| loopback (g3-s3) | `GET /sources` | 1b89bed77d3b | identical (1b89bed77d3b) | identical |
| source (g3-s3) | `GET /diagnostics/health` | f2e89cdf2852 | identical (f2e89cdf2852) | identical |
| loopback (g3-s3) | `GET /diagnostics/health` | f2e89cdf2852 | identical (f2e89cdf2852) | identical |
| source (g3-s3) | `GET /diagnostics/stream-telemetry` | cd144960c309 | identical (cd144960c309) | identical |
| loopback (g3-s3) | `GET /diagnostics/stream-telemetry` | cd144960c309 | identical (cd144960c309) | identical |
