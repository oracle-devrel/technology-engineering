// Customer-owned One-OE source configuration.
//
// Replace every customer token below before generating the reviewed JSON files.
// Add further environments here later; the same protected foundation state
// makes those additions normal, repeatable Landing Zone changes.
{
  notification_email: '__NOTIFICATION_EMAIL__',
  // Set this to the OCI-assigned OP03 Bastion endpoint plus /32. Keep it null
  // until the Bastion exists so no non-authoritative example rule is emitted.
  platform_bastion_private_endpoint_cidr: null,
  // OP01 uses this list to render security and observability controls. During
  // initial installation OP01 remains in its core stage until DEV OP02 exists.
  // Add later environments here only after their OP02 state exists.
  activated_environments: ['dev'],
  blueprint: {
    region: '__OCI_REGION__',
    region_short_name: '__OCI_REGION_KEY__',
    realm: 'oc1',
    cis_level: 1,

    // Hub E is the low-cost, no-firewall One-OE topology.
    hub: {
      kind: 'hub_e',
      network: { vcn: '__HUB_VCN_CIDR__' },
    },

    environments: {
      dev: {
        shared_project_network: {
          network: { vcn: '__DEV_VCN_CIDR__' },
        },
      },
    },
  },
}
