# Optional Multi-Cloud Control Plane UI

Use the UI when you prefer a guided form to editing JSON.

1. Sign in and select your handed-off project repository.
2. Choose one supported resource or OCI lifecycle operation.
3. Select the environment and region, then complete the requested fields using
   the available handoff values.
4. Review and submit the request.
5. Add your change reference, such as `CRQ1234`, if your change process uses
   one. The field is optional and accepts any format; the value appears in the
   pull-request title and the audit log.
6. Follow the standard [request lifecycle](request-lifecycle.md) after the UI
   opens the pull request.

The UI creates an issue, branch, commit, and pull request, and holds no more
authority than that. Check [Reference capabilities](../reference/support.md) for the
resources and lifecycle operations available through this interface.

The UI renders catalog values exactly. For OCI Compute and Autonomous Database,
select the published Small, Medium, or Large profile; its capacity, image,
license, storage, and auto-scaling values are not editable in the form. For an
OCI project NSG, choose either a new NSG or an existing one, then add zero or
more approved TCP ingress and egress rules. The UI writes integer destination
port ranges and adds rules to an existing NSG without replacing its creation
fields. It never offers an arbitrary resource-JSON editor or an unmodelled
catalog field.

If the UI is not available, use the GitHub interface. Cloud Operations installs
it using the [optional UI setup](../installation/optional-interfaces.md#optional-multi-cloud-control-plane-ui).
