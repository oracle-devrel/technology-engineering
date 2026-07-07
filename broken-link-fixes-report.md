# Broken Link Fix Report

Scope: repository-internal page links in Markdown files: normal Markdown links, reference links, and HTML `href` attributes. External URLs, pure anchors, images, scripts, PDFs, source files, notebooks, and other non-page assets were skipped. Local `LICENSE` / `LICENSE.txt` links were normalized to the canonical GitHub URL requested by Alexander.

- Markdown files scanned: 1185
- Auto-fixed moved page links: 2
- License links updated to canonical URL: 91
- Broken page-like links left for review: 10

## Auto-Fixed Links

| File | Old Link | New Link | Reason |
| --- | --- | --- | --- |
| `oci-and-db/foundation/landing-zones/README.md` | `/landing-zones/standard_landing_zones/readme.md` | `./standard_landing_zones/readme.md` | known FY27 folder move |
| `oci-and-db/foundation/landing-zones/README.md` | `/landing-zones/commons/oci_landingzones_iac.md` | `./commons/oci_landingzones_iac.md` | known FY27 folder move |

## License Link Update

Updated 91 local license links so their target is `https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt`. The visible link text was left unchanged.

## Remaining Broken Page-Like Links And Suggested Fixes

| File | Link | Resolved Missing Path | Suggested Fix |
| --- | --- | --- | --- |
| `oci-and-db/virtualization/oracle-cloud-vmware-solution/README.md` | `def` | `oci-and-db/virtualization/oracle-cloud-vmware-solution/def` | Likely Markdown reference-definition false positive; review manually, probably no link fix needed. |
| `oci-and-db/virtualization/openshift-on-oci/README.md` | `def` | `oci-and-db/virtualization/openshift-on-oci/def` | Likely Markdown reference-definition false positive; review manually, probably no link fix needed. |
| `oci-and-db/cloud-native/devops-and-containers/functions/java-helloworld-ai-with-local-dev-and-oci-functions/README.md` | `Dockerfile.local_oci` | `oci-and-db/cloud-native/devops-and-containers/functions/java-helloworld-ai-with-local-dev-and-oci-functions/Dockerfile.local_oci` | No safe automatic fix found; target may need to be restored, renamed, or updated manually. |
| `oci-and-db/cloud-native/devops-and-containers/functions/java-helloworld-ai-with-local-dev-and-oci-functions/README.md` | `./files/src/` | `oci-and-db/cloud-native/devops-and-containers/functions/java-helloworld-ai-with-local-dev-and-oci-functions/files/src` | Target directory exists but has no README page; link to a specific Markdown file or add a README. |
| `oci-and-db/cloud-native/devops-and-containers/functions/java-helloworld-ai-with-local-dev-and-oci-functions/README.md` | `./files/Dockerfile.native` | `oci-and-db/cloud-native/devops-and-containers/functions/java-helloworld-ai-with-local-dev-and-oci-functions/files/Dockerfile.native` | No safe automatic fix found; target may need to be restored, renamed, or updated manually. |
| `ai/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/in-database-machine-learning/files/OML_WAD_v1.3.md` | `**OAC**:Oracle` | `ai/analytical-data-platform-lakehouse/shared-assets/workload-architecture-documents/in-database-machine-learning/files/**OAC**:Oracle` | Likely Markdown reference-definition false positive; review manually, probably no link fix needed. |
| `oci-and-db/foundation/observability-and-management/assets/oci-log-analytics-detections/docs/WEBAPP.md` | `../webapp/deploy/oke/README.md` | `oci-and-db/foundation/observability-and-management/assets/oci-log-analytics-detections/webapp/deploy/oke/README.md` | No safe automatic fix found; target may need to be restored, renamed, or updated manually. |
| `oci-and-db/foundation/observability-and-management/assets/oci-log-analytics-detections/skills/oci-log-analytics-dashboard-enhancer/SKILL.md` | `references/kql-conversion-architecture.md` | `oci-and-db/foundation/observability-and-management/assets/oci-log-analytics-detections/skills/oci-log-analytics-dashboard-enhancer/references/kql-conversion-architecture.md` | No safe automatic fix found; target may need to be restored, renamed, or updated manually. |
| `oci-and-db/cloud-native/devops-and-containers/devops/oci-devops-terraform-function-java-graalvm/README.md` | `./files/build_pipeline_specs/` | `oci-and-db/cloud-native/devops-and-containers/devops/oci-devops-terraform-function-java-graalvm/files/build_pipeline_specs` | Target directory exists but has no README page; link to a specific Markdown file or add a README. |
| `oci-and-db/cloud-native/devops-and-containers/devops/oci-devops-terraform-function-java-graalvm/README.md` | `./files` | `oci-and-db/cloud-native/devops-and-containers/devops/oci-devops-terraform-function-java-graalvm/files` | Target directory exists but has no README page; link to a specific Markdown file or add a README. |
