# Function Event Triggers

`FunctionEventTrigger` declaratively routes an event type to an OCI Function referenced by this operator's `Function` CRD.

There are two trigger backends:

- OCI service event types such as `com.oraclecloud.objectstorage.createobject` are backed by OCI Events Rules.
- Kubernetes-native event types with the reserved `functionevent.` prefix are backed by `FunctionEvent` CRDs and invoke directly through the operator.

Do not mix OCI event types and `functionevent.*` values in one trigger.

## Resource Model

Create or reference a `Function` first.

For OCI Events triggers, the trigger controller waits until that `Function` has:

- `Ready=True`
- `status.functionId` populated

Then it creates or updates an OCI Events Rule in `spec.compartmentId` with a FAAS action targeting that function OCID.

```yaml
apiVersion: functions.oci.oracle.com/v1alpha1
kind: FunctionEventTrigger
metadata:
  name: object-created-trigger
spec:
  functionRef:
    name: managed-hello
  compartmentId: <COMPARTMENT_OCID>
  displayName: object-created-trigger
  description: Invoke managed-hello when objects are created
  isEnabled: true
  deletionPolicy: Delete
  condition:
    eventType:
    - com.oraclecloud.objectstorage.createobject
    data:
      additionalDetails:
        bucketName: <BUCKET_NAME>
```

The controller stores the OCI Events Rule OCID in `status.ruleId`.

For Kubernetes-native FunctionEvent triggers, omit OCI Events rule fields:

```yaml
apiVersion: functions.oci.oracle.com/v1alpha1
kind: FunctionEventTrigger
metadata:
  name: order-created-trigger
spec:
  functionRef:
    name: managed-hello
  isEnabled: true
  condition:
    eventType:
    - functionevent.order.created
```

No OCI Events Rule is created for `functionevent.*` triggers. `compartmentId`, `displayName`, and `deletionPolicy` are not required for FunctionEvent-only triggers. See [Function Events](function-events.md) for creating Kubernetes-native event objects.

`condition.eventType` is a Kubernetes list field. For the common single-value case, the controller renders one item as the scalar OCI Events condition value:

```json
{"eventType":"com.oraclecloud.objectstorage.createobject","data":{"additionalDetails":{"bucketName":"my-bucket"}}}
```

Structured `condition.data` also renders single-item arrays as scalar values for compatibility with OCI Events. Multiple event types or multiple values for one data attribute are preserved as arrays, which OCI Events documents as matching if any value in the array matches the event.

## Raw Conditions

For exact OCI Events condition JSON, use `condition.rawJson` instead of the structured fields:

```yaml
condition:
  rawJson: |
    {
      "eventType": "com.oraclecloud.objectstorage.createobject",
      "data": {
        "additionalDetails": {
          "bucketName": "my-bucket"
        }
      }
    }
```

`rawJson` is mutually exclusive with `eventType` and `data`. It must already be valid OCI Events condition JSON. Use scalar values for single event types or data attributes, and arrays only when you intentionally want an any-of match across multiple values.

## Deletion Policy

- `deletionPolicy: Delete` is the default for OCI Events triggers. Deleting the Kubernetes trigger deletes the OCI Events Rule.
- `deletionPolicy: Retain` removes the Kubernetes object but leaves the OCI Events Rule in OCI.
- FunctionEvent-only triggers do not create OCI Events Rules, so `deletionPolicy` is not used.

## Run The Sample

Edit placeholders in the sample:

```sh
cp config/samples/functions_v1alpha1_functioneventtrigger_object_created.yaml /tmp/object-created-trigger.yaml
```

Set:

- `<COMPARTMENT_OCID>` to the compartment where the OCI Events Rule should live.
- `<BUCKET_NAME>` to the Object Storage bucket name.
- `spec.functionRef.name` to a `Function` in the same namespace, if not `managed-hello`.

Apply:

```sh
kubectl apply -f /tmp/object-created-trigger.yaml
kubectl get functioneventtriggers
kubectl describe functioneventtrigger object-created-trigger
```

