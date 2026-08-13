# Optional Multi-Cloud Plane UI

The Multi-Cloud Plane UI is an optional form-led way to prepare a request in an
already handed-off project repository. It creates an issue, branch, commit, and
pull request; it does not deploy infrastructure, approve a pull request, or
access cloud credentials.

Use the UI when a guided form is more convenient than editing a JSON manifest
directly. It supports the same approved Day 1 resources and OCI Day 2
operations as the direct GitHub route. Azure and Google Day 2 operations are
not part of the supplied baseline.

After the UI opens the pull request, follow the standard
[request lifecycle](request-lifecycle.md). The direct GitHub path remains
available for every supported request.

Cloud Operations installs and configures the UI separately. See the technical
[Optional UI README](../../repository-sources/optional-ui/README.md) for its GitHub App,
OAuth, runtime, and deployment requirements.
