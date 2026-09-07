version: 0.1
component: command
timeoutInSeconds: 600
shell: bash
env:
  variables:
    OCI_CLI_REGION: "${region}"
    image_repository: "$${image_repository}"
    release_candidate_tag: "$${image_tag}"
  exportedVariables:
    - release_image_tag

steps:
  - type: Command
    name: Validate release image promotion inputs
    timeoutInSeconds: 600
    failImmediatelyOnError: true
    command: |
      set -euo pipefail

      : "$${image_repository:?image_repository deployment parameter is required}"
      : "$${release_candidate_tag:?image_tag deployment parameter is required}"

      if ! printf '%s' "$${image_repository}" | grep -Eq '^[a-z0-9.-]+[.]ocir[.]io/.+/.+'; then
        echo "Invalid OCIR image repository: $${image_repository}" >&2
        exit 1
      fi
      if ! printf '%s' "$${release_candidate_tag}" | grep -Eq '^[0-9]+[.][0-9]+[.][0-9]+-rc[.][0-9]+$'; then
        echo "Invalid release candidate tag: $${release_candidate_tag}" >&2
        exit 1
      fi

      release_image_tag="$${release_candidate_tag%-rc.*}"
      if ! printf '%s' "$${release_image_tag}" | grep -Eq '^[0-9]+[.][0-9]+[.][0-9]+$'; then
        echo "Invalid final release tag: $${release_image_tag}" >&2
        exit 1
      fi
      export release_image_tag

      {
        printf "image_repository=%q\n" "$${image_repository}"
        printf "release_candidate_tag=%q\n" "$${release_candidate_tag}"
        printf "release_image_tag=%q\n" "$${release_image_tag}"
      } > "$${OCI_WORKSPACE_DIR}/release-image-promotion.env"

      echo "Release image promotion inputs validated"

  - type: Command
    name: Promote release image tag
    timeoutInSeconds: 600
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      source "$${OCI_WORKSPACE_DIR}/release-image-promotion.env"
      export release_image_tag

      registry="$${image_repository%%/*}"
      repository_path="$${image_repository#*/}"
      manifest_url="https://$${registry}/v2/$${repository_path}/manifests"
      accept_header='application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json'

      token="$(oci raw-request --http-method GET --target-uri "https://$${registry}/20180419/docker/token" | tr -d '\n' | sed -E 's/.*"token"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
      if [ -z "$${token}" ]; then
        echo "Failed to fetch OCIR bearer token" >&2
        exit 1
      fi

      manifest_file="$(mktemp)"
      headers_file="$(mktemp)"
      if curl -fsS -D "$${headers_file}" \
        -H "Authorization: Bearer $${token}" \
        -H "Accept: $${accept_header}" \
        "$${manifest_url}/$${release_image_tag}" >/dev/null; then
        echo "Final release image tag already exists: $${image_repository}:$${release_image_tag}" >&2
        exit 1
      fi

      curl -fsS -D "$${headers_file}" \
        -H "Authorization: Bearer $${token}" \
        -H "Accept: $${accept_header}" \
        "$${manifest_url}/$${release_candidate_tag}" \
        -o "$${manifest_file}"

      source_digest="$(awk 'BEGIN{IGNORECASE=1} /^Docker-Content-Digest:/ {gsub("\r", "", $2); print $2}' "$${headers_file}" | tail -1)"
      content_type="$(awk 'BEGIN{IGNORECASE=1} /^Content-Type:/ {$1=""; sub(/^ /, ""); gsub("\r", ""); print}' "$${headers_file}" | tail -1)"
      if [ -z "$${source_digest}" ] || [ -z "$${content_type}" ]; then
        echo "Unable to read source image manifest metadata" >&2
        exit 1
      fi

      curl -fsS -X PUT \
        -H "Authorization: Bearer $${token}" \
        -H "Content-Type: $${content_type}" \
        --data-binary "@$${manifest_file}" \
        "$${manifest_url}/$${release_image_tag}" >/dev/null

      curl -fsS -D "$${headers_file}" \
        -H "Authorization: Bearer $${token}" \
        -H "Accept: $${accept_header}" \
        "$${manifest_url}/$${release_image_tag}" >/dev/null
      target_digest="$(awk 'BEGIN{IGNORECASE=1} /^Docker-Content-Digest:/ {gsub("\r", "", $2); print $2}' "$${headers_file}" | tail -1)"
      if [ "$${source_digest}" != "$${target_digest}" ]; then
        echo "Final release image digest mismatch: $${source_digest} != $${target_digest}" >&2
        exit 1
      fi

      echo "Promoted $${image_repository}:$${release_candidate_tag} to $${image_repository}:$${release_image_tag}"
      echo "Digest: $${target_digest}"
