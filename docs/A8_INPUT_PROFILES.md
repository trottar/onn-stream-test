# PrivyHub A8 — Named Input Profiles

## Status

- A8.1 schema / CRUD / assignment backend: **runtime validated**
- A8.2 RetroArch session adapter: **COMPLETE / runtime validated**
- A8.3 Android profile editor: **development patch; runtime UI validation required**
- A8.4 per-game UI / diagnostics polish: pending

## Architecture

```text
Physical controller
    ↓
Android canonical XUSB / PHI1 transport     [unchanged]
    ↓
Windows ViGEm X360 devices                  [unchanged]
    ↓
PrivyHub named gameplay profile             [A8.1]
    ↓
session-only RetroArch binding adapter      [A8.2]
    ↓
RetroPad / core
```

Save / Load / Pause / End remain outside this gameplay mapping layer.

PS1 Digital vs DualShock remains the existing, separate libretro-device profile.

## Storage

Path:

```text
data/games/input_profiles.json
```

Schema version: `1`.

The immutable `Default` profile is virtual. A missing file is a valid zero-override state.

Custom IDs are monotonic:

```text
profile_000001
profile_000002
...
```

Assigned profiles cannot be deleted until games are reassigned.

## A8.2 adapter behavior

The effective profile is resolved in `EmulatorManager._prepare_input_override()`.

The adapter writes only session-scoped bindings into:

```text
data/games/retroarch/config/privyhub-input.cfg
```

### Default profile

`Default` emits no explicit gameplay bindings. RetroArch's existing controller autoconfiguration remains authoritative.

### Custom profiles

Only mapped RetroPad targets are overridden. Unspecified targets remain on the existing autoconfig.

For digital targets, the adapter explicitly clears the alternate axis/button bind so the old autoconfig cannot remain as a second physical source for the remapped target.

For analog-stick targets, both plus/minus directions are overridden together and button fallbacks are nulled.

### Canonical XUSB source model

The source tokens use the already-validated PHI1 / ViGEm X360 semantics.

Physical digital sources:

- A/B/X/Y
- LB/RB
- Start/Select
- L3/R3
- D-pad directions

Physical trigger sources:

- LT/RT

Physical analog sources:

- left X/Y
- right X/Y

The adapter uses RetroArch's XInput/Xbox-controller button and axis layout.

### Fail-closed compatibility

A8.1 stores canonical source/target names.

A8.2 rejects nonsensical runtime combinations, for example:

```text
RetroPad left_x <- physical A button
```

Analog RetroPad targets require analog-stick sources.

Digital RetroPad targets accept digital/D-pad sources and triggers.

## Diagnostics

Deterministic generated-config probe:

```powershell
python .\tools\probe_a8_2_input_adapter.py
```

This creates temporary profile data, checks P1/P2 generated RetroArch binds, confirms `Default` emits no A8 bindings, tests fail-closed behavior, and restores both:

- `data/games/input_profiles.json`
- `data/games/retroarch/config/privyhub-input.cfg`

to their exact pre-probe bytes.

### Runtime E2E

After restarting the companion:

```powershell
python .\tools\probe_a8_2_runtime_mapping.py
```

The probe:

1. refuses to start if a game is already active;
2. chooses an existing PS1 game through the localhost Games API;
3. creates a temporary P1 A/B-swap profile;
4. assigns it to that game;
5. tells the user which game to launch normally on the onn;
6. asks whether the A/B swap was actually observed and meta controls remained normal;
7. restores `input_profiles.json` byte-for-byte.

If runtime validation fails, return only:

```text
logs/games/a8_2_runtime_mapping_probe.txt
```

## Durable rules

- Do not modify PHI1/XUSB transport for A8 mapping.
- Do not modify the ViGEm bridge for A8 mapping.
- Do not merge PS1 Digital/DualShock selection into gameplay remapping.
- Do not remap Save/Load/Pause/End.
- Use session-only RetroArch config rather than persistent RetroArch user configuration.
- Malformed or incompatible assigned profiles fail closed before game launch.
- Extend the existing debug harness rather than inventing parallel troubleshooting paths.


## A8.2 installer verifier correction

The first A8.2 installer failed **before modification** because it attempted to
reconstruct the expected A8.1 files from Git checkpoint bytes plus the bundled
A8.1 transformer.

That reconstruction is not authoritative for this project. The authoritative
state is the local working tree and the receipt written by the successful A8.1
installer:

```text
logs/games/a8_1_input_profiles_install.txt
```

The corrected A8.2 installer requires that receipt to report:

```text
Result: INSTALLED SUCCESSFULLY
Patch: privyhub_a8_1_input_profiles
Storage probe: PASS
Storage restored: True
```

It reads the receipt's exact post-install SHA-256 values for:

```text
companion/games/emulator_manager.py
companion/plugins/games.py
```

and requires the current files to match those exact receipt values before A8.2
can modify anything.

It also requires the A8.1 source markers and the exact A8.1 documentation hash.

No Git-byte reconstruction is used.


## A8.2 controller preflight ordering correction

