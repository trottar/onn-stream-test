#!/usr/bin/env python3
"""B223: bench's expected numbers for a score ending come from the regions' label record on a surveyed title, never
from the old label.json; a title without a survey reads the old record, as before. No hub, no title, no picture."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))


class BenchNumbers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["PRIVYHUB_ADD_GAME_HOME"] = self.tmp.name
        import party_add_game as t
        self.t = t
        self.home = Path(self.tmp.name) / "T01"
        self.home.mkdir(parents=True)

    def tearDown(self):
        os.environ.pop("PRIVYHUB_ADD_GAME_HOME", None)
        self.tmp.cleanup()

    def write(self, name, saves):
        (self.home / name).write_text(json.dumps({"saves": {r: {"readings": [v, v], "sha": "x"}
                                                            for r, v in saves.items()}}))

    def test_surveyed_reads_the_regions_record(self):
        b = {"survey": {"kind": "score"}}
        self.write("regions_label.json", {"end_P1": "02-00", "end_P1_3": "03-01", "end_P2_3": "05-06"})
        self.assertEqual(self.t._bench_numbers("T01", b, "end_P1_3"), [3, 1])
        self.assertEqual(self.t._bench_numbers("T01", b, "end_P2_3"), [5, 6])
        self.assertEqual(self.t._bench_numbers("T01", b, "end_P1"), [2, 0])

    def test_surveyed_never_reads_a_stale_old_record(self):
        b = {"survey": {"kind": "score"}}
        self.write("label.json", {"end_P1": "09-08"})                    # the old path's record, stale
        self.write("regions_label.json", {"end_P1": "02-00", "end_P1_3": "03-01"})
        self.assertEqual(self.t._bench_numbers("T01", b, "end_P1"), [2, 0])
        self.assertEqual(self.t._bench_numbers("T01", b, "end_P1_3"), [3, 1])

    def test_surveyed_no_old_record_at_all(self):
        b = {"survey": {"kind": "score"}}
        self.write("regions_label.json", {"end_P2": "02-03"})
        self.assertEqual(self.t._bench_numbers("T01", b, "end_P2"), [2, 3])

    def test_no_reading_is_none_not_an_error(self):
        b = {"survey": {"kind": "score"}}
        self.write("regions_label.json", {"end_P1": "02-00"})
        self.assertIsNone(self.t._bench_numbers("T01", b, "end_P2"))
        self.write("regions_label.json", {"end_P1": "WO/W"})
        self.assertIsNone(self.t._bench_numbers("T01", b, "end_P1"))

    def test_without_a_survey_the_old_record_as_before(self):
        self.write("label.json", {"end_P1": "16-14"})
        self.write("regions_label.json", {"end_P1": "02-00"})
        self.assertEqual(self.t._bench_numbers("T01", {}, "end_P1"), self.t._numbers("T01", "end_P1"))
        self.assertEqual([int(x) for x in self.t._bench_numbers("T01", {}, "end_P1")], [16, 14])
        self.assertIsNone(self.t._bench_numbers("T01", {}, "end_P2"))


if __name__ == "__main__":
    unittest.main()
