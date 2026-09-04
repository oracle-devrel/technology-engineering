version: 0.1
component: command
timeoutInSeconds: 600
shell: bash
env:
  variables:
    OCI_CLI_REGION: "${region}"
    source_repository_id: "$${source_repository_id}"
    release_candidate_tag: "$${image_tag}"

steps:
  - type: Command
    name: Tag released commit
    timeoutInSeconds: 600
    failImmediatelyOnError: true
    command: |
      set -euo pipefail

      : "$${source_repository_id:?source repository id is required}"
      : "$${release_candidate_tag:?image_tag deployment parameter is required}"

      if ! printf '%s' "$${source_repository_id}" | grep -Eq '^ocid1[.]devopsrepository[.]'; then
        echo "Invalid source repository OCID: $${source_repository_id}" >&2
        exit 1
      fi
      if ! printf '%s' "$${release_candidate_tag}" | grep -Eq '^[0-9]+[.][0-9]+[.][0-9]+-rc[.][0-9]+$'; then
        echo "Invalid release candidate tag: $${release_candidate_tag}" >&2
        exit 1
      fi

      release_tag="$${release_candidate_tag%-rc.*}"
      if ! printf '%s' "$${release_tag}" | grep -Eq '^[0-9]+[.][0-9]+[.][0-9]+$'; then
        echo "Invalid final release tag: $${release_tag}" >&2
        exit 1
      fi

      rc_commit_id="$(oci devops repository list-refs \
        --repository-id "$${source_repository_id}" \
        --ref-type TAG \
        --ref-name "$${release_candidate_tag}" \
        --query 'data.items[0]."object-id"' \
        --raw-output)"
      if [ -z "$${rc_commit_id}" ] || [ "$${rc_commit_id}" = "null" ]; then
        echo "Release candidate Git tag not found: $${release_candidate_tag}" >&2
        exit 1
      fi

      final_commit_id="$(oci devops repository list-refs \
        --repository-id "$${source_repository_id}" \
        --ref-type TAG \
        --ref-name "$${release_tag}" \
        --query 'data.items[0]."object-id"' \
        --raw-output)"
      if [ -n "$${final_commit_id}" ] && [ "$${final_commit_id}" != "null" ]; then
        if [ "$${final_commit_id}" = "$${rc_commit_id}" ]; then
          echo "Final release Git tag already points to the released commit: $${release_tag}"
          exit 0
        fi
        echo "Final release Git tag $${release_tag} already points to a different commit: $${final_commit_id}" >&2
        exit 1
      fi

      oci devops repository create-or-update-git-tag-details \
        --repository-id "$${source_repository_id}" \
        --ref-name "$${release_tag}" \
        --object-id "$${rc_commit_id}" >/dev/null

      echo "Tagged released commit $${rc_commit_id} as $${release_tag}"
