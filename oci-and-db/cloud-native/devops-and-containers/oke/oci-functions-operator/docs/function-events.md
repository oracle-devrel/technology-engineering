# Function Events

`FunctionEvent` is the Kubernetes-native event source for this operator. An application creates a namespaced `FunctionEvent` object, and the operator invokes same-namespace `FunctionEventTrigger` objects whose `condition.eventType` contains the event's `spec.eventType`.

This is separate from OCI Events:

- OCI service event types such as `com.oraclecloud.objectstorage.createobject` are backed by OCI Events Rules and require `cloudevents-rules` IAM.
- Kubernetes-native event types use the reserved `functionevent.` prefix and are backed by `FunctionEvent` CRDs. They invoke directly through the operator's existing Function invocation path.

Do not mix OCI event types and `functionevent.*` values in one `FunctionEventTrigger`.

## Event Shape

```yaml
apiVersion: functions.oci.oracle.com/v1alpha1
kind: FunctionEvent
metadata:
  name: order-created-abc123
  namespace: default
spec:
  eventType: functionevent.order.created
  source: checkout-service
  subject: orders/abc123
  payload:
    orderId: abc123
    customerId: c-42
    total: "123.45"
```

`spec.eventType` must start with `functionevent.`. `source` and `subject` are informational routing context for the invoked Function. `payload` is carried in the invocation envelope.

The invoked Function receives JSON shaped like:

```json
{
  "id": "event-uid-or-spec-id",
  "eventType": "functionevent.order.created",
  "source": "checkout-service",
  "subject": "orders/abc123",
  "payload": {
    "orderId": "abc123",
    "customerId": "c-42",
    "total": "123.45"
  }
}
```

Set `spec.id` when the emitter has its own idempotency key. Otherwise the controller uses `metadata.uid` in the invocation envelope. Internally, the controller tracks each invocation by `FunctionEvent.metadata.uid` plus trigger name so retries do not duplicate already-succeeded trigger invocations.

## Trigger Shape

FunctionEvent triggers are lightweight. They do not need `compartmentId`, `displayName`, or `deletionPolicy` because no OCI Events Rule is created.

```yaml
apiVersion: functions.oci.oracle.com/v1alpha1
kind: FunctionEventTrigger
metadata:
  name: order-created-trigger
  namespace: default
spec:
  functionRef:
    name: managed-hello
  isEnabled: true
  condition:
    eventType:
    - functionevent.order.created
```

The referenced `Function` must exist in the same namespace and be `Ready=True` before the event can be invoked. If the Function is not ready, the `FunctionEvent` stays `Processing` and retries later.

## Run The Sample

Create or apply a `Function` first. The sample trigger expects a `Function` named `managed-hello` in namespace `default`.

```sh
kubectl apply -f config/samples/functions_v1alpha1_functioneventtrigger_order_created.yaml
kubectl apply -f config/samples/functions_v1alpha1_functionevent_order_created.yaml
```

Check status:

```sh
kubectl get functionevents
kubectl describe functionevent order-created-abc123
```

Expected high-level output:

```text
NAME                   PHASE       EVENT TYPE                    MATCHED                   AGE
order-created-abc123   Processed   functionevent.order.created   [order-created-trigger]   10s
```

If no triggers match, the event is still marked `Processed` with message `No matching triggers`.

## Emit From Code

Any Kubernetes client can create a `FunctionEvent`. With the Go client, using the dynamic client keeps the example short:

```go
gvr := schema.GroupVersionResource{
    Group:    "functions.oci.oracle.com",
    Version:  "v1alpha1",
    Resource: "functionevents",
}

event := &unstructured.Unstructured{Object: map[string]interface{}{
    "apiVersion": "functions.oci.oracle.com/v1alpha1",
    "kind":       "FunctionEvent",
    "metadata": map[string]interface{}{
        "name":      "order-created-abc123",
        "namespace": "default",
    },
    "spec": map[string]interface{}{
        "eventType": "functionevent.order.created",
        "source":    "checkout-service",
        "subject":   "orders/abc123",
        "payload": map[string]interface{}{
            "orderId":    "abc123",
            "customerId": "c-42",
            "total":      "123.45",
        },
    },
}}

_, err := dynamicClient.Resource(gvr).Namespace("default").Create(ctx, event, metav1.CreateOptions{})
```

## IAM

`FunctionEvent` does not create or update OCI Events Rules, so the event source does not require `cloudevents-rules` IAM.

The operator still invokes OCI Functions. In OCI mode on OKE, the workload identity policy must allow the existing Function invocation path, and managed Functions still need the usual Functions, network, OCIR image, and Workload Identity setup documented in [OKE deployment](oke-deployment.md).

## Limits

- `condition.source` is not implemented.
- `FunctionEvent` matching only uses `FunctionEventTrigger.spec.condition.eventType`.
- OCI event types and `functionevent.*` event types cannot be mixed in a single trigger.
- There is no schedule, watch trigger, queue trigger, or workflow engine in this feature.
