# B86 — `debug.privyhub.mapping_picture=0` = today's editor, hunk by hunk (`b86.diff`)

| file | hunk | the property `0` / `off` |
| --- | --- | --- |
| `streaming/MappingPicture.kt`, `streaming/ControllerPictureView.kt` | new | `MappingPicture.fromSystem()` = false (`theProperty`) |
| `MainActivity.kt`, `showEditInputProfilePlayerDialog` | `editorDefault` = null → `pictureView` = null; nothing added to the dialog | no picture, no legend |
| | `editorSourceLabel(source)` in place of `inputProfileSourceLabel(source)` (3 calls) | `pictureView == null` → `inputProfileSourceLabel(source)`: today's labels |
| | the Change dialog's title | `pictureView == null` → `"Change ${inputProfileTargetLabel(target)} - Current: $currentLabel"`: today's |
| | `refreshRows`: the row text and the hidden "Current:" line | only inside `if (pictureView != null)` |
| | `pictureView?.show(…)` | null → nothing |
| `B86MappingPictureTest.kt` | new | — |

**Display only, with the property on too:** no line touches `working`, `inputProfileSavedMapping` or
`saveInputProfileMapping`; the picture reads the working map (`theStoredMappingIsNeverTouched`).
