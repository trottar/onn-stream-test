1. Session B done, G3-S2 (client side), baseline 3107fb5. Nothing adopted, committed or installed. No adb, no onn; the companion was never restarted.
2. Client: identity/ (SessionProtocol, IdentitySession, AndroidIdentity) behind the setting identity_v2, default off. Off = today's requests, byte for byte (WireRequestTest).
3. Device secret: 32 bytes, app-private, never logged. It is sent once, at pairing (G3-S1's hub holds the HMAC key). The device id is assigned by the hub.
4. Settings: "Pair with hub…" (code + name; "Re-pair (new key)" replaces the secret). On the hub: curl -s -X POST http://localhost:8765/session/pairing/open.
5. Setup: nonce + HMAC input byte for byte G3-S1's vectors; media_host (route's local end), video_port signed, audio_port declared; token on games/tv calls; refresh at 10 min; one retry; reason shown.
6. Tests: 30/30 client unit tests (19 new; vectors made by G3-S1's own sign() and gate). Handshake harness against G3-S1's host 18/18 (run 1 17/18: a harness-ordering slip, disclosed).
7. Debug APK 77011eef…7d9d, 9,808,513 bytes, built offline, NOT installed. The CONFIRMED build output de072762… is preserved in PrivyHub/app/build/g3_s2_preserved/.
8. Release APK not built: lint-gradle 32.3.2 is not cached offline; the user skipped it ("the debug APK is the one CL-B2 installs").
9. Next, CL-B2: after the watch, install 77011eef…; update the pinned hashes (c3_l4_nft_night.py + its test, e1_suite.py EXPECT_APK); pair by hand; the live G3 smoke on the LAN.
10. Records: evidence/G3_S2_…_2026-10-16.md + g3_s2_2026-10-16/, patches/G3-S2_…, REMOTE_TRUST §6, ROADMAP §G3; logs/g3_s2_git_status.txt. The watch read inactive at B's end (not touched by B).
