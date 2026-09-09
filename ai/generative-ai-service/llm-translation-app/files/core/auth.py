import logging
import os

from oci.signer import Signer

from core.config import OCI_CONFIG_FILE, OCI_CONFIG_PROFILE

logger = logging.getLogger(__name__)

_cached_signer: Signer | None = None
_cached_config: dict | None = None
_using_resource_principal: bool = False

# Set OCI_AUTH=api_key to skip Resource Principal and use config file directly.
_auth_mode = os.environ.get("OCI_AUTH", "auto").lower()


def get_signer() -> Signer:
    """Return an OCI Signer, trying Resource Principal first, then config file."""
    global _cached_signer, _cached_config, _using_resource_principal
    if _cached_signer is not None:
        return _cached_signer

    # Try Resource Principal (OCI Functions / OCI Container Instances)
    if _auth_mode != "api_key":
        try:
            from oci.auth.signers import get_resource_principals_signer

            _cached_signer = get_resource_principals_signer()
            _using_resource_principal = True
            logger.info("Using Resource Principal authentication")
            return _cached_signer
        except Exception:
            pass

    # Fall back to config file
    from oci.config import from_file

    _cached_config = from_file(OCI_CONFIG_FILE, OCI_CONFIG_PROFILE)
    _cached_signer = Signer(
        tenancy=_cached_config["tenancy"],
        user=_cached_config["user"],
        fingerprint=_cached_config["fingerprint"],
        private_key_file_location=_cached_config["key_file"],
        pass_phrase=_cached_config.get("pass_phrase"),
    )
    logger.info("Using config-file authentication (%s)", OCI_CONFIG_FILE)
    return _cached_signer


def get_oci_config() -> dict:
    """Return the OCI config dict. Call get_signer() first to populate it."""
    if _cached_config is None and not _using_resource_principal:
        get_signer()  # populate cache
    return _cached_config or {}
