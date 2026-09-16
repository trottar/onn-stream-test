---
memory_schema: 1
as_of: 2026-09-16
status: runtime_validated
classification: D5_EXTERNAL_STORAGE_REMOUNT_DEPENDS_ON_OS_MOUNT_ACTIVATION
---

# D5 external-storage eject/reinsert recovery evidence

## Test

The external VOD drive was ejected while PrivyHub was running.

Observed while absent:
- the existing VOD symlink target was unavailable;
- `/sources` returned zero VOD sources.

The drive was then physically reconnected.

Initial post-reconnect state:
- the symlink target remained unavailable;
- no external exFAT mount was visible;
- restarting PrivyHub did not restore the movie catalog.

The user then opened the external drive through the Linux directory/file-manager
UI.

Immediately afterward:
- the filesystem became mounted;
- the existing VOD symlink target became valid;
- PrivyHub dynamic rescanning repopulated the movie library;
- no companion restart was required for catalog recovery;
- movies played normally again on the onn.

## Classification

`D5_EXTERNAL_STORAGE_REMOUNT_DEPENDS_ON_OS_MOUNT_ACTIVATION`

## Interpretation

The failing boundary is OS-level mount activation, not PrivyHub catalog recovery.

D5 should remove dependence on desktop automount by providing a deterministic
appliance mount strategy and an explicit configurable bulk-media root. PrivyHub
must distinguish an unavailable configured root from an actually empty library.
