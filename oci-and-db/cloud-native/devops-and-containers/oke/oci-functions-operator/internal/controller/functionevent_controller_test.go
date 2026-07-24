// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package controller

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"

	functionsv1alpha1 "github.com/oracle/oci-functions-operator/api/v1alpha1"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	apiruntime "k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
)

func TestFunctionEventInvokesMatchingTriggerAndCompletes(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("managed-hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	trigger := orderCreatedFunctionEventTrigger("order-created-trigger", "default", function.Name)
	event := orderCreatedFunctionEvent("order-created-abc123", "default")
	invoker := &scriptedInvoker{}
	recorder := record.NewFakeRecorder(10)

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEvent{}).
		WithObjects(function, trigger, event).
		Build()
	reconciler := &FunctionEventReconciler{Client: k8sClient, Scheme: scheme, Invoker: invoker, Recorder: recorder}

	result, err := reconcileFunctionEventResult(t, ctx, reconciler, event)
	if err != nil {
		t.Fatalf("reconcile FunctionEvent: %v", err)
	}
	if result.Requeue || result.RequeueAfter != 0 {
		t.Fatalf("result = %#v, want no requeue after success", result)
	}
	if got, want := len(invoker.requests), 1; got != want {
		t.Fatalf("invocation count = %d, want %d", got, want)
	}
	assertRequestTargets(t, invoker.requests, function.Status.FunctionID, function.Status.InvokeEndpoint)

	var body map[string]interface{}
	if err := json.Unmarshal(invoker.requests[0].Body, &body); err != nil {
		t.Fatalf("unmarshal invocation body: %v", err)
	}
	if body["eventType"] != "functionevent.order.created" || body["source"] != "checkout-service" || body["subject"] != "orders/abc123" {
		t.Fatalf("invocation body = %#v, want FunctionEvent envelope", body)
	}
	payload, ok := body["payload"].(map[string]interface{})
	if !ok || payload["orderId"] != "abc123" {
		t.Fatalf("payload = %#v, want order payload", body["payload"])
	}

	updated := getFunctionEvent(t, ctx, k8sClient, event)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventPhaseProcessed {
		t.Fatalf("phase = %q, want Processed", updated.Status.Phase)
	}
	if len(updated.Status.MatchedTriggers) != 1 || updated.Status.MatchedTriggers[0] != trigger.Name {
		t.Fatalf("matchedTriggers = %#v, want %q", updated.Status.MatchedTriggers, trigger.Name)
	}
	invocation := functionEventInvocationByTrigger(t, updated.Status.Invocations, trigger.Name)
	if invocation.Phase != functionsv1alpha1.FunctionEventInvocationPhaseSucceeded || invocation.Attempts != 1 {
		t.Fatalf("invocation status = %#v, want succeeded with one attempt", invocation)
	}
	processed := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionEventConditionProcessed)
	if processed == nil || processed.Status != metav1.ConditionTrue {
		t.Fatalf("Processed condition = %#v, want true", processed)
	}
	assertEventContains(t, drainEvents(recorder), "Normal Processed")
}

func TestFunctionEventProcessesWithNoMatchingTriggers(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	event := orderCreatedFunctionEvent("order-created-abc123", "default")
	invoker := &scriptedInvoker{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEvent{}).
		WithObjects(event).
		Build()
	reconciler := &FunctionEventReconciler{Client: k8sClient, Scheme: scheme, Invoker: invoker}

	reconcileFunctionEvent(t, ctx, reconciler, event)
	if len(invoker.requests) != 0 {
		t.Fatalf("invocation count = %d, want 0 with no matching triggers", len(invoker.requests))
	}
	updated := getFunctionEvent(t, ctx, k8sClient, event)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventPhaseProcessed {
		t.Fatalf("phase = %q, want Processed", updated.Status.Phase)
	}
	if updated.Status.Message != "No matching triggers" {
		t.Fatalf("message = %q, want No matching triggers", updated.Status.Message)
	}
}

