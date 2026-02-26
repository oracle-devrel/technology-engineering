"""
Test usage API 02
"""

import json
from consumption_utils import (
    usage_summary_by_service_structured,
    usage_summary_by_compartment_structured,
)


# --- Esempio d'uso standalone (per test locale) ---
if __name__ == "__main__":
    result = usage_summary_by_service_structured(
        start_day="2025-09-01",
        end_day_inclusive="2025-09-30",
        query_type="COST",
    )

    print(json.dumps(result, indent=2))
