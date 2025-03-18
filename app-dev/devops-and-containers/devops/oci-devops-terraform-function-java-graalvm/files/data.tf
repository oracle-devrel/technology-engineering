data "oci_objectstorage_namespace" "tenancy_namespace" {
    compartment_id = oci_artifacts_container_configuration.export_container_configuration.id
}
