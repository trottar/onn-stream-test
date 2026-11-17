# H7-D1 — the four passes (every read from each keep folder's `index.csv`; ids replaced)

**Disclosed, before the passes counted here:** a first T88-early attempt sent every call to a wrong address (my driver's base URL lacked a slash): all 404, nothing launched, nothing loaded. A first T88-late attempt read RetroArch's command port before the launch (each launch writes a new one): `GET_STATUS` never answered, so no `h7-start` was sent (no load) and the title was stopped. Both re-run with the driver fixed; their logs in A's working folder.

## T88 early

- the keep folder `runtime/h7_frames/<T88 id>_20261117T055540Z/` (git-ignored); **45 pictures**, 45 `index.csv` rows
- `launch_answer` at 2.273 s: {"code": 200, "active": true, "paused": true, "profile_matches": true}
- `h7_start_answer` at 2.351 s: {"code": 200, "since_launch_s": 0.078, "watch": "started", "loaded": true, "begin": "setup", "load_line_ms": 23.8, "keep": "<id>_20261117T055540Z", "replaced": false}
- `bench_release` at 2.44 s: {"code": 200, "released": true}
- `status` at 2.447 s: {"active": true, "paused": false, "setup_profile": true}
- `reads_done` at 47.518 s: {"reads": 45, "recognised": false, "state": "watching", "cls": "start"}
- `load_line` at 48.461 s: {"present": true, "lines": 1, "scratch_in_setup": [true], "bytes": [16777240]}
- the thresholds (the spec, version 2): {"screen": 0.082, "end_P1": 0.1044, "end_P2": 0.0983, "start": 0.0958}

| second | class | distances |
| --- | --- | --- |
| 1.20 | other | {"screen": 0.1757} |
| 2.00 | other | {"screen": 0.0856} |
| 3.00 | other | {"screen": 0.0845} |
| 4.00 | other | {"screen": 0.0836} |
| 5.00 | other | {"screen": 0.0863} |
| 6.00 | other | {"screen": 0.0828} |
| 7.00 | other | {"screen": 0.0874} |
| 8.00 | other | {"screen": 0.0916} |
| 9.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 10.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0117} |
| 11.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |
| 12.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 13.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 14.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 15.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 16.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 17.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 18.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |
| 19.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 20.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 21.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 22.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 23.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 24.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 25.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0117} |
| 26.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 27.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 28.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 29.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 30.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 31.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 32.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 33.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 34.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 35.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 36.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 37.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 38.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 39.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |
| 40.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 41.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 42.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 43.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 44.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 45.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |

- **the first read naming `start`:** 9.00 s after the load
- **the least start distance:** 0.0117 at 10.00 s

## T88 late

- the keep folder `runtime/h7_frames/<T88 id>_20261117T055857Z/` (git-ignored); **45 pictures**, 45 `index.csv` rows
- `launch_answer` at 1.662 s: {"code": 200, "active": true, "paused": true, "profile_matches": true}
- `h7_start_answer` at 17.134 s: {"code": 200, "since_launch_s": 15.472, "watch": "started", "loaded": true, "begin": "setup", "load_line_ms": 27.9, "keep": "<id>_20261117T055857Z", "replaced": false}
- `bench_release` at 1.764 s: {"code": 200, "released": true}
- `status_before_pause` at 16.778 s: {"status": "PLAYING"}
- `paused` at 17.095 s: {"status": "PAUSED", "toggles": 1}
- `unpaused` at 17.449 s: {"status": "PLAYING"}
- `status` at 17.458 s: {"active": true, "paused": false, "setup_profile": true}
- `reads_done` at 62.529 s: {"reads": 45, "recognised": true, "state": "watching", "cls": "start"}
- `load_line` at 63.434 s: {"present": true, "lines": 1, "scratch_in_setup": [true], "bytes": [16777240]}
- the thresholds (the spec, version 2): {"screen": 0.082, "end_P1": 0.1044, "end_P2": 0.0983, "start": 0.0958}

| second | class | distances |
| --- | --- | --- |
| 1.20 | other | {"screen": 0.0949} |
| 2.00 | other | {"screen": 0.0898} |
| 3.00 | other | {"screen": 0.089} |
| 4.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 5.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 6.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |
| 7.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 8.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 9.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 10.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 11.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |
| 12.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 13.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 14.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 15.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 16.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 17.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0117} |
| 18.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |
| 19.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 20.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 21.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 22.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 23.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 24.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 25.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 26.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 27.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 28.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0117} |
| 29.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 30.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 31.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 32.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0037, "start": 0.0117} |
| 33.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 34.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |
| 35.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 36.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 37.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 38.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 39.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |
| 40.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 41.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0118} |
| 42.00 | start | {"end_P1": 0.2029, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 43.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} |
| 44.00 | start | {"end_P1": 0.2028, "end_P2": 0.1976, "screen": 0.0038, "start": 0.0117} |
| 45.00 | start | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0039, "start": 0.0118} |

