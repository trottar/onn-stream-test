# B95 — addendum 1 (after the design's hash, before the validation runs)

B93's session copied the game into its temp folder ("a copy: the library's file is only read"). For the real proof
(T88, a PS1 disc image) that is a large copy on every load, and a `.cue` copied alone loses its track files. **Changed:**
the session reads the game **in place** (RetroArch only reads content); a missing file is an error. The temp folders
still hold everything RetroArch writes (config, saves, states, logs). B93's and B95's tests run unchanged.
