import os

import pytest

from core import glossary


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_OCI_INTEGRATION_TESTS") != "1",
    reason="Set RUN_OCI_INTEGRATION_TESTS=1 to call OCI Object Storage",
)


def test_downloads_glossary_from_oci_bucket():
    glossary._glossary = {}
    glossary._last_refresh_at = 0.0

    glossary.refresh_glossary(force=True)

    english_to_spanish = glossary.get_glossary_for_pair("english", "spanish-mx")
    assert english_to_spanish["jackpot"] == "bote"