- **the first read naming `start`:** 4.00 s after the load
- **the least start distance:** 0.0117 at 8.00 s

## T89 early

- the keep folder `runtime/h7_frames/<T89 id>_20261117T055953Z/` (git-ignored); **45 pictures**, 45 `index.csv` rows
- `launch_answer` at 1.92 s: {"code": 200, "active": true, "paused": true, "profile_matches": true}
- `h7_start_answer` at 2.002 s: {"code": 200, "since_launch_s": 0.082, "watch": "started", "loaded": true, "begin": "setup", "load_line_ms": 56.4, "keep": "<id>_20261117T055953Z", "replaced": false}
- `bench_release` at 2.094 s: {"code": 200, "released": true}
- `status` at 2.102 s: {"active": true, "paused": false, "setup_profile": true}
- `reads_done` at 47.17 s: {"reads": 45, "recognised": false, "state": "watching", "cls": "other"}
- `load_line` at 48.05 s: {"present": true, "lines": 1, "scratch_in_setup": [true], "bytes": [16793440]}
- the thresholds (the spec, version 3): {"end": 0.1011, "start": 0.0932}

| second | class | distances |
| --- | --- | --- |
| 1.20 | other | {"end": 0.2904, "screen": 0.2525, "start": 0.2525} |
| 2.00 | other | {"end": 0.3077, "screen": 0.2545, "start": 0.2545} |
| 3.00 | other | {"end": 0.3092, "screen": 0.2529, "start": 0.2529} |
| 4.00 | other | {"end": 0.3078, "screen": 0.2535, "start": 0.2535} |
| 5.00 | other | {"end": 0.309, "screen": 0.2561, "start": 0.2561} |
| 6.00 | other | {"end": 0.3071, "screen": 0.257, "start": 0.257} |
| 7.00 | other | {"end": 0.3058, "screen": 0.258, "start": 0.258} |
| 8.00 | other | {"end": 0.3061, "screen": 0.2554, "start": 0.2554} |
| 9.00 | other | {"end": 0.3104, "screen": 0.2551, "start": 0.2551} |
| 10.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 11.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 12.20 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 13.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 14.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 15.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 16.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 17.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 18.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 19.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 20.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 21.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 22.20 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 23.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 24.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 25.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 26.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 27.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 28.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 29.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 30.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 31.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 32.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 33.20 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 34.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 35.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 36.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 37.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 38.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 39.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 40.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 41.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 42.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 43.20 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 44.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 45.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |

- **the first read naming `start`:** never in 45
- **the least start distance:** 0.2525 at 1.20 s

## T89 late

- the keep folder `runtime/h7_frames/<T89 id>_20261117T060103Z/` (git-ignored); **45 pictures**, 45 `index.csv` rows
- `launch_answer` at 2.456 s: {"code": 200, "active": true, "paused": true, "profile_matches": true}
- `h7_start_answer` at 17.974 s: {"code": 200, "since_launch_s": 15.518, "watch": "started", "loaded": true, "begin": "setup", "load_line_ms": 57.2, "keep": "<id>_20261117T060103Z", "replaced": false}
- `bench_release` at 2.565 s: {"code": 200, "released": true}
- `status_before_pause` at 17.58 s: {"status": "PLAYING"}
- `paused` at 17.896 s: {"status": "PAUSED", "toggles": 1}
- `unpaused` at 18.279 s: {"status": "PLAYING"}
- `status` at 18.288 s: {"active": true, "paused": false, "setup_profile": true}
- `reads_done` at 63.364 s: {"reads": 45, "recognised": false, "state": "watching", "cls": "other"}
- `load_line` at 64.242 s: {"present": true, "lines": 1, "scratch_in_setup": [true], "bytes": [16793440]}
- the thresholds (the spec, version 3): {"end": 0.1011, "start": 0.0932}

| second | class | distances |
| --- | --- | --- |
| 1.20 | other | {"end": 0.3085, "screen": 0.2606, "start": 0.2606} |
| 2.00 | other | {"end": 0.3085, "screen": 0.2606, "start": 0.2606} |
| 3.00 | other | {"end": 0.3085, "screen": 0.2606, "start": 0.2606} |
| 4.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 5.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 6.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 7.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 8.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 9.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 10.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 11.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 12.20 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 13.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 14.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 15.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 16.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 17.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 18.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 19.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 20.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 21.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 22.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 23.20 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 24.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 25.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 26.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 27.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 28.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 29.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 30.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 31.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 32.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 33.20 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 34.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 35.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 36.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 37.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 38.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 39.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 40.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 41.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 42.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 43.20 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 44.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |
| 45.00 | other | {"end": 0.3101, "screen": 0.262, "start": 0.262} |

- **the first read naming `start`:** never in 45
- **the least start distance:** 0.2606 at 1.20 s

