"""Offline tests for parse_validate_all_queries (no live OCI calls)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import parse_validate_all_queries as pv  # noqa: E402


class IterQueryFilesTests(unittest.TestCase):
    def test_discovers_runnable_queries_and_excludes_generated(self):
        files = list(pv._iter_query_files())
        names = {f.name for f in files}
        # a representative runnable query is included
        self.assertIn("oci_console_login_failure.json", names)
        # generated/inventory artifacts are excluded
        for generated in ("catalog.json", "manifest.json", "log_source_field_dictionary.json"):
            self.assertNotIn(generated, names, f"{generated} must be excluded")
        # sanity: the corpus is large
        self.assertGreater(len(files), 400)


class AuthFailureExitTests(unittest.TestCase):
    def test_returns_3_when_oci_config_fails(self):
        with mock.patch.object(pv, "require_oci_config", side_effect=RuntimeError("no auth")):
            rc = pv.main([])
        self.assertEqual(rc, 3)


if __name__ == "__main__":
    unittest.main()
