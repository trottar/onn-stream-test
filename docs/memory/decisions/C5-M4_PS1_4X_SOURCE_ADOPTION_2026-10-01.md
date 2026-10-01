---
memory_schema: 1
as_of: 2026-10-01
status: ADOPTED 2026-10-01 21:03Z — the PS1 source renders at internal resolution 4x into a 1920x1080 window (RetroArch fullscreen on the headless display), through a Beetle PSX HW core override and one line in the base core options and the six per-title copies. Adopted by the pre-registered rows V1-V6 (C5-M4A, sha256 18312026…), on the user's authorization of 2026-10-01. The stream profile, the companion's argv, the client and the 2D cores are unchanged
---

# C5-M4 — the PS1 source at 4x, adopted

## The user's words

2026-10-01, on C5-M4 Part 1's proposal: **"Yes apply the 4x config"**.
The task was `handoffs/C5-M4A_PS1_4X_SOURCE_ADOPTION_TASK.md`, adopted by
its pre-registered rows or restored from the backups. The evidence is
`../evidence/C5_M4A_PS1_4X_SOURCE_ADOPTION_2026-10-01.md`.

## What changed, file by file

All the files are under `~/.config/retroarch/config/Beetle PSX HW/`.
The backups are `../evidence/c5_m4a_2026-10-01/backup/`.

| file | before | after | change |
| --- | --- | --- | --- |
| `Beetle PSX HW.cfg` (core override) | absent | `dc4d6019…85b9` | new: `video_fullscreen = "true"`, `video_windowed_fullscreen = "true"` (C5-M4's proposal, byte for byte) |
| `Beetle PSX HW.opt` (base) | `78850771…54f0` | `e409d6c1…3b9f` | `beetle_psx_hw_internal_resolution` `"1x(native)"` → `"4x"` |
| `Twisted Metal 2 (USA).opt` | `78850771…54f0` | `e409d6c1…3b9f` | the same line |
| `Bomberman - Party Edition (USA).opt` | `acd5b92a…1a2d` | `86a52347…c83c` | the same line |
| `Crash Bash (USA).opt` | `acd5b92a…1a2d` | `86a52347…c83c` | the same line |
| `FIFA - Road to World Cup 98 (USA) (En,Fr,De,Es,Nl,Sv).opt` | `acd5b92a…1a2d` | `86a52347…c83c` | the same line |
| `Nicktoons Racing (USA).opt` | `acd5b92a…1a2d` | `86a52347…c83c` | the same line |
| `Speed Punks (USA).opt` | `acd5b92a…1a2d` | `86a52347…c83c` | the same line |

**Nothing else changed.** A recursive sha256 listing of
`~/.config/retroarch/` before and after the apply differs in these eight
files only.

The override file's first comment line still reads "(PROPOSED, not
applied)". It is applied byte for byte as proposed, and the comment is
cosmetic.

## What it does

- Every PS1 title launches into a **1920×1080 borderless window**, with
  the 4:3 picture pillarboxed at 1316×1008. Each renders at **4x
  internal resolution**, a 4096² render target.
- RetroArch logs "Core-specific overrides found … Beetle PSX HW.cfg" on
  every PS1 launch. `retroarch.cfg`'s own `video_fullscreen` and
  `video_windowed_fullscreen = "false"` lines are superseded by the
  override.
- The companion captures the 1920×1080 window and downscales it to the
  adopted 1280×720 stream at 7000. Its argv, its filter string and the
  profile are unchanged. **This is the quick win: the 4x source through
  today's stream.**
- The multitap path seeds a title's `.opt` from the base on that title's
  first multitap launch. So:
  - **a new PS1 title's copy inherits 4x** (CTR, multitap port 1 with no
    copy yet, would be seeded at 4x);
  - the existing copies carry the line now;
  - the multitap write edits only the two multitap keys. Verified: Crash
    Bash's `.opt` is hash-identical after its multitap session.

## What it does not change

- **The 2D cores.**
  - SNES (bsnes) still launches at 879×672 with no override loaded, and
    `bsnes.opt` is hash-identical.
  - fceumm and blastem have no options files before or after. Genesis and
    NES have no local content to launch.
  - `data/games/retroarch/retroarch.cfg` is unchanged.
- **The stream.** The profile `native_game_720p60_reference` (720p,
  7000, cap 90 KB, GOP 15) and `any_override` false are unchanged, as are
  the live adaptive default and the APK `de072762…835e`.
- **The rest of the PS1 core options** stay as they were: dither mode,
  texture filter, PGXP, MSAA, the renderer (OpenGL) and 8x. None was
  measured, and none is adopted.

## The measured cost

From C5-M4 §4, confirmed by C5-M4A's 20-min hold:

- **GPU busy** with the stream: 15 % → 21-22 % (p95 28). The GPU draws
  about 1 W more.
- **RetroArch** takes ~33-36 % of one core at either scale.
- **The encoder process** takes 36 % (C5-M4, 5 min) to 49 % (C5-M4A,
  20 min, T2) of one core, against 25-31 % on the 879×720 window. The
  capture now reads 2.25× the pixels and downscales them.
- **Tctl** peaks at 61-63 °C.
- **No minimum-hardware claim** is made; that is Phase E's.

**The picture,** offline on the 3D demo segment: content SSIM 0.838 →
0.873 as shown on the 1080p TV, at the same link cost. No ≥ 80-packet
frames; cap hits 9.7 s/min over the 20-min hold, the adopted 720p's usual
9-10.

## Revert (verbatim; no game running)

```bash
D="$HOME/.config/retroarch/config/Beetle PSX HW"
B=/home/privyhub/Projects/onn-stream-test/docs/memory/evidence/c5_m4a_2026-10-01/backup
curl -s localhost:8765/plugins/games/status | grep -q '"active": false' || echo "STOP: a game is running"
rm "$D/Beetle PSX HW.cfg"
cp "$B"/*.opt "$D"/
(cd "$D" && sha256sum *.opt)   # 7885077…54f0 for the base and Twisted Metal 2; acd5b92a…1a2d for the other five
```

RetroArch rewrites the `.opt` files on exit with the values in force, so
change them only with no game running. A title whose copy was first
seeded after the adoption (CTR, for example) carries 4x. To revert it,
set its line back to `"1x(native)"` or delete the copy, and the multitap
path re-seeds it from the base.

## Open picture items (the user's, TV only, nothing perceptual as a gate)

1. **Dither mode first.** `beetle_psx_hw_dither_mode` is `"1x(native)"`,
   so at 4x the native dither pattern is drawn at 4× size. The
   alternatives are "internal resolution" and "disabled".
2. The texture filter: textures stay nearest-filtered at 4x.
3. PGXP; MSAA; Vulkan; 8x (it missed C5-M4's R1 by one interval).

Each would be a measured arm before any change.
