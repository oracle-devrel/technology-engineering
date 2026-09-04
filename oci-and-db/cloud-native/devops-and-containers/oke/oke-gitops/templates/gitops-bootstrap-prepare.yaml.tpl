version: 0.1
component: command
timeoutInSeconds: 900
shell: bash
failImmediatelyOnError: true
env:
  variables:
    OCI_CLI_REGION: "${region}"
    cluster_id: "${oke_cluster_id}"
    kube_endpoint: "${kube_endpoint}"
    gitops_agent: "${gitops_agent}"
    gitops_namespace: "${gitops_namespace}"
    ocir_registry: "${ocir_registry}"
    ocir_chart_repository: "${ocir_chart_repository}"
    legacy_git_username: "${legacy_git_username}"
    legacy_ocir_username: "${legacy_ocir_username}"
    cluster_config_repo_url: "${cluster_config_repo_url}"
    apps_config_repo_url: "${apps_config_repo_url}"
    fleet_config_repo_url: "${fleet_config_repo_url}"
    git_read_credentials_secret_ocid: "$${git_read_credentials_secret_ocid}"
    registry_pull_secret_ocid: "$${registry_pull_secret_ocid}"
    auth_token_secret_ocid: "$${auth_token_secret_ocid}"

steps:
  - type: Command
    name: Validate bootstrap inputs
    timeoutInSeconds: 60
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      is_vault_secret() {
        printf '%s' "$1" | grep -Eq '^ocid1\.vaultsecret\.'
      }

      git_secret_valid=false
      ocir_secret_valid=false
      legacy_secret_valid=false
      is_vault_secret "$${git_read_credentials_secret_ocid}" && git_secret_valid=true
      is_vault_secret "$${registry_pull_secret_ocid}" && ocir_secret_valid=true
      is_vault_secret "$${auth_token_secret_ocid}" && legacy_secret_valid=true

      if [ "$${git_secret_valid}" != "$${ocir_secret_valid}" ]; then
        echo "git_read_credentials_secret_ocid and registry_pull_secret_ocid must be configured together" >&2
        exit 1
      elif [ "$${git_secret_valid}" = true ]; then
        echo "Separate Git and OCIR runtime credentials selected"
      elif [ "$${legacy_secret_valid}" = true ]; then
        echo "WARNING: auth_token_secret_ocid is deprecated; migrate to separate read-only Git and OCIR credentials" >&2
      else
        echo "Set both runtime credential secret OCIDs to OCI Vault secrets" >&2
        exit 1
      fi

      printf '%s' "$${cluster_id}" | grep -Eq '^ocid1\.cluster\.' || {
        echo "Invalid OKE cluster OCID" >&2
        exit 1
      }
      case "$${gitops_agent}" in
        argocd|fluxcd) ;;
        *) echo "Unsupported GitOps agent: $${gitops_agent}" >&2; exit 1 ;;
      esac
      echo "Bootstrap inputs validated for $${gitops_agent}"

  - type: Command
    name: Configure OKE access
    timeoutInSeconds: 180
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      oci ce cluster create-kubeconfig \
        --cluster-id "$${cluster_id}" \
        --file "$${KUBECONFIG}" \
        --region "$${OCI_CLI_REGION}" \
        --token-version 2.0.0 \
        --kube-endpoint "$${kube_endpoint}"
      kubectl version --client
      kubectl get namespace kube-system >/dev/null

  - type: Command
    name: Prepare namespace and credentials
    timeoutInSeconds: 300
    failImmediatelyOnError: true
    command: |
      set -euo pipefail
      export KUBECONFIG="$${OCI_WORKSPACE_DIR}/kubeconfig"
      credentials_dir="$${OCI_WORKSPACE_DIR}/gitops-credentials"
      mkdir -p "$${credentials_dir}"
      chmod 700 "$${credentials_dir}"

      git_json_path="$${credentials_dir}/git.json"
      ocir_json_path="$${credentials_dir}/ocir.json"
      legacy_token_path="$${credentials_dir}/legacy-token"
      git_username_path="$${credentials_dir}/git-username"
      git_password_path="$${credentials_dir}/git-password"
      ocir_username_path="$${credentials_dir}/ocir-username"
      ocir_password_path="$${credentials_dir}/ocir-password"
      dockerconfig_path="$${credentials_dir}/dockerconfig.json"
      trap 'rm -f "$${git_json_path}" "$${ocir_json_path}" "$${legacy_token_path}" "$${git_username_path}" "$${git_password_path}" "$${ocir_username_path}" "$${ocir_password_path}" "$${dockerconfig_path}"' EXIT

      umask 077
      read_vault_secret() {
        secret_id="$1"
        output_path="$2"
        oci secrets secret-bundle get \
          --secret-id "$${secret_id}" \
          --query 'data."secret-bundle-content".content' \
          --raw-output |
          base64 --decode >"$${output_path}"
        if [ ! -s "$${output_path}" ]; then
          echo "The configured OCI Vault secret is empty" >&2
          exit 1
        fi
      }

      is_vault_secret() {
        printf '%s' "$1" | grep -Eq '^ocid1\.vaultsecret\.'
      }

      git_secret_valid=false
      ocir_secret_valid=false
      is_vault_secret "$${git_read_credentials_secret_ocid}" && git_secret_valid=true
      is_vault_secret "$${registry_pull_secret_ocid}" && ocir_secret_valid=true

      if [ "$${git_secret_valid}" = true ] && [ "$${ocir_secret_valid}" = true ]; then
        read_vault_secret "$${git_read_credentials_secret_ocid}" "$${git_json_path}"
        read_vault_secret "$${registry_pull_secret_ocid}" "$${ocir_json_path}"

        export git_json_path ocir_json_path
        export git_username_path git_password_path
        export ocir_username_path ocir_password_path
        python3 - <<'PY'
      import json
      import os
      from pathlib import Path

      credentials = (
          (
              "Git",
              Path(os.environ["git_json_path"]),
              Path(os.environ["git_username_path"]),
              Path(os.environ["git_password_path"]),
          ),
          (
              "OCIR",
              Path(os.environ["ocir_json_path"]),
              Path(os.environ["ocir_username_path"]),
              Path(os.environ["ocir_password_path"]),
          ),
      )

      for label, source, username_target, password_target in credentials:
          try:
              value = json.loads(source.read_text(encoding="utf-8"))
          except (json.JSONDecodeError, OSError) as error:
              raise SystemExit(f"{label} Vault secret must contain valid JSON: {error}")
          if not isinstance(value, dict):
              raise SystemExit(f"{label} Vault secret must contain a JSON object")
          username = value.get("username")
          password = value.get("password")
          if not isinstance(username, str) or not username.strip():
              raise SystemExit(f"{label} Vault secret is missing a non-empty username")
          if not isinstance(password, str) or not password:
              raise SystemExit(f"{label} Vault secret is missing a non-empty password")
          username_target.write_text(username.strip(), encoding="utf-8")
          password_target.write_text(password, encoding="utf-8")
      PY
        echo "Loaded separate read-only Git and OCIR credentials"
      else
        read_vault_secret "$${auth_token_secret_ocid}" "$${legacy_token_path}"
        printf '%s' "$${legacy_git_username}" >"$${git_username_path}"
        printf '%s' "$${legacy_ocir_username}" >"$${ocir_username_path}"
        cp "$${legacy_token_path}" "$${git_password_path}"
        cp "$${legacy_token_path}" "$${ocir_password_path}"
        echo "WARNING: using deprecated shared bootstrap credentials" >&2
      fi

      git_runtime_username="$(cat "$${git_username_path}")"
      ocir_runtime_username="$(cat "$${ocir_username_path}")"

      cluster_repo_prefix="$${cluster_config_repo_url%/*}"
      apps_repo_prefix="$${apps_config_repo_url%/*}"
      if [ "$${cluster_repo_prefix}" != "$${apps_repo_prefix}" ]; then
        echo "cluster-config and apps-config do not share an OCI DevOps repository URL prefix" >&2
        exit 1
      fi

      export GIT_USERNAME="$${git_runtime_username}"
      export GIT_PASSWORD
      GIT_PASSWORD="$(cat "$${git_password_path}")"
      export GIT_TERMINAL_PROMPT=0
      credential_helper='!f() { printf "username=%s\npassword=%s\n" "$GIT_USERNAME" "$GIT_PASSWORD"; }; f'
      git -c credential.helper="$${credential_helper}" \
        ls-remote "$${cluster_config_repo_url}" HEAD >/dev/null
      git -c credential.helper="$${credential_helper}" \
        ls-remote "$${apps_config_repo_url}" HEAD >/dev/null
      if [ -n "$${fleet_config_repo_url}" ]; then
        fleet_repo_prefix="$${fleet_config_repo_url%/*}"
        if [ "$${cluster_repo_prefix}" != "$${fleet_repo_prefix}" ]; then
          echo "fleet-config does not share the OCI DevOps repository URL prefix" >&2
          exit 1
        fi
        git -c credential.helper="$${credential_helper}" \
          ls-remote "$${fleet_config_repo_url}" HEAD >/dev/null
      fi
      unset GIT_PASSWORD GIT_USERNAME
      echo "Read-only Git credentials validated against the required repositories"

      export ocir_registry
      export ocir_runtime_username ocir_password_path dockerconfig_path
      python3 - <<'PY'
      import base64
      import json
      import os
      from pathlib import Path

      registry = os.environ["ocir_registry"]
      username = os.environ["ocir_runtime_username"]
      password = Path(os.environ["ocir_password_path"]).read_text(encoding="utf-8")
      auth = base64.b64encode(f"{username}:{password}".encode()).decode()
      with open(os.environ["dockerconfig_path"], "w", encoding="utf-8") as stream:
          json.dump({
              "auths": {
                  registry: {
                      "username": username,
                      "password": password,
                      "auth": auth,
                  }
              }
          }, stream)
      PY

      kubectl create namespace "$${gitops_namespace}" \
        --dry-run=client -o yaml | kubectl apply -f -
      kubectl -n "$${gitops_namespace}" create secret generic ocirsecret \
        --type=kubernetes.io/dockerconfigjson \
        --from-file=.dockerconfigjson="$${dockerconfig_path}" \
        --dry-run=client -o yaml | kubectl apply -f -

      if [ "$${gitops_agent}" = "fluxcd" ]; then
        kubectl -n "$${gitops_namespace}" create secret generic git-token-auth \
          --from-literal=username="$${git_runtime_username}" \
          --from-file=password="$${git_password_path}" \
          --dry-run=client -o yaml | kubectl apply -f -
      else
        create_argocd_credentials_secret() {
          secret_type="$1"
          secret_name="$2"
          password_path="$3"
          shift 3
          kubectl -n "$${gitops_namespace}" create secret generic "$${secret_name}" \
            "$@" \
            --from-file=password="$${password_path}" \
            --dry-run=client -o yaml |
            kubectl label --local -f - \
              argocd.argoproj.io/secret-type="$${secret_type}" \
              -o yaml |
            kubectl apply -f -
        }

        create_argocd_credentials_secret repo-creds oci-devops-git-credentials \
          "$${git_password_path}" \
          --from-literal=type=git \
          --from-literal=url="$${cluster_repo_prefix}" \
          --from-literal=username="$${git_runtime_username}"
        create_argocd_credentials_secret repository ocir-oci-repo \
          "$${ocir_password_path}" \
          --from-literal=type=helm \
          --from-literal=name=ocir \
          --from-literal=enableOCI=true \
          --from-literal=url="$${ocir_chart_repository}" \
          --from-literal=username="$${ocir_runtime_username}"

        kubectl -n "$${gitops_namespace}" delete secret \
          cluster-config-repo apps-config-repo \
          --ignore-not-found
      fi

      echo "Namespace and separated runtime credentials are ready"
