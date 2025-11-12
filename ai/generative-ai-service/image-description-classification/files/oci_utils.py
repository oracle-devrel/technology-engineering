"""Small utilities to handle OCI related functionality."""

import oci
from datetime import datetime, timezone


def get_tenancy_id():
    """Returns the tenancy ID."""
    config = oci.config.from_file()
    return config["tenancy"]


def list_subscribed_regions():
    """List all subscribed regions for the default tenancy."""
    config = oci.config.from_file()
    identity_client = oci.identity.IdentityClient(config)
    return sorted(
        r.region_name
        for r in identity_client.list_region_subscriptions(config["tenancy"]).data
    )


def list_genai_models(compartment_ocid: str, region: str):
    """List all available Generative AI models that are active and not deprecated."""
    config = oci.config.from_file()
    config["region"] = region
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
