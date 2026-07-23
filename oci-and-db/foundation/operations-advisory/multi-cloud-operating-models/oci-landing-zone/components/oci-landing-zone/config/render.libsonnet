// Protected OP00-OP02 projection adapter for OE config mode.
//
// OCI Landing Zone Operating Entities owns the resource definitions. This
// adapter only separates those definitions along the product's established
// state and ownership boundaries.
local lz = import 'landing_zone.libsonnet';
local platforms = import 'platforms.libsonnet';
local render_context = import 'render_context.libsonnet';
local project_catalog = import 'projects.json';

local global_policy_keys = [
  'PCY-AUDITING-ADMIN-KEY',
  'PCY-COST-ADMIN-KEY',
  'PCY-GENERIC-ADMIN-KEY',
  'PCY-IAM-ADMIN-KEY',
  'PCY-SECURITY-ADMIN-KEY',
  'PCY-SERVICES-ADMIN-KEY',
];
local landing_zone_policy_keys = [
  'PCY-LZ-NETWORK-ADMIN-KEY',
  'PCY-LZ-SECURITY-ADMIN-KEY',
];
local base_group_keys = [
  'GRP-AUDITORS-ADMIN-KEY',
  'GRP-COST-ADMIN-KEY',
  'GRP-IAM-ADMIN-KEY',
  'GRP-LZ-NETWORK-ADMIN-KEY',
  'GRP-LZ-SECURITY-ADMIN-KEY',
  'GRP-SECURITY-ADMIN-KEY',
];
local retired_osms_statement =
  'allow service osms to read instances in tenancy';
local bastion_rule_description =
  'EXAMPLE: Allow inbound traffic from the Bastion Service private endpoint IP address';

local selected_policies(policies, keys) =
  policies {
    supplied_policies: {
      [key]: policies.supplied_policies[key]
      for key in keys
    },
  };

local without_retired_osms_statement(policy) =
  policy {
    statements: std.filter(
      function(statement) statement != retired_osms_statement,
      policy.statements,
    ),
  };

local selected_groups(groups, keys) =
  groups {
    groups: {
      [key]: groups.groups[key]
      for key in keys
    },
  };

local with_notification_recipient(document, notification_email) =
  if !std.objectHas(document, 'notifications_configuration') then document
  else document {
    notifications_configuration+: {
      topics: {
        [topic_key]:
          local topic =
            document.notifications_configuration.topics[topic_key];
          topic {
            subscriptions: [
              subscription { values: [notification_email] }
              for subscription in topic.subscriptions
            ],
          }
        for topic_key in
          std.objectFields(document.notifications_configuration.topics)
      },
    },
  };

local environment_category(categories, vcn_key) =
  local matches = [
    categories[key]
    for key in std.objectFields(categories)
    if std.objectHas(categories[key].vcns, vcn_key)
  ];
  assert std.length(matches) == 1 :
    'expected one network category for ' + vcn_key;
  matches[0];

local drg_route_statement_key(distribution_key) =
  std.strReplace(
    std.strReplace(distribution_key, 'DRGRD-', 'DRGRDS-'),
    '-KEY',
    '-ALL-VCNS-KEY',
  );

