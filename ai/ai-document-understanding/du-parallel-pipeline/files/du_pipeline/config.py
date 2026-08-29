import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Connection settings for the OCI Document Understanding client.

    The compartment OCID is never hardcoded: it comes from the
    OCI_COMPARTMENT_ID environment variable or the --compartment-id flag.
    """

    compartment_id: str
    config_file: str = "~/.oci/config"
    profile: str = "DEFAULT"

    @classmethod
    def from_env(cls, compartment_id=None, config_file=None, profile=None):
        compartment_id = compartment_id or os.environ.get("OCI_COMPARTMENT_ID")
        if not compartment_id:
            raise SystemExit(
                "No compartment OCID given. Set the OCI_COMPARTMENT_ID environment "
                "variable or pass --compartment-id."
            )
        return cls(
            compartment_id=compartment_id,
            config_file=config_file or os.environ.get("OCI_CONFIG_FILE", "~/.oci/config"),
            profile=profile or os.environ.get("OCI_CONFIG_PROFILE", "DEFAULT"),
        )
