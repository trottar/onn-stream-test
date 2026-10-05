# E1-S1 inventory — the ROADMAP E1 workloads and the samplers on this host

Written 2026-10-05 (06:10-06:45Z) **before any suite run**. Sources: the
code (`companion/`, `PrivyHub/app/src/main/java/`), the host's `/proc` and
`/sys`, the companion's own routes (read-only `GET`s), and one forced EPG
refresh used to confirm the route works (`ComedyCentral.us@East`, 6.2 s,
88 programmes; the companion's normal cache write). Host: the HP EliteDesk
prototype, Ryzen 5 PRO 4650G (6 cores / 12 threads), 14 GiB visible RAM,
12 GiB swap on the same NVMe, one 238 GB NVMe (`nvme0n1`: `/`, swap, EFI),
one wired interface (`eno1`). Headless X on `:0` (`H2`).

## A. Background on the host that is not PrivyHub

Resident and outside PrivyHub, so every host figure carries it: several
Claude Code processes (idle sessions plus the one running this task),
the Claude desktop app, a VPN daemon, the XFCE session (xfwm4, panel,
desktop), Xorg, PulseAudio. Idle sample: host CPU mean ~0.8 %, of which the
non-PrivyHub "other" bucket is most. The sampler puts all of this in its
`other` row (CPU only, top three by `comm`) so a host-CPU difference can be
attributed. Xorg (RetroArch's window, `x11grab`'s source) and PulseAudio
(the stream's audio capture) get their own rows because the game path uses
them.

## B. The workloads

| E1 workload | what it is on this host | unattended today? | natural steady state | telemetry it already produces |
| --- | --- | --- | --- | --- |
| **idle Linux + PrivyHub** | the companion unit (`privyhub-companion`, `python3 -u ./companion/privyhub_service.py`, plus its child `companion/range_server.py` on :8000), no game, no stream, no source; the onn on its launcher or screensaver | **YES** | the companion idle after its restart (single-threaded, ~37 MB RSS) | none of its own beyond the journal |
| **Live TV** | a channel plays **upstream → ExoPlayer on the onn directly**: the app fetches the playlists itself (`TvRepository.kt:111-125`, iptv-org / Free-TV / freecasthub, Room DB) and plays in `MainActivity` (`MA:5026` → `MA:15082`); **no host proxy, restream or remux**. The host's share is the TV-state sync (`/plugins/tv_state/state`) and the EPG (`/plugins/epg/*`: the warmer thread, the `npm run grab` child) | **NO** — no intent, extra or deep link starts a channel (`MainActivity` reads only `privyhub.stale_output_ms`), so a channel needs D-pad navigation; D5's playback row was the user's manual smoke; D122/D136 are API-level only | a tuned channel (on the onn); on the host: idle + the EPG work the TV entry triggers | the app's player; host: `/plugins/epg/status` (`background_refresh`) |
| **VOD** | a local file served **as-is** over HTTP range requests by `range_server.py` (`/vod/...`, `svc:1594-1640`); played by `MainActivity`; **no transcode anywhere** | **NO — ABSENT**: `data/storage.json`'s `vod_root` is on the external media drive (an autofs mount), and the drive is **not attached** ("No such device"; `logs/server.log`: VOD available False). The default `media/vod` is empty | a playing VOD: range reads at the file's bitrate | `logs/server.log` (range server) |
| **browser / live source** | `companion/config/sources.json` `browser`: `scripts/start_browser.ps1` (ffmpeg `ddagrab` + dshow → HLS) | **NO — ABSENT**: Windows-only (PowerShell, dshow/ddagrab); no `powershell.exe` / `pwsh` on this host; no Linux implementation (C6 reclassified it, `D-101`) | — | — |
| **camera / live source** | `sources.json` `pc_camera`: `scripts/start_camera.ps1` (dshow webcam → HLS) | **NO — ABSENT**: Windows-only as above, **no camera attached** (no `/dev/video*`), no v4l2 code. `logs/pc_camera.log` (2026-09-15 08:11) holds only the launcher banner, nothing after: the PowerShell launch failed on Linux | — | `logs/pc_camera.log` (banner only) |
| **NES** | core `fceumm`, installed | **NO — ABSENT**: 0 files in `games/nes` (A9's correction: no fixture) | — | — |
| **SNES** | core `bsnes`, installed; **44 `.sfc`** in `games/snes`. Reference title for E1: *Super Mario World (USA)* (`game_snes_c6fecdcdddb35398`), whose title screen runs its own demo loop | **YES**, streamed through the companion with the onn (the product's path), the same launch/RESUME/BACK harness as PS1 | the title-screen demo loop at 60 fps | RetroArch's window-title frame counter (the measurement-only game override, as C5), the stream's heartbeat and C2 telemetry |
| **Genesis** | core `blastem`, installed | **NO — ABSENT**: 0 files in `games/genesis` | — | — |
| **PS1 local emulation** | RetroArch + Beetle PSX HW on the host, the **adopted 4x source** (1920×1080 window), no stream. **There is no local-only mode**: `POST /plugins/games/launch` starts RetroArch and **pauses** it (`games.py:3347-3349`); only `native-stream-ready` (which needs a stream) unpauses. So the row unpauses it with RetroArch's own command, `PAUSE_TOGGLE` on its network command port at 127.0.0.1 (the port the launch writes to `privyhub-input.cfg`, the same command `EmulatorManager.resume` sends), and confirms `GET_STATUS` PLAYING. Title: *Tekken 3 (USA)* | **YES** (with the unpause above; the client-silence recovery cannot fire: no controller packet ever arrives) | Tekken 3's attract loop | RetroArch's frame counter (title) |
| **PS1 + native streaming** | the adopted stream: `native_game_720p60_reference` 1280×720@60, 7000 kbps, live adaptive (ladder 5000-7000) by the drop-in, the 4x source, Tekken 3 attract, the onn as client through RESUME PLAYING (C5's harness) | **YES** | the attract loop at 7000 / 1280×720 | heartbeat (`rendered_frames`, `lost_packets`, audio underruns), C2 telemetry (`/diagnostics/stream-telemetry`), the decoder report at BACK, `host_resource_sampler` (30 s, started by the companion), the controller's decision log |
| **720p60 reference profile** | **the same row as PS1 + native streaming**: the adopted profile *is* `native_game_720p60_reference`; live adaptive tops out at its 7000 and stays there on a clean link. A separate fixed (adaptive-off) row would need the drop-in removed — a change to the adopted system — and is **not needed separately in E1** | (= the row above) | — | — |
| **higher Phase-C profiles** | the 1080p rung (12,600 kbps / 1920×1080) behind `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`, **not adopted**; entered by the test-only injection (`..._INJECT=1`, `inject?class=INCREASE_1080P` ≥ 60 s after PLAYING) and confirmed 1920×1080 in `native-stream-status`. One row, flags for that row only | **YES** (flags set and unset by the runner) | the attract loop at the rung | as the stream row + `adaptive_bitrate.level_size`, `width`/`height` |
| **metadata / storage work** | (a) **the EPG grab**: a forced refresh `POST /plugins/epg/refresh?channel_id=` runs the `npm run grab` child (private Node 24.21.0, the iptv-org/epg checkout under `data/epg/toolchain/`, 668 MB) synchronously, writes `data/epg/cache/<sha>.json`; one grab 6-20 s, network-bound (upstream guide sites); (b) **the games library scan** (`GamesPlugin._scan`, in-process, 5 s cache, on `GET /plugins/games/games`); (c) the **VOD scan** (in-process on `GET /sources`) — the VOD root is absent; (d) the **metadata reconcile** (`PrivyHubGameMetadataReconcile` thread at start; last result `SKIPPED_CURRENT`, 124 discovered) and `tools/update_game_metadata.py` (downloads DATs and box art into `media/`): **not run** — it writes library metadata, outside E1's no-change rule. No thumbnail generation exists | (a) + (b) **YES**; (c) ABSENT (drive); (d) not run | a cycle of forced grabs over a fixed channel list, with a library scan every 30 s | `/plugins/epg/status`; the route's own reply (`programme_count`, `attempts`) |
| **concurrent core workloads** | what can actually run at once on one client: **PS1 streaming + the EPG grab cycle** (the warmer/prefetch can run during a stream; the TV and the stream cannot share the onn). PS1 streaming + VOD transcode does not exist (no transcode); + a library scan is the in-process scan (ms). Two games at once: no (one emulator session) | **YES** (PS1 stream + EPG cycle) | the stream row's steady state with grabs running | the stream's + the EPG row's |

**Fixtures:** SNES (44) and PS1 (80 `.cue`) exist; **NES and Genesis have
none** — those rows stay ABSENT until the user supplies them.

## C. The samplers

**What exists:**

- `c5_m4_sampler.py` (C5-M4, copied through C5-CLOSE): 1 s per-CPU busy %,
  `gpu_busy_percent`, "GPU W" (hwmon `power1_average`/`input` — **on this
  APU that is the socket PPT, not the GPU alone**), Tctl, GPU edge,
  RetroArch and encoder % of one core; RetroArch's title counter; C2
  telemetry every 2 s; optional thumbnails.
- `c5_m4_host_table.py`: the per-hold table from those rows.
- `t2_sample.py` (D-BASE-T2): every 10 s, all hwmon temperatures, per-core
  cpufreq, encoder / RetroArch CPU, `eno1` counters, the onn (thermal,
  RSSI, link) and the Opal (read-only station row).
- `tools/host_resource_sampler.py`: started by the companion with every
  stream session, 30 s: temperatures, PPT, load, CPU / RSS / RssAnon /
  threads for RetroArch, the companion, the encoder.

**What E2 still needs, and whether this host exposes it (no root, no new
hardware):**

| E2 metric | on this host | `e1_sampler.py` field |
| --- | --- | --- |
| total / per-core CPU | yes (`/proc/stat`) | `cpu.mean_pct`, `cpu.max_pct`, `per_cpu` |
| process CPU | yes (`/proc/<pid>/stat`) | `procs.<cat>.cpu_pct` |
| RAM / working set per process | **yes: PSS** via `/proc/<pid>/smaps_rollup` for own-user processes (Xorg is root: RSS only) | `procs.<cat>.pss_kb`, `rss_kb`, `rss_anon_kb` |
| swap | yes (`/proc/meminfo`, `/proc/vmstat`) | `mem.swap_used_mb`, `pswpin/out_per_s` |
| memory / CPU / IO pressure | yes (PSI) | `psi_ms_per_s.*` |
| iGPU / render utilization | yes (`gpu_busy_percent`; `gpu_metrics` gfx activity) | `gpu.busy_pct`, `gpu.gfx_activity_pct` |
| hardware video engine | **yes: `gpu_metrics` v2.2 `average_mm_activity` = VCN** (0 at idle; read without root) | `gpu.vcn_activity_pct`, `vclk_mhz` / `dclk_mhz` |
| encoder headroom | encoder % of a core + VCN activity (no direct headroom counter) | `procs.encoder.cpu_pct`, `gpu.vcn_activity_pct` |
| storage latency / throughput | yes (`/proc/diskstats`, `nvme0n1`) and per-process IO (`/proc/<pid>/io`) | `disk.*`, `procs.<cat>.read/write_kBps` |
| network | yes (`/proc/net/dev`, `eno1`) | `net.eno1.*` |
| FEC / decoder telemetry | yes (C2, heartbeat, decoder report) | the suite's `key` block |
| end-to-end latency | partial: C2 `latency` (control RTT, receive→decode, output gap); glass-to-glass needs a camera — ABSENT | `key.stream` |
| temperatures / throttling | yes: Tctl, per-core / SoC / gfx temperatures (`gpu_metrics`), cpufreq, **`throttle_status`** (SMU); no Intel-style per-CPU throttle counters | `gpu.t_*`, `freq.*`, `throttled` |
| package power | **yes, coarse: socket power (whole W) and CPU / SoC power (mW) from `gpu_metrics`; hwmon PPT**. **RAPL `energy_uj` is root-only (0400) → not readable** without `sudo` | `gpu.socket_power_w`, `cpu_power_w`, `soc_power_w`, `ppt_w` |
| wall / idle power | **ABSENT** — needs a meter the user does not have | — |
| concurrency behaviour | yes, from the above on the concurrency row | — |

The sampler's own cost is recorded per sample (`cost_ms`, ~12 ms per 1-s
sample; its process row `e1_sampler`).
