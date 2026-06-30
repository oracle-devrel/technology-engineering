"""Small OCI CLI facade used by discovery, enablement, and validation.

``OciCli`` is composed from per-domain command mixins (network, database, vault,
IAM, infra, Database Management, Ops Insights, Data Safe) so each area lives in
its own focused module while presenting a single flat client to callers. The
public surface — every ``oci.list_*`` / ``oci.get_*`` / ``oci.create_*`` method —
is unchanged; the split is purely file organization. Shared plumbing
(``run_json``/``run``/``_items``/``_data``/``profile_tenancy``) lives in
:class:`dbman_opsi._oci_base._OciBase`, the common base of every mixin.
"""

from __future__ import annotations

from dbman_opsi._oci_database import DatabaseCommands
from dbman_opsi._oci_datasafe import DataSafeCommands
from dbman_opsi._oci_dbmgmt import DatabaseManagementCommands
from dbman_opsi._oci_iam import IamCommands
from dbman_opsi._oci_infra import InfraCommands
from dbman_opsi._oci_network import NetworkCommands
from dbman_opsi._oci_opsi import OpsiCommands
from dbman_opsi._oci_vault import VaultCommands

__all__ = ["OciCli"]


class OciCli(
    NetworkCommands,
    DatabaseCommands,
    VaultCommands,
    IamCommands,
    InfraCommands,
    DatabaseManagementCommands,
    OpsiCommands,
    DataSafeCommands,
):
    """Flat OCI CLI client composed from per-domain command mixins.

    All mixins share :class:`_OciBase`, which the MRO collapses to one entry, so
    ``__init__`` (``profile``, ``region``, ``runner``) runs exactly once.
    """
