# Stage 2 — the fetch (the one thing fetched; 16:05:36Z; on the user's recorded go)

- **The addresses** (public; the Godot project's own release on GitHub, tag `4.7.2-stable`; `checksum.txt`):
  `https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip`
  (77,860,424 bytes) and `https://github.com/godotengine/godot/releases/download/4.7.2-stable/SHA512-SUMS.txt`
  (5,682 bytes; kept here). Nothing else fetched; nothing installed.
- **SHA-512** — the published line and the computed one: `9aa00f7a…ed54c65` both, **equal** (`checksum.txt`, full
  values).
- The zip held one file (the executable, 146,414,384 bytes); unpacked off both repos into **the tools folder** under
  the user's home (a new folder; no path in this record), made executable for the user.
- **`--version`: `4.7.2.stable.official.ed1daf0bf`** (`version.txt`); **`--help`** kept (`help.txt`, colours taken out,
  the tools folder's path replaced). Every flag used was confirmed in it first: `--headless`, `--path`, `--import`,
  `--script`, `--rendering-method`, `--rendering-driver`, `--resolution`, `--position`, `--print-fps`,
  `--disable-vsync`, `--max-fps`. The download folder (A's, off both repos) keeps the zip and the sums file.
