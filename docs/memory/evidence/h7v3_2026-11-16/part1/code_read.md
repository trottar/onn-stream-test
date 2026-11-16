# Why the game could not be brought to running and unpaused with no client (change 3: the code read, read only)

B's calls at 15:07:55-15:08:04Z: the launch answered 200 with the game **paused** (as B read: `plugins/games.py:3711`);
`native-stream-start` (sent 15:08:03.748Z) answered **503 "audio codec opus is required by this host
(PRIVYHUB_AUDIO_CODEC) and the client did not declare it in session/setup"**; `native-stream-ready` (15:08:03.786Z)
answered **503 "Native stream is not active; gameplay remains paused."** B's sketch (B106) did not take the adopted
line 8 into account: it was read from the code of the games plugin and the recovery monitor, not from a run.

What the code says (no file edited; nothing called but the reads below and the calls in `answers.md`):

1. **The stream start is gated by adopted line 8** (`PRIVYHUB_AUDIO_CODEC=opus`, G-A2): `native_stream.py:1690` —
   `AUDIO_CODEC.prepare(…, client_ip)` refuses before anything is spawned unless **the stream's target host declared
   `opus`** (`audio_codec.py:358-374`, "fails closed"). The target is the caller's address: loopback.
2. **The only way a host declares opus is a successful `/session/setup`** (`audio_codec.py:313-331`, wrapped onto the
   adopted session identity's gate at `privyhub_service.py:1861`): the declared host is the body's `media_host` (and
   `overlay_host`). **`/session/setup` needs a nonce and an HMAC signature with a paired device's key**
   (`session_identity.py:705`, "bad-signature" otherwise) and **refuses a loopback `media_host`**
   (`session_identity.py:712`). A loopback caller with no client therefore cannot declare opus for the loopback address; doing it
   would mean signing as the user's paired onn with its stored key and pointing the media at a real address — that is
   the adopted identity (line 7) and the user's own credential, which the task forbids touching.
3. **Without the stream the pause cannot be released**: `native-stream-ready` releases it only when the stream is
   active (`plugins/games.py:4250-4254`); the games plugin has no other resume route for a game session (no `resume`
   / `pause` action; `recovery-resume` is the recovery's).
4. **And without the stream the watcher cannot start**: `h7-start` refuses "the stream is not up"
   (`h7_minigame.py:219-220`) — confirmed once at 15:08:47Z (400, before any load or keep folder).

**So no loopback call with no client brings the game to running and unpaused with the stream up, under the eighteen
adopted lines, without touching the adopted identity or the user's pairing key.** Per the handoff's change 3: part 1
NOT MET with this reason, and the close. Ways forward are B's (not done here): a watcher-only mode that does not need
the stream (B's own "What I would change" 5), or a bench-only way to start the stream to nobody that does not involve
the client's identity (e.g. a loopback exemption in the audio gate behind the bench flag), each hashed and tested
first.
