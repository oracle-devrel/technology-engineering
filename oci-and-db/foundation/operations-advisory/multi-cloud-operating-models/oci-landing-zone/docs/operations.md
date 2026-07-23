# Day-to-day operations

Use one focused pull request for each foundation change. The pull request should
show the configuration change and its Terraform plan before approval.

Cloud Operators are responsible for:

- Maintaining tenancy IAM, shared networking, environments, and platform
  foundations.
- Creating each official OE project compartment, group, and policies through
  OP04.
- Reviewing plans for unexpected replacement, deletion, or privilege changes.
- Confirming state and OCI agree after each deployment.
- Providing the validated project handoff after OP04.

Project Teams must not modify foundation or OP04 configuration. They manage
project NSGs, workloads, and supported lifecycle operations in their project
repository.

If a plan or apply fails, retain the workflow logs and determine whether
Terraform state matches OCI before submitting a corrective pull request. Do not
edit state manually or bypass review with a local apply.

The workflow publishes `environment_information.md` for people and
`project-foundation-handoff.json` for automated processing. Keep the Markdown
file at the machine contract's exact `handoff_path` in the target project
repository.