Expected high-level status:

```text
NAME                     PHASE   RULE ID                                      FUNCTION        AGE
object-created-trigger   Ready   ocid1.eventrule.oc1.me-jeddah-1...          managed-hello   30s
```

## IAM And Invocation

This IAM section applies to OCI Events-backed triggers with OCI service event types such as `com.oraclecloud.*`. FunctionEvent-only triggers with `functionevent.*` event types do not create OCI Events Rules and do not require `cloudevents-rules` IAM.

The operator workload identity needs permission to inspect compartments at tenancy scope, manage OCI Events rules in the target compartment, and access the Function action target. OCI Events also needs permission to invoke the target Function at delivery time. Keep both sides in mind:

- Operator workload: inspect compartments, manage Events rules, and access the Function action target.
- Events rule principal: invoke the Function action target.

Oracle documents `EVENTRULE_CREATE` under `manage cloudevents-rules`. For rules with Functions actions, Oracle's Events IAM guidance also lists access to Functions resources and virtual networking resources for actions. In OKE Workload Identity testing, `manage cloudevents-rules` was not enough by itself: OCI Events `CreateRule` failed until the workload principal also had `inspect compartments in tenancy`.

Use `functions-family` with the trailing `s`. `function-family` is not the correct Functions aggregate resource type.

Operator workload policy:

```text
Allow any-user to inspect compartments in tenancy where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to manage cloudevents-rules in compartment <events-rule-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to manage functions-family in compartment <function-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to use virtual-network-family in compartment <function-network-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
```

Events rule invocation policy:

```text
Allow any-user to use fn-invocation in compartment <function-compartment> where all {request.principal.type = 'eventrule'}
```

Use the namespace, service account, cluster OCID, and compartments from your Helm deployment and target Functions. If you use defined tags on rules, also grant the workload `use tag-namespaces` for the tag namespace. A missing workload policy commonly appears as `404 NotAuthorizedOrNotFound` on `CreateRule`. A missing invocation policy can let the rule reconcile but stop matching events from invoking the Function.

Object Storage event conditions do not require `object-family` permissions for OCI Events rule creation. The bucket still must have object events enabled, or no object create/delete events will be emitted for the rule to match.

For diagnostics only, you can temporarily prove an IAM gap by granting the workload `manage all-resources` in the target compartment, testing rule creation, and then immediately replacing it with the least-privilege statements above. Do not leave `manage all-resources` as the permanent operator policy.

See [OKE deployment](oke-deployment.md) for the broader Workload Identity policy context.

## Troubleshooting

Referenced Function not Ready:

- Check `kubectl get function <name> -o yaml`.
- Confirm `Ready=True`.
- Confirm `status.functionId` is populated.
- Managed Functions must finish OCI application/function reconciliation first.

Missing Events IAM permission:

- `FunctionEventTrigger.status.phase` becomes `Error`.
- `status.message` usually contains an OCI authorization or permission error.
- Check operator pod logs and Kubernetes events for `RuleError`.

Invalid event condition JSON:

- `condition.rawJson` must be a JSON object.
- OCI Events condition values should be scalar strings in the common single-value case.
- Arrays are valid for intentional any-of matching across multiple event types or data attribute values.
- Structured `condition.data` must be valid object-shaped YAML/JSON.
- `status.conditions[?type=="RuleReady"]` uses reason `InvalidCondition` when validation fails.

Rule created but Function not invoked:

- Confirm the rule is enabled.
- Confirm the FAAS action target is the expected Function OCID.
- Confirm OCI policy allows Events to invoke the target Function if required in your tenancy.
- Confirm the event actually occurs in the rule compartment or a child compartment.

Wrong compartment, bucket, or event type:

- OCI Events Rules match events emitted in the rule compartment and child compartments.
- Object Storage bucket filters must match the event payload shape.
- Use the exact event type, for example `com.oraclecloud.objectstorage.createobject`.
