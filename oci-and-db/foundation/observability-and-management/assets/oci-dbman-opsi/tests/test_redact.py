from dbman_opsi.redact import redact_data, redact_text


def test_redacts_oci_topology_and_secret_shapes() -> None:
    compartment_ocid = "ocid1" + ".compartment.oc1..aaaaaaaaexample"
    namespace = "fr4" + "zqfimuxtr"
    internal_key = "isk_" + ("a" * 40)
    public_ip = "130" + ".61.1.2"
    private_ip = "10" + ".42.3.4"
    text = (
        f"{compartment_ocid} {public_ip} {private_ip} "
        f"{namespace} e3:9e:1e:ed:aa:bb:cc:dd:ee:ff:00:11:22:33:44:55 "
        f"{internal_key}"
    )

    redacted = redact_text(text)

    assert "ocid1" + "." not in redacted
    assert public_ip not in redacted
    assert private_ip not in redacted
    assert namespace not in redacted
    assert "isk_" not in redacted


def test_redacts_nested_data_without_mutating_shape() -> None:
    data = {"items": ["ocid1" + ".database.oc1..aaaaaaaaexample"], "ok": True}

    assert redact_data(data) == {"items": ["<OCI_OCID>"], "ok": True}


def test_redacts_data_safe_and_pluggable_database_ocids() -> None:
    ds_target = "ocid1" + ".datasafetargetdatabase.oc1.eu-frankfurt-1.aaaaexample"
    ds_pe = "ocid1" + ".datasafeprivateendpoint.oc1.eu-frankfurt-1.bbbbexample"
    pdb = "ocid1" + ".pluggabledatabase.oc1.eu-frankfurt-1.ccccexample"
    insight = "ocid1" + ".databaseinsight.oc1.eu-frankfurt-1.ddddexample"

    redacted = redact_text(f"{ds_target} {ds_pe} {pdb} {insight}")

    assert "ocid1" + "." not in redacted
    assert redacted.count("<OCI_OCID>") == 4
