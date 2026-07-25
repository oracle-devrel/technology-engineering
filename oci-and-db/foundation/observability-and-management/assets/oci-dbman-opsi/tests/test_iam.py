from dbman_opsi.config import EnablementConfig
from dbman_opsi.iam import policy_statements


def test_policy_statements_cover_required_services() -> None:
    config = EnablementConfig(profile="DEFAULT", region="eu-frankfurt-1", compartment_id="compartment-id")

    statements = "\n".join(policy_statements(config))

    assert "database-management-family" in statements
    assert "opsi-family" in statements
    assert "management-agents" in statements
    assert "secret-family" in statements
    assert "virtual-network-family" in statements
