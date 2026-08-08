// Copyright (c) 2026 Oracle and/or its affiliates.
//
// OCI Landing Zone's TBAC add-on is the policy source of truth. This adapter
// only parameterizes its One-OE preprod example for the environment catalogue
// used by this foundation; it deliberately does not recreate policy statements.
local official_iam =
  import 'addons/oci-tbac/oci_open_lz_one-oe_iam.auto.tfvars.json';
local official_governance =
  import 'addons/oci-tbac/oci_open_lz_one-oe_governance.auto.tfvars.json';

local namespace = 'tn-lzp-proj-role';
local roles = {
  app: 'app-admin',
  database: 'db-admin',
  infrastructure: 'infra-admin',
};
local source_policy_keys = {
  app: 'PCY-LZP-PREPROD-PROJECTS-APP-ADMINISTRATION',
  database: 'PCY-LZP-PREPROD-PROJECTS-DB-ADMINISTRATION',
  infrastructure: 'PCY-LZP-PREPROD-PROJECTS-INFRA-ADMINISTRATION',
};
local source_policies = official_iam.policies_configuration.supplied_policies;
local replace_environment_names(statement, environment) =
  local projects = 'cmp-lz-%s-projects' % std.asciiLower(environment);
  local network = 'cmp-lz-%s-network' % std.asciiLower(environment);
  local security = 'cmp-lz-%s-security' % std.asciiLower(environment);
  std.strReplace(
    std.strReplace(
      std.strReplace(statement, 'cmp-lzp-pp-projects', projects),
      'cmp-lzp-pp-network', network,
    ),
    'cmp-lzp-pp-security', security,
  );
local role_key(n, environment, project, role) =
  n.key_global(
    'GRP',
    [environment, project] +
      if role == 'app' then ['APP', 'ADMINS']
      else if role == 'database' then ['DB', 'ADMINS']
      else ['INFRA', 'ADMINS'],
  );
local role_name(environment, project, role) =
  'grp-lz-%s-%s-%s-admins' % [
    std.asciiLower(environment),
    std.asciiLower(project),
    if role == 'database' then 'db'
    else if role == 'infrastructure' then 'infra'
    else role,
  ];
local project_group_key(n, environment, project) =
  n.key_global('GRP', [environment, project, 'ADMINS']);
local project_group_name(environment, project) =
  'grp-lz-%s-%s-admins' % [
    std.asciiLower(environment),
    std.asciiLower(project),
  ];
local project_key(n, environment, project) =
  n.key_global('CMP', [environment, project]);
local child_key(n, environment, project, role) =
  n.key_global(
    'CMP',
    [environment, project] +
      if role == 'app' then ['APP']
      else if role == 'database' then ['DB']
      else ['INFRA'],
  );
local project_name(environment, project) =
  'cmp-lz-%s-%s' % [
    std.asciiLower(environment),
    std.asciiLower(project),
  ];

{
  governance: official_governance,
  project_key: project_key,
  child_key: child_key,
  project_compartment(n, environment, project): {
    name: project_name(environment, project),
    description: 'OCI Landing Zone TBAC project root compartment.',
    defined_tags: {
      [namespace + '.proj-admin']:
        project_group_name(environment, project),
    },
    children: {
      [child_key(n, environment, project, role)]: {
        name: project_name(environment, project) +
          if role == 'app' then '-app'
          else if role == 'database' then '-db'
          else '-infra',
        description: 'OCI Landing Zone TBAC project %s compartment.' % role,
        defined_tags: {
          [namespace + '.' + roles[role]]:
            role_name(environment, project, role),
        },
      }
      for role in std.objectFields(roles)
    },
  },
  project_groups(n, environment, project): {
    groups: {
      [project_group_key(n, environment, project)]: {
        name: project_group_name(environment, project),
        description: 'OCI Landing Zone TBAC project administrators.',
        defined_tags: {
          [namespace + '.proj-admin']:
            project_group_name(environment, project),
        },
      },
    } + {
      [role_key(n, environment, project, role)]: {
        name: role_name(environment, project, role),
        description: 'OCI Landing Zone TBAC project %s administrators.' % role,
        defined_tags: {
          [namespace + '.proj-admin']:
            project_group_name(environment, project),
          [namespace + '.' + roles[role]]:
            role_name(environment, project, role),
        },
      }
      for role in std.objectFields(roles)
    },
  },
  common_policies: {
    'PCY-LZ-PROJECTS-COMMON-KEY':
      source_policies['PCY-LZP-PROJECTS-COMMON'] {
        name: 'pcy-lz-projects-common',
      },
  },
  environment_policies(n, environment): {
    ['PCY-LZ-%s-PROJECTS-%s-ADMINISTRATION-KEY' % [
      std.asciiUpper(environment), std.asciiUpper(role),
    ]]:
      local source = source_policies[source_policy_keys[role]];
      source {
        name: 'pcy-lz-%s-projects-%s-administration' % [
          std.asciiLower(environment), std.asciiLower(role),
        ],
        description: source.description,
        compartment_id: n.key_global('CMP', [environment]),
        statements: [
          replace_environment_names(statement, environment)
          for statement in source.statements
        ],
      }
    for role in std.objectFields(roles)
  },
}