Runtime evidence showed the generated named-profile bindings were correct in
both `privyhub-input.cfg` and the final `privyhub-session.cfg`, but RetroArch
initially failed to initialize the configured `xinput` joypad driver and only
autoconfigured the two virtual Xbox 360 controllers later.

The authoritative Games plugin source showed why: the existing
`ensure_game_controller()` call ran only after the normal emulator launch had
already completed.

The corrected order is:

```text
create/verify existing persistent ViGEm X360 controllers
-> existing RetroArch launch
-> existing pause/handoff
-> existing native stream start/resume
```

This does not change PHI1/XUSB transport, ViGEm report mapping, Android input,
Save/Load/Pause/End, A8 profile semantics, or audio/video.

RetroArch documents that explicit `input_playerN_*_btn/axis` binds take
priority over controller autoconfiguration, so A8.2 continues using explicit
session bindings.

Runtime success requires the fresh A8.2 probe to report:

```text
A/B swap observed: True
Generated swapped RetroPad binds: True
XInput startup fallback observed: False
Result: A8_RUNTIME_MAPPING_OBSERVED
Input profile storage restored: True
```


## A8.2 final runtime validation

A8.2 is runtime validated.

The boundary diagnostics established, in order:

```text
pre-RetroArch PHI1 -> ViGEm/XInput canonical transport: PASS
prelaunch A8 assignment generation: PASS
postlaunch physical A -> XInput A: PASS
postlaunch physical B -> XInput B: PASS
postlaunch A8 assignment unchanged: PASS
XInput startup fallback observed: False
Xbox controllers autoconfigured: True
```

The final gameplay test then confirmed the intended **physical BUTTON A /
physical BUTTON B remap** in Crash Team Racing.

Important terminology:

- `Player 1` / `Player 2` means controller/player assignment.
- `Physical A button` / `Physical B button` means buttons printed on the
  physical controller.
- `RetroPad A` / `RetroPad B` means libretro's virtual gameplay controls.

These must not be called merely "A/B swap" when the distinction matters.

## A8.3 Android profile editor

A8.3 adds a game-scoped Android entry point:

```text
Game
  -> Options
  -> Input Profile
```

It reuses the existing A8.1 API and A8.2 runtime adapter.

Supported editor operations:

- assign `Default` or any reusable custom profile to the selected game;
- create a named reusable profile;
- edit Player 1 mappings;
- edit Player 2 mappings;
- rename a custom profile;
- duplicate a custom profile;
- reset a custom profile to zero explicit overrides;
- delete an unassigned custom profile.

The editor displays mapping direction explicitly:

```text
RetroPad target <- Physical controller input
```

For example:

```text
RetroPad A <- Physical A button
RetroPad B <- Physical B button
```

`RetroPad` labels are virtual emulator controls. `Physical` labels are the
controls printed on the controller.

Unmapped targets remain on the existing RetroArch Default/autoconfig path.

The Android editor does **not** modify:

- Android PHI1/XUSB transport;
- Windows ViGEm report mapping;
- controller startup ordering;
- RetroArch launch/session lifecycle;
- Save / Load / Pause / End;
- audio/video.

Custom gameplay profile changes apply on the next game launch.

### Android source probe

```powershell
python .\tools\probe_a8_3_android_input_profiles.py --root L:\Projects\onn-stream-test
```

Expected:

```text
Result: PASS
Production controller transport changed: False
```

A8.3 remains a development patch until the UI is exercised on the onn and a
custom profile is confirmed in gameplay.


## A8.3 v3 dialog-list correction

The first runtime UI check found that `Game -> Options -> Input Profile` opened
without selectable profile actions even though the A8.3 source probe confirmed
the editor and backend hooks were installed.

Root cause: `showGameInputProfileMenu()` configured the same AppCompat
`AlertDialog` with both message content and `setItems(...)`. On this Android TV
UI path the message content occupied the content panel and the selectable list
was not rendered.

v3 changes only this dialog construction:

```text
before: title + message + selectable items
after:  title showing current profile + selectable items
```

The v3 source probe explicitly fails if `showGameInputProfileMenu()` contains a
`setMessage(...)` call and requires its `setItems(...)` action list.

No A8 backend, runtime adapter, PHI1/XUSB, ViGEm, controller preflight,
Save/Load/Pause/End, audio, or video path is changed.


## A8.3 v4 complete directional permutation editor

The editor now models gameplay remapping as 24 directional endpoints per player:

- D-pad Up/Down/Left/Right;
- A/B/X/Y;
- L1/R1/L2/R2/L3/R3;
- Select/Start;
- Left Stick Left/Right/Up/Down;
- Right Stick Left/Right/Up/Down.

Every custom mapping begins from a complete Default permutation matching the
validated RetroArch Xbox/XInput autoconfiguration. In particular, the baseline
face layout is `RetroPad A <- Physical B`, `RetroPad B <- Physical A`,
`RetroPad X <- Physical Y`, `RetroPad Y <- Physical X`.

Stick directions are first-class sources and targets. RetroArch axis-direction
bindings allow, for example:

```text
RetroPad L2 <- Physical Right Stick Left
RetroPad R2 <- Physical Right Stick Right
```

