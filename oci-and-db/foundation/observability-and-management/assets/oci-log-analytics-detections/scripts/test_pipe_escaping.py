#!/usr/bin/env python3
"""Regression tests for Windows named-pipe backslash escaping in convert_sigma.

Context
-------
Windows named-pipe detections (Cobalt Strike / Mimikatz / PsExec / generic C2)
express pipe patterns with literal backslashes, e.g. ``\\MSSE-`` or ``\\PSEXESVC``.
OCI Log Analytics interprets ``\\r``/``\\n``/``\\t`` as escape sequences inside a
string literal, so a single literal backslash must be emitted DOUBLED (``\\\\``) to
survive the parser. A prior bug emitted the backslashes unescaped, which produced
unparseable LAQL on every regeneration and silently overwrote curated pipe queries.

These tests pin that the converter:
  * doubles literal backslashes for every field modifier (startswith/contains/
    endswith) AND for exact pipe-name matches (which become wildcard LIKE);
  * regenerates each real ``rules/windows/pipe_created/*.yaml`` into LAQL that
    passes the converter's own structural validator with zero issues;
  * never leaves an odd-length backslash run (the signature of a half-escaped
    literal that the live parser rejects);
  * honors ``do_not_overwrite`` so a curated pipe query is never clobbered.

No external dependencies — stdlib unittest only.
"""

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml  # noqa: E402

from convert_sigma import (  # noqa: E402
    convert_rule,
    load_config,
    parse_selection,
    query_syntax_issues,
    should_skip_existing_output,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPE_RULES_DIR = REPO_ROOT / 'rules' / 'windows' / 'pipe_created'

# A maximal run of backslashes that has ODD length is the fingerprint of a
# half-escaped literal (e.g. a stray single ``\``). Every literal backslash the
# converter emits must be doubled, so every run must be even-length.
_ODD_BACKSLASH_RUN = re.compile(r'(?<!\\)\\(?:\\\\)*(?!\\)')


def _has_unescaped_backslash(text):
    """True if any maximal backslash run in ``text`` has odd length."""
    return bool(_ODD_BACKSLASH_RUN.search(text))


class TestPipeModifierEscaping(unittest.TestCase):
    """Field modifiers on pipe-name selectors must double literal backslashes."""

    field_map = {'PipeName': "'Pipe Name'"}

    def test_startswith_backslash_is_doubled(self):
        # Cobalt Strike sel_cs_default: PipeName|startswith: \MSSE-
        result = parse_selection(
            {'PipeName|startswith': [r'\MSSE-', r'\postex_']}, self.field_map
        )
        self.assertIn(r"'Pipe Name' like '\\MSSE-*'", result)
        self.assertIn(r"'Pipe Name' like '\\postex_*'", result)
        self.assertFalse(_has_unescaped_backslash(result))

    def test_contains_backslash_is_doubled(self):
        # PsExec sel_psexec: PipeName|contains: \PSEXESVC
        result = parse_selection(
            {'PipeName|contains': [r'\PSEXESVC', r'\PAExec']}, self.field_map
        )
        self.assertIn(r"'Pipe Name' like '*\\PSEXESVC*'", result)
        self.assertIn(r"'Pipe Name' like '*\\PAExec*'", result)
        self.assertFalse(_has_unescaped_backslash(result))

    def test_endswith_backslash_is_doubled(self):
        result = parse_selection({'PipeName|endswith': r'\beacon'}, self.field_map)
        self.assertIn(r"'Pipe Name' like '*\\beacon'", result)
        self.assertFalse(_has_unescaped_backslash(result))

    def test_exact_pipe_match_becomes_escaped_wildcard(self):
        # Mimikatz sel_known_pipes: exact PipeName list -> wildcard LIKE, not '='
        result = parse_selection(
            {'PipeName': [r'\HID_CTRL', r'\Win32Pipes.']}, self.field_map
        )
        self.assertIn(r"'Pipe Name' like '*\\HID_CTRL*'", result)
        self.assertIn(r"'Pipe Name' like '*\\Win32Pipes.*'", result)
        self.assertNotIn(r"'Pipe Name' = '\HID_CTRL'", result)
        self.assertFalse(_has_unescaped_backslash(result))


class TestRealPipeRulesRegenerateCleanly(unittest.TestCase):
    """Every shipped pipe rule must regenerate into validator-clean LAQL."""

    @classmethod
    def setUpClass(cls):
        cls.field_map, cls.logsource_map = load_config()
        cls.rule_paths = sorted(PIPE_RULES_DIR.glob('*.yaml'))

    def test_pipe_rules_exist(self):
        # Guard against the directory being moved/renamed out from under the test.
        self.assertGreaterEqual(len(self.rule_paths), 4)

    def test_each_pipe_rule_has_no_syntax_issues(self):
        for rule_path in self.rule_paths:
            with self.subTest(rule=rule_path.name):
                result = convert_rule(str(rule_path), self.field_map, self.logsource_map)
                self.assertIsNotNone(result)
                query = result['query']
                self.assertEqual(
                    query_syntax_issues(query), [],
                    f"{rule_path.name} produced issues: {query}",
                )

    def test_each_pipe_rule_has_no_half_escaped_backslash(self):
        for rule_path in self.rule_paths:
            with self.subTest(rule=rule_path.name):
                result = convert_rule(str(rule_path), self.field_map, self.logsource_map)
                query = result['query']
                self.assertFalse(
                    _has_unescaped_backslash(query),
                    f"{rule_path.name} left an odd backslash run: {query}",
                )

    def test_pipe_rules_emit_pipe_name_like_clauses(self):
        # Sanity: the rules really do exercise the Pipe Name path (so the
        # escaping above is actually load-bearing, not vacuously passing).
        for rule_path in self.rule_paths:
            with self.subTest(rule=rule_path.name):
                result = convert_rule(str(rule_path), self.field_map, self.logsource_map)
                self.assertIn("'Pipe Name' like", result['query'])


class TestDoNotOverwriteProtectsCuratedPipeQuery(unittest.TestCase):
    """A curated pipe query flagged do_not_overwrite must survive regeneration."""

    def test_skip_when_existing_json_flags_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, 'curated_pipe.json')
            with open(out_path, 'w') as fh:
                fh.write('{"query": "curated", "do_not_overwrite": true}')
            # Even though the freshly-converted result omits the flag, the
            # on-disk curated query opts out and must be preserved.
            result = {'query': "('Log Source' = 'x')", 'sigma_id': 'abc'}
            self.assertTrue(should_skip_existing_output(result, out_path))

    def test_skip_when_rule_source_flags_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, 'curated_pipe.json')
            with open(out_path, 'w') as fh:
                fh.write('{"query": "anything"}')
            result = {'query': 'x', 'do_not_overwrite': True}
            self.assertTrue(should_skip_existing_output(result, out_path))

    def test_no_skip_for_normal_pipe_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, 'normal_pipe.json')
            with open(out_path, 'w') as fh:
                fh.write('{"query": "x"}')
            result = {'query': 'x'}
            self.assertFalse(should_skip_existing_output(result, out_path))


if __name__ == '__main__':
    unittest.main()
