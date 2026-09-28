#!/usr/bin/env python3
"""C6-D1: unit tests for the native source contract module.

    python3 -m unittest tools/test_native_source_contract.py -v

The module is interfaces only and imported by nothing in production; these
tests instantiate the games source DESCRIPTION (not a running source).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "companion"))

import native_source_contract as c  # noqa: E402


class ContractTests(unittest.TestCase):

    def test_does_not_drag_production_in(self):
        """Rule: importing the contract never loads native_stream (the games source)."""
        # In a fresh interpreter, so other test modules in the same run
        # (which may import native_stream themselves) cannot mask the result.
        import subprocess
        code = ("import sys; sys.path.insert(0, %r); import native_source_contract; "
                "print('native_stream' in sys.modules)" % str(Path(c.__file__).resolve().parent))
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.strip(), "False")
        src = Path(c.__file__).read_text()
        self.assertNotIn("import native_stream\n", src)
        self.assertNotIn("from native_stream ", src)

    def test_nothing_in_production_imports_the_contract(self):
        """Rule: no companion module imports native_source_contract (C6-D1 scope)."""
        root = Path(c.__file__).resolve().parent
        users = [p for p in root.rglob("*.py")
                 if p.name != "native_source_contract.py"
                 and "native_source_contract" in p.read_text(errors="replace")]
        self.assertEqual(users, [])

    def test_games_description_validates(self):
        """Rule: the games source, described from its own constants, conforms."""
        d = c.GamesSourceDescription()
        self.assertEqual(d.validate(), [])
        self.assertEqual(d.actuator_class, c.ActuatorClass.VIDEO_ONLY_RESTART)
        self.assertEqual(d.reference_bitrate_kbps, 7000)
        self.assertEqual(d.validated_bitrates_kbps, (5000, 5500, 6000, 7000))
        self.assertEqual(d.fec_schemes[0].wire_version, 1)
        self.assertEqual(d.fec_schemes[0].group_size, 8)
        self.assertTrue(d.diagnostics_identity_free)

    def test_description_reads_constants_not_copies(self):
        """Rule: the description follows the profile module (no duplicated constants)."""
        import native_stream_profiles as p
        d = c.GamesSourceDescription()
        self.assertEqual(d.supported_profiles, (p.NATIVE_GAME_720P60_REFERENCE.id,))
        self.assertEqual(d.reference_bitrate_kbps, p.NATIVE_GAME_720P60_REFERENCE.bitrate_kbps)

    def test_validation_catches_violations(self):
        """Rule: duplicate wire versions, an address-bearing diagnostics surface, and an
        actuator without a validated ladder are each rejected."""
        good = c.GamesSourceDescription()
        from dataclasses import replace
        dup = replace(good, fec_schemes=good.fec_schemes * 2)
        self.assertTrue(any("unique" in m for m in dup.validate()))
        ident = replace(good, diagnostics_identity_free=False)
        self.assertTrue(any("D114" in m for m in ident.validate()))
        noladder = replace(good, validated_bitrates_kbps=())
        self.assertTrue(noladder.validate())

    def test_profile_satisfies_protocol(self):
        """Rule: today's profile object satisfies the SourceProfile protocol."""
        import native_stream_profiles as p
        self.assertIsInstance(p.NATIVE_GAME_720P60_REFERENCE, c.SourceProfile)

    def test_lifecycle_states(self):
        """Rule: the shared lifecycle carries the states every source needs."""
        names = {s.value for s in c.SourceLifecycle}
        for s in ("IDLE", "STARTING", "READY", "PLAYING", "PAUSED", "RECOVERING", "STOPPING", "FAILED"):
            self.assertIn(s, names)


if __name__ == "__main__":
    unittest.main()
