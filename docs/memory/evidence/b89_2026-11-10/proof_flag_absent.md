# B89 — `debug.privyhub.mapping_picture=0` = today's editor (`b89.diff`)

| file | hunk | the property `0` / `off` |
| --- | --- | --- |
| `streaming/MappingPicture.kt` | the geometry, `shortLabels`, `pictureSize`, `svg`; `LAYOUT` now from the boxes | read only by the picture's view; B86's functions (`padLabel`, `gameLabel`, `rowText`, `pictureLabels`, `changed`, `parse`) unchanged |
| `streaming/ControllerPictureView.kt` | the drawing and `onMeasure` | the view is never created: `MainActivity`'s B86 gate (`MappingPicture.fromSystem()` false → `pictureView` null) |
| `B89MappingPictureTest.kt` | new | — |

`MainActivity.kt` is not touched by B89: with the property `0` the editor is today's, the same calls and strings as
B86's off path. The APK tree's only source differences from the baseline that rebuilds `c801caab…` byte for byte are
B89's three files (`apk_source_diff.txt`).
