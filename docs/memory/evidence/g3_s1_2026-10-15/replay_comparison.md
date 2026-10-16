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