func TestFunctionEventIgnoresOCIEventTriggers(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("managed-hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	event := orderCreatedFunctionEvent("order-created-abc123", "default")
	invoker := &scriptedInvoker{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEvent{}).
		WithObjects(function, trigger, event).
		Build()
	reconciler := &FunctionEventReconciler{Client: k8sClient, Scheme: scheme, Invoker: invoker}

	reconcileFunctionEvent(t, ctx, reconciler, event)
	if len(invoker.requests) != 0 {
		t.Fatalf("invocation count = %d, want 0 for OCI event trigger", len(invoker.requests))
	}
	updated := getFunctionEvent(t, ctx, k8sClient, event)
	if updated.Status.Message != "No matching triggers" {
		t.Fatalf("message = %q, want no matching triggers", updated.Status.Message)
	}
}

func TestFunctionEventRetriesFailedInvocationWithDelayedRequeue(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("managed-hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	trigger := orderCreatedFunctionEventTrigger("order-created-trigger", "default", function.Name)
	event := orderCreatedFunctionEvent("order-created-abc123", "default")
	invoker := &scriptedInvoker{
		failuresByIndex: map[int32][]error{
			0: {
				errors.New("oci invoke failed opc-request-id=first"),
				errors.New("oci invoke failed opc-request-id=second"),
				errors.New("oci invoke failed opc-request-id=third"),
			},
		},
	}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEvent{}).
		WithObjects(function, trigger, event).
		Build()
	reconciler := &FunctionEventReconciler{Client: k8sClient, Scheme: scheme, Invoker: invoker}

	result, err := reconcileFunctionEventResult(t, ctx, reconciler, event)
	if err != nil {
		t.Fatalf("first reconcile FunctionEvent: %v", err)
	}
	if result.RequeueAfter != functionEventRetryBackoff {
		t.Fatalf("first requeueAfter = %s, want %s", result.RequeueAfter, functionEventRetryBackoff)
	}
	first := getFunctionEvent(t, ctx, k8sClient, event)
	firstInvocation := functionEventInvocationByTrigger(t, first.Status.Invocations, trigger.Name)
	if firstInvocation.Attempts != 1 || firstInvocation.Phase != functionsv1alpha1.FunctionEventInvocationPhasePending {
		t.Fatalf("first invocation = %#v, want pending after one attempt", firstInvocation)
	}
	if strings.Contains(firstInvocation.Message, "opc-request-id") {
		t.Fatalf("first invocation message = %q, want volatile request id stripped", firstInvocation.Message)
	}

	if _, err := reconcileFunctionEventResult(t, ctx, reconciler, event); err != nil {
		t.Fatalf("second reconcile FunctionEvent: %v", err)
	}
	result, err = reconcileFunctionEventResult(t, ctx, reconciler, event)
	if err != nil {
		t.Fatalf("third reconcile FunctionEvent: %v", err)
	}
	if result.Requeue || result.RequeueAfter != 0 {
		t.Fatalf("terminal result = %#v, want no requeue", result)
	}
	updated := getFunctionEvent(t, ctx, k8sClient, event)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventPhaseFailed {
		t.Fatalf("phase = %q, want Failed", updated.Status.Phase)
	}
	invocation := functionEventInvocationByTrigger(t, updated.Status.Invocations, trigger.Name)
	if invocation.Attempts != functionEventRetryLimit || invocation.Phase != functionsv1alpha1.FunctionEventInvocationPhaseFailed {
		t.Fatalf("invocation = %#v, want failed after retry limit", invocation)
	}
}

func TestFunctionEventInvalidEventTypeFailsClearly(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	event := orderCreatedFunctionEvent("bad-event", "default")
	event.Spec.EventType = "com.example.order.created"

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEvent{}).
		WithObjects(event).
		Build()
	reconciler := &FunctionEventReconciler{Client: k8sClient, Scheme: scheme, Invoker: &scriptedInvoker{}}

	reconcileFunctionEvent(t, ctx, reconciler, event)
	updated := getFunctionEvent(t, ctx, k8sClient, event)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventPhaseFailed {
		t.Fatalf("phase = %q, want Failed", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "must start with") {
		t.Fatalf("message = %q, want prefix guidance", updated.Status.Message)
	}
}

func orderCreatedFunctionEvent(name, namespace string) *functionsv1alpha1.FunctionEvent {
	return &functionsv1alpha1.FunctionEvent{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			UID:       types.UID("event-uid-" + name),
		},
		Spec: functionsv1alpha1.FunctionEventSpec{
			EventType: "functionevent.order.created",
			Source:    "checkout-service",
			Subject:   "orders/abc123",
			Payload:   &apiruntime.RawExtension{Raw: []byte(`{"orderId":"abc123","customerId":"c-42","total":"123.45"}`)},
		},
	}
}

func orderCreatedFunctionEventTrigger(name, namespace, functionName string) *functionsv1alpha1.FunctionEventTrigger {
	enabled := true
	return &functionsv1alpha1.FunctionEventTrigger{
		ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: namespace},
		Spec: functionsv1alpha1.FunctionEventTriggerSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: functionName},
			IsEnabled:   &enabled,
			Condition: functionsv1alpha1.FunctionEventCondition{
				EventType: []string{"functionevent.order.created"},
			},
		},
	}
}

func reconcileFunctionEvent(t *testing.T, ctx context.Context, reconciler *FunctionEventReconciler, event *functionsv1alpha1.FunctionEvent) {
	t.Helper()
	if _, err := reconcileFunctionEventResult(t, ctx, reconciler, event); err != nil {
		t.Fatalf("reconcile FunctionEvent: %v", err)
	}
}

func reconcileFunctionEventResult(t *testing.T, ctx context.Context, reconciler *FunctionEventReconciler, event *functionsv1alpha1.FunctionEvent) (ctrl.Result, error) {
	t.Helper()
	return reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: event.Name, Namespace: event.Namespace}})
}

func getFunctionEvent(t *testing.T, ctx context.Context, k8sClient client.Client, event *functionsv1alpha1.FunctionEvent) functionsv1alpha1.FunctionEvent {
	t.Helper()
	var updated functionsv1alpha1.FunctionEvent
	if err := k8sClient.Get(ctx, types.NamespacedName{Name: event.Name, Namespace: event.Namespace}, &updated); err != nil {
		t.Fatalf("get FunctionEvent: %v", err)
	}
	return updated
}

func functionEventInvocationByTrigger(t *testing.T, invocations []functionsv1alpha1.FunctionEventInvocationStatus, triggerName string) functionsv1alpha1.FunctionEventInvocationStatus {
	t.Helper()
	for _, invocation := range invocations {
		if invocation.TriggerName == triggerName {
			return invocation
		}
	}
	t.Fatalf("missing invocation for trigger %q in %#v", triggerName, invocations)
	return functionsv1alpha1.FunctionEventInvocationStatus{}
}
