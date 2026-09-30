#!/usr/bin/env python3
"""C3-L4-L2B: unit tests for the nft night harness's allow-list, listing parser and fake sudo.

    python3 -m unittest tools/test_c3_l4_nft_night.py -v

Nothing here runs `sudo` or `nft`. The allow-list tests build every command of
the L1 record's section 7 and check that anything else is refused before it
could reach sudo. The listing tests feed the parser nft-format text and the
fake sudo's own output (tools/c3_l4_fake_sudo.py, in a temp dir).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import c3_l4_nft_night as h  # noqa: E402

FAKE = HERE / "c3_l4_fake_sudo.py"
SECTION7 = {
    "add_table": "nft add table inet privyhub_fault",
    "add_chain": "nft add chain inet privyhub_fault flt { type filter hook output priority 0; }",
    "counter_rule": "nft add rule inet privyhub_fault flt udp dport 48100 counter",
    "cap_rule": "nft add rule inet privyhub_fault flt udp dport 48100 limit rate over 869 kbytes/second "
                "burst 64 kbytes counter drop",
    "loss_rule": "nft add rule inet privyhub_fault flt udp dport 48100 numgen random mod 1000 < 20 counter drop",
    "drop_rule": "nft add rule inet privyhub_fault flt udp dport { 48100, 48101 } counter drop",
    "list_table": "nft list table inet privyhub_fault",
    "list_tables": "nft list tables",
    "flush_chain": "nft flush chain inet privyhub_fault flt",
    "delete_table": "nft delete table inet privyhub_fault",
}


class AllowListBuilds(unittest.TestCase):
    def test_every_section7_command_builds_and_checks(self):
        self.assertEqual(set(SECTION7), set(h.NFT_ALLOW))
        for name, text in SECTION7.items():
            argv = h.nft_argv(name, 869 if name == "cap_rule" else None)
            self.assertEqual(" ".join(argv), text, name)
            self.assertEqual(h.nft_check(argv), name)
            self.assertEqual(argv[0], "nft")

    def test_no_shell_metacharacters_reach_argv_as_one_string(self):
        # argument lists, no shell: the set and the chain spec are single argv entries, nothing else has spaces
        for name in h.NFT_ALLOW:
            argv = h.nft_argv(name, 869 if name == "cap_rule" else None)
            spaced = [a for a in argv if " " in a]
            self.assertTrue(set(spaced) <= {"{ type filter hook output priority 0; }", "{ 48100, 48101 }"}, argv)
            self.assertFalse(any(c in a for a in argv for c in ";|&`$>\n" if a not in spaced), argv)

    def test_cap_bounds(self):
        for cap in (200, 869, 1444, 2000):
            h.nft_argv("cap_rule", cap)
        for cap in (None, 0, 199, 2001, 869.0, "869", True, -5):
            with self.assertRaises(h.NftRefused, msg=repr(cap)):
                h.nft_argv("cap_rule", cap)
        with self.assertRaises(h.NftRefused):
            h.nft_argv("counter_rule", 869)


class AllowListRefuses(unittest.TestCase):
    def refused(self, text_or_argv):
        argv = text_or_argv.split(" ") if isinstance(text_or_argv, str) else text_or_argv
        with self.assertRaises(h.NftRefused, msg=repr(argv)):
            h.nft_check(argv)

    def test_unknown_names(self):
        for name in ("add_rule", "delete_rule", "flush_ruleset", "list_ruleset", "", "cap"):
            with self.assertRaises(h.NftRefused):
                h.nft_argv(name)

    def test_another_table(self):
        for name in h.NFT_ALLOW:
            argv = h.nft_argv(name, 869 if name == "cap_rule" else None)
            if "privyhub_fault" in argv:
                self.refused([a.replace("privyhub_fault", "filter") for a in argv])
                self.refused([a.replace("inet", "ip") for a in argv])

    def test_another_port(self):
        for name in ("counter_rule", "cap_rule", "loss_rule", "drop_rule"):
            argv = h.nft_argv(name, 869 if name == "cap_rule" else None)
            self.refused([a.replace("48100", "22") for a in argv])
            self.refused([a.replace("48100", "48102") for a in argv])
        self.refused(h.nft_argv("drop_rule")[:-3] + ["{ 48100, 22 }", "counter", "drop"])

    def test_another_binary(self):
        for binary in ("iptables", "/usr/sbin/nft", "bash", "sh", "tc", "nft;"):
            argv = h.nft_argv("delete_table")
            self.refused([binary] + argv[1:])

    def test_other_nft_verbs_and_shapes(self):
        for text in ("nft flush ruleset", "nft list ruleset", "nft -f /tmp/x",
                     "nft delete table inet privyhub_fault extra",
                     "nft add table inet privyhub_fault ; rm -rf ~",
                     "nft insert rule inet privyhub_fault flt udp dport 48100 counter drop",
                     "nft add rule inet privyhub_fault flt udp dport 48100 drop",
                     "nft add rule inet privyhub_fault flt udp dport 48100 numgen random mod 1000 < 200 counter drop",
                     "nft add chain inet privyhub_fault flt { type filter hook input priority 0; }"):
            self.refused(text)
        self.refused(["nft", "add", "chain", "inet", "privyhub_fault", "flt",
                      "{ type filter hook output priority 0; }", "extra"])
        self.refused([])
        # the placeholder itself is not a cap
        self.refused([t for t in h.NFT_ALLOW["cap_rule"]])

    def test_cap_token_shapes(self):
        base = h.nft_argv("cap_rule", 869)
        i = base.index("869")
        for tok in ("8690", "199", "2001", "869.5", "-869", "８６９", "869 ", "0x365", ""):
            self.refused(base[:i] + [tok] + base[i + 1:])


LISTING = """table inet privyhub_fault {
\tchain flt {
\t\ttype filter hook output priority filter; policy accept;
\t\tudp dport 48100 limit rate over 869 kbytes/second burst 64 kbytes counter packets 12 bytes 14400 drop
\t}
}
"""


class ListingParser(unittest.TestCase):
    def test_rules_and_patterns(self):
        self.assertEqual(h.table_rules(LISTING), [
            "udp dport 48100 limit rate over 869 kbytes/second burst 64 kbytes counter packets 12 bytes 14400 drop"])
        self.assertTrue(h.rule_pattern("cap_rule", 869).match(h.table_rules(LISTING)[0]))
        self.assertFalse(h.rule_pattern("cap_rule", 870).match(h.table_rules(LISTING)[0]))
        self.assertFalse(h.rule_pattern("loss_rule").match(h.table_rules(LISTING)[0]))

    def test_absent_and_empty(self):
        self.assertIsNone(h.table_rules(""))
        self.assertIsNone(h.table_rules("table inet filter {\n}\n"))
        self.assertIsNone(h.table_rules("Error: No such file or directory"))
        empty = "table inet privyhub_fault {\n\tchain flt {\n\t\ttype filter hook output priority filter; policy accept;\n\t}\n}\n"
        self.assertEqual(h.table_rules(empty), [])

    def test_set_rule_and_mbytes(self):
        text = LISTING.replace(
            "udp dport 48100 limit rate over 869 kbytes/second burst 64 kbytes counter packets 12 bytes 14400 drop",
            "udp dport { 48100, 48101 } counter packets 3 bytes 3600 drop")
        rules = h.table_rules(text)
        self.assertEqual(len(rules), 1)
        self.assertTrue(h.rule_pattern("drop_rule").match(rules[0]))
        self.assertTrue(h.rule_pattern("cap_rule", 1024).match(
            "udp dport 48100 limit rate over 1 mbytes/second burst 64 kbytes counter packets 1 bytes 2 drop"))

    def test_sudo_refused(self):
        self.assertTrue(h.sudo_refused("sudo: a password is required\n"))
        self.assertTrue(h.sudo_refused("sudo: a terminal is required to read the password"))
        self.assertFalse(h.sudo_refused("Error: Could not process rule: No such file or directory"))
        self.assertFalse(h.sudo_refused(""))


class FakeSudo(unittest.TestCase):
    """The shim the forced-abort runs use; its listings must parse like nft's."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, FAKE_SUDO_DIR=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def sudo(self, *args):
        r = subprocess.run([sys.executable, str(FAKE), *args], capture_output=True, text=True, env=self.env)
        return r.returncode, r.stdout + r.stderr

    def nft(self, name, cap=None):
        return self.sudo("-n", *h.nft_argv(name, cap))

    def test_every_recipe_verifies(self):
        for rule, cap in (("counter_rule", None), ("cap_rule", 869), ("loss_rule", None), ("drop_rule", None)):
            for n in ("add_table", "add_chain"):
                self.assertEqual(self.nft(n)[0], 0)
            self.assertEqual(self.nft(rule, cap)[0], 0)
            rc, out = self.nft("list_table")
            self.assertEqual(rc, 0)
            rules = h.table_rules(out)
            self.assertEqual(len(rules), 1, out)
            self.assertTrue(h.rule_pattern(rule, cap).match(rules[0]), rules)
            self.assertIn("privyhub_fault", self.nft("list_tables")[1])
            self.assertEqual(self.nft("delete_table")[0], 0)
            rc, out = self.nft("list_tables")
            self.assertEqual(rc, 0)
            self.assertNotIn("privyhub_fault", out)

    def test_flush_then_new_rule(self):
        for n, c in (("add_table", None), ("add_chain", None), ("counter_rule", None),
                     ("flush_chain", None), ("cap_rule", 900)):
            self.assertEqual(self.nft(n, c)[0], 0)
        rules = h.table_rules(self.nft("list_table")[1])
        self.assertEqual(len(rules), 1)
        self.assertTrue(h.rule_pattern("cap_rule", 900).match(rules[0]))

    def test_delete_absent_is_an_nft_error_not_a_sudo_refusal(self):
        rc, out = self.nft("delete_table")
        self.assertEqual(rc, 1)
        self.assertFalse(h.sudo_refused(out))
        self.assertIsNone(h.table_rules(self.nft("list_table")[1]))

    def test_deny_and_password(self):
        Path(self.tmp.name, "deny").touch()
        rc, out = self.sudo("-n", "-v")
        self.assertEqual(rc, 1)
        self.assertTrue(h.sudo_refused(out))
        rc, out = self.nft("list_tables")
        self.assertTrue(h.sudo_refused(out))
        self.assertEqual(self.sudo("-v")[0], 0)
        self.assertEqual(self.sudo("-n", "-v")[0], 0)

    def test_shim_refuses_non_nft(self):
        self.assertEqual(self.sudo("-n", "bash", "-c", "true")[0], 2)
        self.assertEqual(self.sudo("nft", "list", "tables")[0], 2)
        argv = [json.loads(l)["argv"] for l in Path(self.tmp.name, "argv.jsonl").read_text().splitlines()]
        self.assertEqual(argv[-1], ["nft", "list", "tables"])


if __name__ == "__main__":
    unittest.main()
