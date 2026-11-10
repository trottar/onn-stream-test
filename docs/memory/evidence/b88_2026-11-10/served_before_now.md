| call | method | served before (HEAD) | served now (B88) |
| --- | --- | --- | --- |
| `/sources` | GET | yes (200) | yes (200) |
| `/plugins/games/status` | GET | yes (200) | yes (200) |
| `/plugins/games/games` | GET | yes (200) | yes (200) |
| `/plugins/games/favorite` | POST | yes (200) | yes (200) |
| `/plugins/games/player-mode` | POST | yes (200) | yes (200) |
| `/plugins/games/controller-profile` | POST | yes (503) | yes (503) |
| `/plugins/games/ps1-multitap` | POST | yes (503) | yes (503) |
| `/plugins/games/native-stream-stop` | POST | yes (200) | yes (200) |
| `/plugins/games/mod-profiles` | POST | yes (200) | yes (200) |
| `/plugins/games/mod-catalog` | POST | yes (200) | yes (200) |
| `/plugins/games/cheat-profiles` | POST | yes (503) | yes (503) |
| `/plugins/games/cheat-catalog` | POST | yes (503) | yes (503) |
| `/plugins/games/input-profiles` | GET | yes (200) | yes (200) |
| `/plugins/games/launch` | POST | yes (503) | yes (503) |
| `/plugins/games/ps2-patches` | POST | **NO** (400, unknown action) | yes (503) |
| `/plugins/games/stop` | POST | yes (200) | yes (200) |
| `/stop` | POST | yes (200) | yes (200) |
| `/diagnostics/vod-client` | POST | yes (400) | yes (400) |
| `/plugins/epg/prefetch` | POST | yes (200) | yes (200) |
| `/plugins/epg/guide` | GET | yes (400) | yes (400) |
| `/plugins/tv_state/state` | GET | yes (200) | yes (200) |
| `/plugins/tv_state/state` | POST | yes (400) | yes (400) |
| `/diagnostics/health` | GET | yes (200) | yes (200) |
| `/diagnostics/self-test` | POST | yes (200) | yes (200) |
| `/diagnostics/bundle` | POST | yes (500) | yes (500) |
| `/plugins/games/decoder-session-log` | POST | yes (200) | yes (200) |
| `/plugins/games/native-stream-start` | POST | yes (503) | yes (503) |
| `/plugins/games/native-stream-relaunch-ports` | POST | yes (200) | yes (200) |
| `/plugins/games/native-stream-heartbeat` | POST | yes (200) | yes (200) |
| `/diagnostics/client-health` | POST | yes (400) | yes (400) |
| `/plugins/games/native-stream-ready` | POST | yes (503) | yes (503) |
| `/plugins/games/native-stream-desync` | POST | yes (200) | yes (200) |
| `/plugins/games/input-profile-create` | POST | yes (200) | yes (200) |
| `/plugins/games/input-profile-update` | POST | yes (503) | yes (503) |
| `/plugins/games/input-profile-delete` | POST | yes (503) | yes (503) |
| `/plugins/games/input-profile-assign` | POST | yes (503) | yes (503) |
| `/plugins/games/recovery-resume` | POST | yes (503) | yes (503) |
| `/plugins/games/recovery-copy` | POST | yes (503) | yes (503) |
| `/plugins/games/recovery-discard` | POST | yes (200) | yes (200) |
| `/plugins/games/save-state` | POST | yes (503) | yes (503) |
| `/plugins/games/load-state` | POST | yes (503) | yes (503) |
| `/plugins/games/disc-swap` | POST | yes (503) | yes (503) |
| `/plugins/games/systems` | GET | yes (200) | yes (200) |
| `/plugins/games/details` | GET | yes (200) | yes (200) |
| `/plugins/iptv_org/categories` | GET | yes (200) | yes (200) |
| `/plugins/iptv_org/channels` | GET | yes (400) | yes (400) |

served: before 45 / 46, now 46 / 46
HEAD: the onn's Save (POST ps2-patches ws=1) -> 400 (unknown action); details' ps2_patches.on after it -> []
B88: the onn's Save (POST ps2-patches ws=1) -> 200; details' ps2_patches.on after it -> ['ws']
