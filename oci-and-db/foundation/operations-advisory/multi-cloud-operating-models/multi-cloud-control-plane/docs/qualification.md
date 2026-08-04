# Qualification boundary

The supplied MVP baseline was qualified as a reference implementation, not as
a certification of every customer environment. Maintainer qualification
covered:

- parsing every shipped JSON file and validating each catalog template against
  its published JSON Schema;
- semantic validation of supported OCI, Azure, and Google create, update, and
  delete requests, including handoff mismatches, public-IP rejection,
  environment-qualified placeholders, unknown clouds, and mixed tuples;
- Terraform formatting, initialization, validation, and credential-free mocked
  lifecycle cases for the Azure and Google adapters;
- synthetic Git repository exercises for governed Project GitOps requests,
  Cloud Operator handoff flows, and environment retirement controls;
- workflow linting, documentation links, rendered installation placeholders,
  publication hygiene, and component parity checks; and
- live OCI smoke evidence for the supplied OCI workload and operations paths.

The maintainer tests and synthetic fixtures are deliberately excluded from the
customer publication. The customer-facing schemas, contracts, templates, and
runbooks remain available for inspection.

## Explicit exclusions

- Azure and Google were not applied to live target-cloud environments for this
  publication and must not be represented as live-cloud certified.
- Azure and Google Day 2 operations are not part of the supplied baseline.
- The GitHub Free profile is qualified for controlled non-production use with
  procedural approval. Production enablement requires the hardened approval
  model and a customer security review.
- Customer extensions are outside the qualification boundary until the full
  [extension model](architecture.md#extension-model) is implemented and tested.

Before enabling requests, render the installation for the customer
organization, complete the selected cloud handoff, and run the acceptance steps
in [Deployment](deployment.md) and [First request](first-request.md) on the
customer runners and identities.
