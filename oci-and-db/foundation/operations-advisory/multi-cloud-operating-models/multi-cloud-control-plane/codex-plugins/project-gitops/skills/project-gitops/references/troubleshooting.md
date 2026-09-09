# Troubleshooting

| Error code | Tell the user |
| --- | --- |
| `INVALID_ARGUMENTS` | Correct the documented validator arguments. |
| `INVALID_REPOSITORY`, `INVALID_ORIGIN`, `INVALID_BASE_REF`, `INVALID_BASE_SHA` | Use the handed-off repository at its exact approved base. |
| `INVALID_HANDOFF`, `HANDOFF_MISMATCH`, `INVALID_WORKLOAD_COMPARTMENT` | Ask Cloud Operations to correct the environment handoff. |
| `INVALID_ENVIRONMENT`, `INVALID_REGION`, `INVALID_PATH`, `INVALID_MANIFEST_PATH` | Use the canonical selected-cloud manifest path. |
| `INVALID_JSON`, `INVALID_UTF8`, `JSON_DUPLICATE_KEY`, `JSON_SIZE_LIMIT`, `JSON_DEPTH_LIMIT`, `JSON_COLLECTION_LIMIT`, `JSON_STRING_LIMIT`, `JSON_NONFINITE_NUMBER` | Correct the manifest JSON and keep it within validator limits. |
| `INVALID_SECRET_PLACEHOLDER`, `CROSS_ENVIRONMENT_SECRET`, `INVALID_SECRET_VALUE` | Use an environment-qualified secret name. Never provide its value. |
| `INVALID_MANIFEST`, `INVALID_ADB_CHANGE`, `INVALID_COMPUTE_CHANGE`, `INVALID_NSG_CHANGE`, `INVALID_NSG_MANIFEST`, `INVALID_LIFECYCLE_CHANGE` | Rebuild the requested resource from its catalog contract. |
| `UNDECLARED_NSG_REFERENCE`, `PUBLIC_IP_FORBIDDEN` | Use handed-off private references and declared project NSGs. |
| `INVALID_CHANGE`, `INVALID_BRANCH`, `BINARY_DIFF`, `DIFF_SIZE_LIMIT`, `FILE_SIZE_LIMIT`, `WORKTREE_CHANGED` | Rebuild one supported manifest change on the required agent branch. |
| `GIT_TIMEOUT`, `GIT_FAILED`, `GIT_OUTPUT_LIMIT`, `INVALID_GIT_OUTPUT`, `UNSAFE_GIT_CONFIG` | Stop and provide the code to Cloud Operations. |
| `UNSUPPORTED_CLOUD`, `UNSUPPORTED_MANIFEST` | Request only an operation listed in the supported catalog contract. |
| `INVALID_EXPECTATION`, `PREVIEW_DRIFT` | Regenerate the validated preview before asking for confirmation. |
| `INTERNAL_ERROR` | Stop. Do not retry the write; provide the code to Cloud Operations. |