and the reverse type:

```text
RetroPad Left Stick Left <- Physical D-pad Left
```

A physical stick direction mapped to a digital RetroPad control is thresholded
by RetroArch as an axis-bound digital input. A digital/hat/trigger input mapped
to a RetroPad stick direction becomes a directional analog binding (full-scale
for button/hat inputs; analog magnitude for axis inputs).

The Android editor maintains a local working copy. Duplicate sources or
unmapped targets turn the affected rows red. Save is disabled until every
RetroPad target has exactly one unique physical source. The backend already
rejects duplicate physical sources as an additional fail-closed check.

Legacy whole-axis A8.2 tokens remain accepted at runtime for compatibility with
existing profiles. The v4 editor writes directional endpoints.

### First directional E2E

Use **Emperor's New Groove (PS1)** and create a complete profile that swaps the
horizontal camera triggers with the physical right stick:

```text
RetroPad L2                 <- Physical Right Stick Left
RetroPad R2                 <- Physical Right Stick Right
RetroPad Right Stick Left   <- Physical LT trigger
RetroPad Right Stick Right  <- Physical RT trigger
```

All other rows remain on the Default baseline. This preserves the one-to-one
permutation while moving camera-left/right from L2/R2 onto the right stick.

A8.2 ordinary face-button swapping remains runtime validated and is not being
retested as part of this directional proof.


## A8.3 v5 editor UI reachability correction

Runtime observation after v4: the directional backend and generated Android editor
were installed, but the user still reached only profile-selection UI rather than
the mapping controls.

Exact source inspection found two remaining Android `AlertDialog` list collisions:

1. the custom-profile action dialog used both `setMessage(...)` and `setItems(...)`;
2. the physical-source chooser inside the mapping editor also used both
   `setMessage(...)` and `setItems(...)`.

These repeated the already-fixed v3 dialog-content mistake at deeper UI levels.

v5 is Android-UI-only. It:

- removes both remaining message/list collisions;
- exposes `Edit Current Player 1 Mapping` and `Edit Current Player 2 Mapping`
  directly in `Game -> Options -> Input Profile` whenever the current profile is
  custom;
- opens Player 1 mapping immediately after creating/assigning a new profile;
- preserves the v4 24-endpoint directional mapper, red invalid rows, and Save
  gate unchanged.

No emulator/runtime/controller/artwork code changes in v5.


## A8.3 v6 simple current-mapping editor

The directional mapping model is unchanged. v6 changes only Android presentation.

The Player mapping screen now presents each destination control as a simple
three-part row:

```text
L2
Current: LT Trigger
[ Change ]

R2
Current: RT Trigger
[ Change ]
```

Normal UI labels intentionally omit `RetroPad`, `Physical`, and mapping-arrow
syntax. Selecting `Change` opens a list titled with the destination and current
source, for example:

```text
Change L2 - Current: LT Trigger
```

The editor still enforces the complete one-to-one directional permutation:
conflicting or unmapped rows are red and Save remains disabled until every row
is valid.

The Emperor's New Groove acceptance mapping remains:

```text
L2               -> Right Stick Left
R2               -> Right Stick Right
Right Stick Left -> LT Trigger
Right Stick Right-> RT Trigger
```

v6 does not change the directional runtime backend, PHI1/XUSB, ViGEm,
Save/Load/Pause/End, audio/video, or A6 artwork.


## A8.3 v7 — Xbox-only labels and player sync

The v6 Current/Change editor interaction was runtime-confirmed as working and is
preserved. v7 changes only Android presentation/editor working-copy behavior.

User-facing control names are now Xbox-style only:

```text
A / B / X / Y
LB / RB / LT / RT
L3 / R3
Back / Start
D-pad Up / Down / Left / Right
Left Stick Up / Down / Left / Right
Right Stick Up / Down / Left / Right
```

PlayStation-style `L1/R1/L2/R2/Select` labels and mixed labels such as
`LT Trigger` are not shown in the normal mapping editor.

Each player editor also has one working-copy action:

```text
Sync Player 1 with Player 2
Sync Player 2 with Player 1
```

Sync copies the other player's complete current saved mapping into the player
being edited. It does not save immediately. The existing red conflict/unmapped
validation and disabled-Save gate still apply, so the copied mapping must be
valid before it can be committed.

v7 does not change the directional backend, RetroArch generator, controller
transport, game lifecycle, audio/video, or artwork.


## A8.3 v8 — conflict choices visible before selection

The working v7 Xbox-only Current/Change editor is preserved. v8 changes only
the Android source-choice popup.

When changing one destination row, any physical source already assigned to a
different destination in that player's unsaved working mapping is rendered
red in the popup before selection. The source currently owned by the row being
edited is excluded from the conflict set unless another row also uses it.

Red choices remain selectable so multi-step swaps can be constructed. Selecting
one can temporarily create duplicate red rows; the existing Save gate remains
disabled until the complete 24-endpoint mapping is one-to-one again.

The generalized directional backend, RetroArch generator, controller transport,
player-sync behavior, game lifecycle, audio/video, and artwork are unchanged.
