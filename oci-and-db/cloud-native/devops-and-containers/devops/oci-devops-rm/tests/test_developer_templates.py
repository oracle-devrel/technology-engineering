import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeveloperTemplateTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def resource_body(self, resource_name):
        source = self.read("modules/devops/artifacts.tf")
        start = source.index(
            f'resource "oci_devops_deploy_artifact" "{resource_name}" {{'
        )
        next_resource = source.find('\nresource "', start + 1)
        return source[start:] if next_resource == -1 else source[start:next_resource]

    def test_release_command_specs_are_shared_singletons(self):
        for resource_name in (
            "promote_release_image_command_spec",
            "tag_release_commit_command_spec",
        ):
            self.assertNotIn("for_each", self.resource_body(resource_name))

    def test_component_build_specs_export_generic_deployment_parameters(self):
        for template in (
            "templates/application-delivery-pipeline.yaml.tpl",
            "templates/release-pipeline.yaml.tpl",
        ):
            source = self.read(template)
            self.assertIn("- image_repository", source)
            self.assertIn("- image_tag", source)
            self.assertNotRegex(source, r"component_image_(repository|tag)_variable")

    def test_production_values_keep_rc_parameter_for_chart_derivation(self):
        source = self.resource_body("component_prod_values")
        self.assertRegex(source, re.compile(r'image_tag_parameter\s*=\s*"image_tag"'))

        deployment = self.read("templates/component-chart-deployment.yaml.tpl")
        self.assertIn('regexReplaceAll "-rc\\\\.[0-9]+$" .Values.image.tag ""', deployment)

    def test_component_release_approval_follows_staging(self):
        source = self.read("modules/devops/deploy_pipelines.tf")
        self.assertNotIn(
            'resource "oci_devops_deploy_stage" "dry_run_component_prod"', source
        )
        self.assertNotIn('name  = "DRY_RUN"', source)
        self.assertIn(
            'id = oci_devops_deploy_stage.deploy_component["${each.key}:staging"].id',
            source,
        )
        self.assertIn("Approve promotion of ${each.value.name} from staging to production", source)

    def test_promotion_exports_generic_final_tag(self):
        source = self.read("templates/promote-release-image-command-spec.yaml.tpl")
        self.assertIn("- release_image_tag", source)
        self.assertIn('release_image_tag="$${release_candidate_tag%-rc.*}"', source)

    def test_development_mode_refreshes_generated_pipeline_specs(self):
        source = self.read("modules/devops/repositories.tf")
        self.assertIn('resource "null_resource" "refresh_platform_development"', source)
        self.assertIn('SEED_MODE      = "refresh"', source)
        self.assertIn("local.generated_component_build_specs", source)
        self.assertIn("component.build_spec_path", source)
        self.assertIn('"${name}-release-pipeline.yaml"', source)
        self.assertIn(
            'fileset("${path.root}/${local.platform_repo_path}/script", "**")',
            source,
        )
        self.assertIn("filesha256", source)

    def test_repository_starters_survive_oci_initial_commits(self):
        source = self.read("modules/devops/repositories.tf")

        for resource_name in (
            "seed_platform_shared",
            "seed_application_source",
            "seed_application_chart_baseline",
        ):
            start = source.index(f'resource "null_resource" "{resource_name}" {{')
            next_resource = source.find('\nresource "', start + 1)
            body = source[start:] if next_resource == -1 else source[start:next_resource]
            self.assertRegex(body, r'SEED_MODE\s*=\s*"add-only"')
            self.assertIn('seed_mode', body)
            self.assertNotRegex(body, r'SEED_MODE\s*=\s*"empty-repository"')

    def test_pipeline_wrappers_do_not_require_executable_git_modes(self):
        image_wrapper = self.read(
            "repos/pipelines/script/application-delivery-build-image.sh"
        )
        chart_wrapper = self.read(
            "repos/pipelines/script/application-delivery-package-chart.sh"
        )

        self.assertIn('bash "${SCRIPT_DIR}/build-push-image.sh"', image_wrapper)
        self.assertIn('bash "${SCRIPT_DIR}/package-push-chart.sh"', chart_wrapper)

    def test_custom_component_build_specs_are_referenced_but_not_generated(self):
        locals_source = self.read("modules/devops/locals.tf")
        self.assertIn(
            'build_spec_path            = coalesce(component.build_spec_path, "${component.name}-build-pipeline.yaml")',
            locals_source,
        )
        self.assertIn(
            "generated_component_build_specs", locals_source
        )
        self.assertIn("if component.generate_build_spec", locals_source)

        build_pipelines = self.read("modules/devops/build_pipelines.tf")
        self.assertIn("build_spec_file                    = each.value.build_spec_path", build_pipelines)

        repositories = self.read("modules/devops/repositories.tf")
        self.assertIn(
            "for_each = local.generated_component_build_specs", repositories
        )
        self.assertIn(
            "local.generated_component_build_specs[name].build_spec_path",
            repositories,
        )
        self.assertIn(
            'resource "local_file" "custom_application_delivery_pipeline"',
            repositories,
        )
        self.assertIn("sort(local.custom_build_spec_paths)", repositories)
        self.assertIn("custom_build_spec_paths", repositories)
        self.assertIn("never refreshed by Resource Manager", repositories)

        self.assertIn("custom_build_specs_by_path", locals_source)
        self.assertIn("component_names = sort", locals_source)

    def test_application_bootstrap_initializes_both_clusters_in_parallel(self):
        source = self.read("modules/devops/deploy_pipelines.tf")
        self.assertIn('display_name = "${each.value.name}-bootstrap"', source)
        self.assertIn(
            "for_each = local.application_bootstrap_targets",
            source,
        )
        self.assertIn(
            "command_spec_deploy_artifact_id = oci_devops_deploy_artifact.application_bootstrap_command_spec.id",
            source,
        )
        self.assertNotIn('resource "oci_devops_deploy_pipeline" "namespace_init"', source)
        self.assertNotIn('resource "oci_devops_deploy_stage" "application_bootstrap_baseline"', source)

    def test_application_bootstrap_credentials_default_to_empty(self):
        source = self.read("modules/devops/deploy_pipelines.tf")
        bootstrap_start = source.index(
            'resource "oci_devops_deploy_pipeline" "application_bootstrap"'
        )
        bootstrap_end = source.index(
            'resource "oci_devops_deploy_stage" "application_bootstrap_namespace"'
        )
        bootstrap = source[bootstrap_start:bootstrap_end]

        for parameter_name in ("registry_username", "pull_password_secret_ocid"):
            parameter_start = bootstrap.index(f'name          = "{parameter_name}"')
            parameter = bootstrap[parameter_start:parameter_start + 200]
            self.assertIn('default_value = null', parameter)

        self.assertNotIn('default_value = "0.1.0"', bootstrap)

        locals_source = self.read("modules/devops/locals.tf")
        self.assertIn('"${application_name}:noprod"', locals_source)
        self.assertIn('"${application_name}:prod"', locals_source)

        command_spec = self.read(
            "templates/application-bootstrap-command-spec.yaml.tpl"
        )
        self.assertIn(
            'oci devops deploy-stage get --stage-id "$${OCI_STAGE_ID}"',
            command_spec,
        )
        self.assertNotIn("--deploy-stage-id", command_spec)

    def test_component_verification_runs_helm_status_in_prod_only(self):
        source = self.read("modules/devops/deploy_pipelines.tf")
        self.assertIn('resource "oci_devops_deploy_stage" "verify_component_prod"', source)
        self.assertNotIn('resource "oci_devops_deploy_stage" "verify_component"', source)
        self.assertIn(
            "command_spec_deploy_artifact_id = oci_devops_deploy_artifact.component_verify_deployment_command_spec.id",
            source,
        )
        self.assertIn(
            'id = oci_devops_deploy_stage.deploy_component["${each.key}:staging"].id',
            source,
        )
        self.assertIn(
            "id = oci_devops_deploy_stage.tag_component_release_commit[each.key].id",
            source,
        )
        self.assertIn(
            "id = oci_devops_deploy_stage.deploy_component_prod[each.key].id",
            source,
        )

        command_spec = self.read(
            "templates/verify-component-production-command-spec.yaml.tpl"
        )
        self.assertIn('helm status "$${release}"', command_spec)
        self.assertIn('helm history "$${release}"', command_spec)
        self.assertIn('helm get notes "$${release}"', command_spec)
        self.assertIn('helm list --namespace "$${namespace}"', command_spec)
        self.assertNotIn("helm get manifest", command_spec)
        self.assertNotIn("helm get values", command_spec)
        self.assertIn('prod_cluster_id: "${prod_oke_cluster_id}"', command_spec)
        self.assertNotIn("verify-deployment.sh", command_spec)
        self.assertIn(
            'oci devops deploy-stage get --stage-id "$${OCI_STAGE_ID}"',
            command_spec,
        )
        self.assertNotIn("--deploy-stage-id", command_spec)

    def test_application_input_validates_derived_names_and_collisions(self):
        variables = self.read("variables.tf")
        self.assertIn("Applications are limited to 46 characters", variables)
        self.assertIn("components to 45", variables)
        self.assertIn("Application namespaces must be unique", variables)
        self.assertIn("Derived repository names must be unique", variables)
        self.assertIn("Chart repository names and paths must use safe lowercase relative naming", variables)

        checks = self.read("checks.tf")
        self.assertIn('check "recommended_application_scale"', checks)
        self.assertIn("local.component_count <= 50", checks)

    def test_deployment_parameter_descriptions_do_not_use_html_placeholders(self):
        for path in (ROOT / "modules").rglob("*.tf"):
            source = path.read_text(encoding="utf-8")
            for description in re.findall(r'description\s*=\s*"([^"]*)"', source):
                self.assertNotRegex(description, r"<[^>]+>", path)

    def test_release_archive_excludes_maintainer_agent_material(self):
        packaging = self.read("update.sh")
        self.assertIn('--exclude ".agents"', packaging)
        self.assertIn('--exclude "AGENT.md"', packaging)


if __name__ == "__main__":
    unittest.main()