local render(customer) =
  local raw_config = customer.blueprint;
  local environment_names = std.objectFields(raw_config.environments);
  local unknown_project_environments = [
    environment
    for environment in std.objectFields(project_catalog)
    if !std.member(environment_names, environment) &&
      std.length(project_catalog[environment]) > 0
  ];
  assert std.length(unknown_project_environments) == 0 :
    'projects.json references an undefined environment';
  local config = raw_config {
    environments: {
      [environment]:
        raw_config.environments[environment] {
          projects: {
            [project]: {}
            for project in project_catalog[environment]
          },
        }
      for environment in environment_names
    },
  };
  local project_names(environment) = project_catalog[environment];
  local invalid_projects = std.flattenArrays([
    [
      project
      for project in project_names(environment)
      if std.length(project) > 30 ||
        std.length(std.findSubstr('_', project)) > 0
    ]
    for environment in environment_names
  ]);
  assert std.length(invalid_projects) == 0 :
    'project names must be lowercase DNS labels of at most 30 characters';
  local duplicate_project_environments = [
    environment
    for environment in environment_names
    if std.length(project_names(environment)) !=
      std.length(std.set(project_names(environment)))
  ];
  assert std.length(duplicate_project_environments) == 0 :
    'projects.json must not contain duplicate projects';
  local active = customer.activated_environments;
  assert std.length(active) ==
    std.length(std.setInter(active, environment_names)) :
    'activated_environments must be a unique subset of blueprint environments';
  local active_config = config {
    environments: {
      [name]: config.environments[name]
      for name in active
    },
    security_targets: active,
  };
  local full = lz(config);
  local active_render = lz(active_config);
  local ctx = render_context.from_raw_config(config);
  local n = ctx.n;
  local iam = full.iam;
  local compartments = iam.compartments_configuration.compartments;
  local landing_zone_key = 'CMP-LANDINGZONE-KEY';
  local landing_zone = compartments[landing_zone_key];
  local environment_compartment_keys = [
    n.key_global('CMP', [name])
    for name in environment_names
  ];
  local shared_landing_zone = landing_zone {
    children: {
      [key]: landing_zone.children[key]
      for key in std.objectFields(landing_zone.children)
      if !std.member(environment_compartment_keys, key)
    },
  };

  local categories =
    full.network.network_configuration.network_configuration_categories;
  local hub_vcn_key = n.key('VCN', ['HUB']);
  local shared_category = environment_category(categories, hub_vcn_key);
  local platform_bastion_cidr =
    if std.objectHas(customer, 'platform_bastion_private_endpoint_cidr')
    then customer.platform_bastion_private_endpoint_cidr
    else null;
  assert platform_bastion_cidr == null ||
    (
      std.type(platform_bastion_cidr) == 'string' &&
      std.endsWith(platform_bastion_cidr, '/32')
    ) :
    'platform_bastion_private_endpoint_cidr must be null or an IPv4 /32';
  local with_platform_bastion_endpoint(category, endpoint_cidr) =
    local management_security_list_key = n.key('SL', ['HUB', 'MGMT']);
    local management_security_list =
      category.vcns[hub_vcn_key]
        .security_lists[management_security_list_key];
    local bastion_rules = std.filter(
      function(rule)
        std.objectHas(rule, 'description') &&
        rule.description == bastion_rule_description,
      management_security_list.ingress_rules,
    );
    assert std.length(bastion_rules) == 1 :
      'expected one official Hub management Bastion example rule';
    category {
      vcns+: {
        [hub_vcn_key]+: {
          security_lists+: {
            [management_security_list_key]+: {
              ingress_rules: std.filter(
                function(rule)
                  !std.objectHas(rule, 'description') ||
                  rule.description != bastion_rule_description,
                management_security_list.ingress_rules,
              ) + (
                if endpoint_cidr == null then []
                else [bastion_rules[0] { src: endpoint_cidr }]
              ),
            },
          },
        },
      },
    };
  local drg_key = n.key('DRG', ['HUB']);
  local full_drg =
    shared_category.non_vcn_specific_gateways
      .dynamic_routing_gateways[drg_key];
  local hub_attachment_key = n.key('DRGATT', ['HUB', 'VCN']);
  local shared_drg = full_drg {
    drg_attachments: {
      [hub_attachment_key]: full_drg.drg_attachments[hub_attachment_key],
    },
    drg_route_distributions: {
      [distribution_key]:
        local distribution =
          full_drg.drg_route_distributions[distribution_key];
        distribution {
          statements: {
            [drg_route_statement_key(distribution_key)]: {
              action: 'ACCEPT',
              match_criteria: {
                attachment_type: 'VCN',
                match_type: 'DRG_ATTACHMENT_TYPE',
              },
              priority: 10,
            },
          },
        }
      for distribution_key in
        std.objectFields(full_drg.drg_route_distributions)
    },
  };
  local op01_network = full.network {
    network_configuration+: {
      network_configuration_categories: {
        '0-shared':
          with_platform_bastion_endpoint(
            shared_category,
            platform_bastion_cidr,
          ) {
          non_vcn_specific_gateways+: {
            dynamic_routing_gateways: {
              [drg_key]: shared_drg,
            },
          },
        },
      },
    },
  };

  local op00_policies =
    selected_policies(iam.policies_configuration, global_policy_keys);
  local op00_iam = {
    identity_domains_configuration:
      iam.identity_domains_configuration,
    identity_domain_groups_configuration:
      selected_groups(
        iam.identity_domain_groups_configuration,
        base_group_keys,
      ),
    policies_configuration: op00_policies {
      supplied_policies: op00_policies.supplied_policies {
        'PCY-SERVICES-ADMIN-KEY':
          without_retired_osms_statement(
            op00_policies.supplied_policies['PCY-SERVICES-ADMIN-KEY'],
          ),
      },
    },
  };
  local op01_iam = {
    compartments_configuration:
      iam.compartments_configuration {
        compartments: {
          [landing_zone_key]: shared_landing_zone,
        },
      },
    policies_configuration:
      selected_policies(
        iam.policies_configuration,
        landing_zone_policy_keys,
      ),
  };

  local op02_identity(environment) =
    local environment_key = n.key_global('CMP', [environment]);
    local project_container_key =
      n.key_global('CMP', [environment, 'PROJECTS']);
    local environment_compartment = landing_zone.children[environment_key];
    local original_project_container =
      environment_compartment.children[project_container_key];
    local project_container = {
      [field]: original_project_container[field]
      for field in std.objectFields(original_project_container)
      if field != 'children'
    };
    {
      compartments_configuration: {
        enable_delete: iam.compartments_configuration.enable_delete,
        compartments: {
          [environment_key]:
            environment_compartment {
              parent_id: landing_zone_key,
              children+: {
                [project_container_key]: project_container,
              },
            },
        },
      },
    };

  local op02_network(environment) =
    local vcn_key = n.key('VCN', [environment, 'PROJECTS']);
    local category = environment_category(categories, vcn_key);
    local attachment_key = n.key('DRGATT', [environment, 'PROJ']);
    local attachment = full_drg.drg_attachments[attachment_key];
    {
      network_configuration: {
        network_configuration_categories: {
          [environment]:
            platforms.publication_network_category(
              category,
              n,
              [],
              false,
            ) {
              non_vcn_specific_gateways+: {
                inject_into_existing_drgs+: {
                  [drg_key]+: {
                    drg_id: drg_key,
                    drg_attachments+: {
                      [attachment_key]:
                        attachment {
                          drg_route_table_id:
                            '__DRG_SPOKES_ROUTE_TABLE_OCID__',
                          drg_route_table_key: null,
                        },
                    },
                  },
                },
              },
            },
        },
      },
    };

  local fixed_observability(document) =
    with_notification_recipient(
      document,
      customer.notification_email,
    );

  // OE v3.1.0 creates a child-specific zone for the shared network
  // compartment. That separates its subnets from platform resources, which
  // inherit the parent CIS zone, and OCI rejects those cross-zone
  // associations. Until the upstream generator uses one zone at the common
  // parent, retain the parent CIS zone and omit only the conflicting child
  // target.
  local without_shared_network_security_zone(document) =
    local shared_network_zone_key =
      n.key_global('SZ-TGT', ['SHARED', 'NETWORK']);
    document {
      security_zones_configuration+: {
        security_zones: {
          [key]: document.security_zones_configuration.security_zones[key]
          for key in
            std.objectFields(
              document.security_zones_configuration.security_zones,
            )
          if key != shared_network_zone_key
        },
      },
    };

  local project_identity(environment, project) =
    local environment_key = n.key_global('CMP', [environment]);
    local project_container_key =
      n.key_global('CMP', [environment, 'PROJECTS']);
    local project_key = n.key_global('CMP', [environment, project]);
    local group_key =
      n.key_global('GRP', [environment, project, 'ADMIN']);
    local policy_keys = [
      n.key_global('PCY', [environment, project, 'ADMIN']),
      n.key_global('PCY', [environment, project, 'ADMIN', 'NET']),
      n.key_global('PCY', [environment, project, 'ADMIN', 'SEC']),
    ];
    local project_compartment =
      landing_zone.children[environment_key]
        .children[project_container_key]
        .children[project_key];
    local runner_principal =
      'allow dynamic-group dg-mccp-platform-runner';
    local group_principal =
      "allow group 'id_lz_common'/'grp-lz-%s-%s-admin'" %
      [std.asciiLower(environment), std.asciiLower(project)];
    local runner_policy(policy, suffix) =
      policy {
        name: policy.name + '-gitops',
        description:
          'GitOps equivalent of the pinned OE project policy.',
        statements: [
          local converted =
            std.strReplace(statement, group_principal, runner_principal);
          if std.length(std.findSubstr(' where all{', converted)) > 0
          then std.split(converted, ' where all{')[0]
          else converted
          for statement in policy.statements
        ] + (
          if suffix == 'net' then [
            '%s to manage network-security-groups in compartment cmp-lz-%s-network' %
            [runner_principal, std.asciiLower(environment)],
          ] else []
        ),
      };
    local source_policies = {
      [key]: iam.policies_configuration.supplied_policies[key]
      for key in policy_keys
    };
    local runner_policies = {
      [key + '-GITOPS']:
        runner_policy(
          source_policies[key],
          if std.endsWith(key, '-NET-KEY') then 'net'
          else if std.endsWith(key, '-SEC-KEY') then 'sec'
          else 'project',
        )
      for key in policy_keys
    };
    {
      compartments_configuration: {
        enable_delete: iam.compartments_configuration.enable_delete,
        default_parent_id: project_container_key,
        compartments: {
          [project_key]: project_compartment,
        },
      },
      identity_domain_groups_configuration:
        selected_groups(
          iam.identity_domain_groups_configuration,
          [group_key],
        ),
      policies_configuration:
        iam.policies_configuration {
          supplied_policies: source_policies + runner_policies,
        },
    };

  local base_outputs = {
    'op00_manage_global_landing_zone/generated/iam.json': op00_iam,
    'op01_manage_landing_zone_environment/generated/iam.json': op01_iam,
    'op01_manage_landing_zone_environment/generated/governance.json':
      full.governance,
    'op01_manage_landing_zone_environment/generated/network.json':
      op01_network,
    'op01_manage_landing_zone_environment/generated/observability_cis1_pre.json':
      fixed_observability(active_render.observability_cis1_pre),
    'op01_manage_landing_zone_environment/generated/observability_cis1.json':
      fixed_observability(active_render.observability_cis1),
    'op01_manage_landing_zone_environment/generated/security_cis1_pre.json':
      active_render.security_cis1_pre,
    'op01_manage_landing_zone_environment/generated/security_cis1.json':
      without_shared_network_security_zone(active_render.security_cis1),
  };
  local environment_outputs = std.foldl(
    function(outputs, environment)
      outputs + {
        [
          'op02_manage_environment/%s/generated/iam.json' %
          environment
        ]:
          op02_identity(environment),
        [
          'op02_manage_environment/%s/generated/network.json' %
          environment
        ]:
          op02_network(environment),
      },
    environment_names,
    base_outputs,
  );
  std.foldl(
    function(outputs, environment)
      std.foldl(
        function(project_outputs, project)
          project_outputs + {
            [
              'op04_manage_project/%s/%s-%s/generated/iam.json' %
              [environment, environment, project]
            ]:
              project_identity(environment, project),
          },
        project_names(environment),
        outputs,
      ),
    environment_names,
    environment_outputs,
  );

render
