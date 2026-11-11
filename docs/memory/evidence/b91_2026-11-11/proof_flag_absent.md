# B91 — `debug.privyhub.mapping_picture=0` = today's editor (`b91.diff`)

| file | hunk | the property `0` / `off` |
| --- | --- | --- |
| `MainActivity.kt` | `editorPlan`, `pictureLegend` | both `null`: they are built only when `pictureView != null` (B86's gate: `MappingPicture.fromSystem()` false → `pictureView` null) |
| `MainActivity.kt` | the picture and legend added to the container | `pictureView != null && …` false → nothing added (as today's off path) |
| `MainActivity.kt` | the rows' `textSize = MappingEditorLayout.ROW_TEXT_SP` | the constant is `17f`, today's literal: the same value |
| `MainActivity.kt` | `editorView` | `pictureView != null && …` false → `scroll` (today's view passed to `setView`) |
| `MainActivity.kt` | after `dialog.show()`: `window.setLayout` | `editorPlan != null && …` false → not called (the theme's size, as today) |
| `streaming/MappingPicture.kt` | anchors, shape bounds, `placeLabels` | read only by the picture's view (never created) and the tests |
| `streaming/MappingEditorLayout.kt` | new | read only when the picture is on |
| `streaming/ControllerPictureView.kt` | `beside`, `drawBeside`, `onMeasure`'s beside branch | the view is never created; with it created and `beside` not called, B89's `onMeasure` / `onDraw` paths run unchanged |
| `B91MappingBesideTest.kt` | new | `theSwitch`: `parse("0")`, `parse("off")` false; `parse(null)`, `parse("")` true |

With the property `0` the editor makes the same calls with the same values as HEAD's off path. The APK tree's only
source differences from the baseline that rebuilds `3f21e2c6…` byte for byte are B91's five files
(`apk_source_diff.txt`). K5 / K7 (`tests_mutations_jvm.txt`) catch the beside layout turned off and the switch ignored.
