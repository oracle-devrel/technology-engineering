import oci
from datetime import datetime, timezone
from pydantic.dataclasses import dataclass


@dataclass
class AppContext:
    config: dict


def list_models(compartment_ocid: str) -> [str]:
    """List all available Generative AI models that are active and not deprecated."""
    config = oci.config.from_file()
    genai_client = oci.generative_ai.GenerativeAiClient(config)
    models = genai_client.list_models(
        compartment_ocid,
        lifecycle_state="ACTIVE",
    ).data.items
    result = set()
    for model in models:
        if model.capabilities != ["CHAT"]:
            continue
        if cutoff := model.time_deprecated:
            if datetime.now(timezone.utc) > cutoff:
                continue
        result.add(model.display_name)
    return sorted(result)
