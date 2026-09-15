// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package controller

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"testing"

	functionsv1alpha1 "github.com/oracle/oci-functions-operator/api/v1alpha1"
	"github.com/oracle/oci-functions-operator/internal/invoker"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	apiruntime "k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
)

func TestFunctionJobReconcilerReportsMissingFunction(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "hello-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "missing"},
		},
	}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}).
		WithObjects(job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme}

	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "hello-job", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "hello-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionJobPhasePending {
		t.Fatalf("phase = %q, want %q", updated.Status.Phase, functionsv1alpha1.FunctionJobPhasePending)
	}
	condition := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionJobConditionFunctionResolved)
	if condition == nil || condition.Status != metav1.ConditionFalse || condition.Reason != "FunctionNotFound" {
		t.Fatalf("FunctionResolved condition = %#v, want FunctionNotFound false", condition)
	}
	pending := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionJobConditionPending)
	if pending == nil || pending.Status != metav1.ConditionTrue {
		t.Fatalf("Pending condition = %#v, want true", pending)
	}
}

func TestFunctionJobReconcilerInvokesPayloadsOnceAndCompletes(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "hello-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "hello"},
			Payloads: []apiruntime.RawExtension{
				rawPayload(`{"message":"one"}`),
				rawPayload(`{"message":"two"}`),
			},
			Parallelism: 2,
			RetryLimit:  1,
		},
	}
	recorder := record.NewFakeRecorder(10)
	invoker := &scriptedInvoker{}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}, &functionsv1alpha1.Function{}).
		WithObjects(function, job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme, Invoker: invoker, Recorder: recorder}

	request := ctrl.Request{NamespacedName: types.NamespacedName{Name: "hello-job", Namespace: "default"}}
	if _, err := reconciler.Reconcile(ctx, request); err != nil {
		t.Fatalf("first reconcile failed: %v", err)
	}
	if _, err := reconciler.Reconcile(ctx, request); err != nil {
		t.Fatalf("second reconcile failed: %v", err)
	}

	if got, want := len(invoker.requests), 2; got != want {
		t.Fatalf("invocation count = %d, want %d", got, want)
	}
	assertRequestIndexes(t, invoker.requests, 0, 1)
	assertRequestTargets(t, invoker.requests, function.Status.FunctionID, function.Status.InvokeEndpoint)

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "hello-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionJobPhaseSucceeded {
		t.Fatalf("phase = %q, want %q", updated.Status.Phase, functionsv1alpha1.FunctionJobPhaseSucceeded)
	}
	if updated.Status.Succeeded != 2 || updated.Status.Failed != 0 || updated.Status.Retries != 0 {
		t.Fatalf("aggregate status succeeded=%d failed=%d retries=%d, want 2/0/0", updated.Status.Succeeded, updated.Status.Failed, updated.Status.Retries)
	}
	complete := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionJobConditionComplete)
	if complete == nil || complete.Status != metav1.ConditionTrue {
		t.Fatalf("Complete condition = %#v, want true", complete)
	}
	assertEventContains(t, drainEvents(recorder), "Normal Complete")
}

func TestFunctionJobReconcilerFailsWhenReferencedFunctionIsNotReady(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	function.Spec.Mode = functionsv1alpha1.FunctionModeManaged
	function.Spec.FunctionID = ""
	function.Spec.InvokeEndpoint = ""
	function.Status.Phase = functionsv1alpha1.FunctionPhasePending
	function.Status.FunctionID = ""
	function.Status.FunctionOCID = ""
	function.Status.InvokeEndpoint = ""
	function.Status.Conditions = []metav1.Condition{{
		Type:               functionsv1alpha1.FunctionConditionReady,
		Status:             metav1.ConditionFalse,
		Reason:             "ManagedFunctionPending",
		Message:            "OCI function exists but invoke endpoint is not available yet.",
		ObservedGeneration: 1,
		LastTransitionTime: metav1.Now(),
	}}
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "pending-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "hello"},
			Payload:     &apiruntime.RawExtension{Raw: []byte(`{"message":"hello"}`)},
		},
	}
	recorder := record.NewFakeRecorder(10)
	invoker := &scriptedInvoker{}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}, &functionsv1alpha1.Function{}).
		WithObjects(function, job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme, Invoker: invoker, Recorder: recorder}

	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "pending-job", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}
	if len(invoker.requests) != 0 {
		t.Fatalf("invocation count = %d, want 0 while Function is not Ready", len(invoker.requests))
	}

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "pending-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionJobPhaseFailed {
		t.Fatalf("phase = %q, want %q", updated.Status.Phase, functionsv1alpha1.FunctionJobPhaseFailed)
	}
	if !strings.Contains(updated.Status.LastError, "not Ready") || !strings.Contains(updated.Status.LastError, "invoke endpoint is missing") {
		t.Fatalf("lastError = %q, want not Ready guidance with missing endpoint", updated.Status.LastError)
	}
	failed := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionJobConditionFailed)
	if failed == nil || failed.Status != metav1.ConditionTrue || failed.Reason != "FunctionNotReady" {
		t.Fatalf("Failed condition = %#v, want FunctionNotReady true", failed)
	}
	assertEventContains(t, drainEvents(recorder), "Warning Failed")
}

func TestFunctionJobReconcilerDoesNotInvokeWhenReadyConditionIsFalse(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	function.Spec.Mode = functionsv1alpha1.FunctionModeManaged
	function.Status.Phase = functionsv1alpha1.FunctionPhaseError
	function.Status.Message = "update OCI Functions application ocid1.fnapp.oc1.me-jeddah-1.exampleuniqueid NSG configuration: not authorized"
	function.Status.Conditions = []metav1.Condition{{
		Type:               functionsv1alpha1.FunctionConditionReady,
		Status:             metav1.ConditionFalse,
		Reason:             "ManagedFunctionError",
		Message:            function.Status.Message,
		ObservedGeneration: 1,
		LastTransitionTime: metav1.Now(),
	}}
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "blocked-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "hello"},
			Payload:     &apiruntime.RawExtension{Raw: []byte(`{"message":"hello"}`)},
		},
	}
	recorder := record.NewFakeRecorder(10)
	invoker := &scriptedInvoker{}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}, &functionsv1alpha1.Function{}).
		WithObjects(function, job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme, Invoker: invoker, Recorder: recorder}

	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "blocked-job", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}
	if len(invoker.requests) != 0 {
		t.Fatalf("invocation count = %d, want 0 while Function Ready condition is false", len(invoker.requests))
	}

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "blocked-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionJobPhaseFailed {
		t.Fatalf("phase = %q, want %q", updated.Status.Phase, functionsv1alpha1.FunctionJobPhaseFailed)
	}
	if !strings.Contains(updated.Status.LastError, "Ready=False") || !strings.Contains(updated.Status.LastError, "ManagedFunctionError") {
		t.Fatalf("lastError = %q, want Ready=false managed error guidance", updated.Status.LastError)
	}
	assertEventContains(t, drainEvents(recorder), "Warning Failed")
}

func TestFunctionJobReconcilerPropagatesOCIRequestID(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "oci-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "hello"},
			Payload:     &apiruntime.RawExtension{Raw: []byte(`{"message":"hello"}`)},
		},
	}
	invoker := &scriptedInvoker{
		responsesByIndex: map[int32]invoker.Response{
			0: {
				InvocationID: "fn-call-id",
				OCIRequestID: "opc-request-id",
				StatusCode:   202,
			},
		},
	}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}, &functionsv1alpha1.Function{}).
		WithObjects(function, job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme, Invoker: invoker}

	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "oci-job", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "oci-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if updated.Status.LastOCIRequestID != "opc-request-id" {
		t.Fatalf("last OCI request ID = %q, want opc-request-id", updated.Status.LastOCIRequestID)
	}
	status := invocationStatusByIndex(t, updated.Status.InvocationStatuses, 0)
	if status.InvocationID != "fn-call-id" || status.OCIRequestID != "opc-request-id" {
		t.Fatalf("invocation status IDs = %#v, want fn-call-id/opc-request-id", status)
	}
}

func TestFunctionJobReconcilerRecordsOCIErrorDetails(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "oci-error-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "hello"},
			Payload:     &apiruntime.RawExtension{Raw: []byte(`{"message":"hello"}`)},
			RetryLimit:  0,
		},
	}
	invoker := &metadataFailingInvoker{}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}, &functionsv1alpha1.Function{}).
		WithObjects(function, job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme, Invoker: invoker}

	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "oci-error-job", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "oci-error-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if updated.Status.LastOCIRequestID != "opc-request-id" {
		t.Fatalf("last OCI request ID = %q, want opc-request-id", updated.Status.LastOCIRequestID)
	}
	if !strings.Contains(updated.Status.LastError, "oci auth error") || !strings.Contains(updated.Status.LastError, "ociRequestId=opc-request-id") {
		t.Fatalf("lastError = %q, want OCI classification and request ID", updated.Status.LastError)
	}
	status := invocationStatusByIndex(t, updated.Status.InvocationStatuses, 0)
	if status.OCIRequestID != "opc-request-id" || status.StatusCode != 401 {
		t.Fatalf("invocation status metadata = %#v, want request ID and status", status)
	}
	if status.Error != updated.Status.LastError {
		t.Fatalf("payload error = %q, want job lastError %q", status.Error, updated.Status.LastError)
	}
}

func TestFunctionJobReconcilerAggregatesPartialFailure(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "partial-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "hello"},
			Payloads: []apiruntime.RawExtension{
				rawPayload(`{"message":"one"}`),
				rawPayload(`{"message":"two"}`),
				rawPayload(`{"message":"three"}`),
			},
			Parallelism: 3,
			RetryLimit:  0,
		},
	}
	recorder := record.NewFakeRecorder(10)
	invoker := &scriptedInvoker{
		failuresByIndex: map[int32][]error{
			1: {errors.New("boom")},
		},
	}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}, &functionsv1alpha1.Function{}).
		WithObjects(function, job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme, Invoker: invoker, Recorder: recorder}

	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "partial-job", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "partial-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionJobPhaseFailed {
		t.Fatalf("phase = %q, want %q", updated.Status.Phase, functionsv1alpha1.FunctionJobPhaseFailed)
	}
	if updated.Status.Succeeded != 2 || updated.Status.Failed != 1 {
		t.Fatalf("aggregate status succeeded=%d failed=%d, want 2/1", updated.Status.Succeeded, updated.Status.Failed)
	}
	failedStatus := invocationStatusByIndex(t, updated.Status.InvocationStatuses, 1)
	if failedStatus.Phase != functionsv1alpha1.InvocationPhaseFailed || failedStatus.Attempts != 1 {
		t.Fatalf("failed payload status = %#v, want failed after one attempt", failedStatus)
	}
	failed := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionJobConditionFailed)
	if failed == nil || failed.Status != metav1.ConditionTrue {
		t.Fatalf("Failed condition = %#v, want true", failed)
	}
	events := drainEvents(recorder)
	assertEventContains(t, events, "Warning InvocationFailed")
	assertEventContains(t, events, "Warning Failed")
}

func TestFunctionJobReconcilerExhaustsRetryLimit(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "retry-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "hello"},
			Payloads: []apiruntime.RawExtension{
				rawPayload(`{"message":"retry"}`),
			},
			Parallelism: 1,
			RetryLimit:  2,
		},
	}
	recorder := record.NewFakeRecorder(10)
	invoker := &scriptedInvoker{
		failuresByIndex: map[int32][]error{
			0: {
				errors.New("first failure"),
				errors.New("second failure"),
				errors.New("third failure"),
			},
		},
	}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}, &functionsv1alpha1.Function{}).
		WithObjects(function, job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme, Invoker: invoker, Recorder: recorder}

	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "retry-job", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "retry-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if got, want := len(invoker.requests), 3; got != want {
		t.Fatalf("invocation attempts = %d, want %d", got, want)
	}
	status := invocationStatusByIndex(t, updated.Status.InvocationStatuses, 0)
	if status.Phase != functionsv1alpha1.InvocationPhaseFailed || status.Attempts != 3 {
		t.Fatalf("payload status = %#v, want failed after three attempts", status)
	}
	if updated.Status.Retries != 2 {
		t.Fatalf("retries = %d, want 2", updated.Status.Retries)
	}
	assertEventContains(t, drainEvents(recorder), "Warning InvocationFailed")
}

func TestFunctionJobReconcilerRequeuesAndDoesNotReinvokeSucceededPayloads(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyFunction("hello", "default", "ocid1.fnfunc.oc1.iad.exampleuniqueid")
	job := &functionsv1alpha1.FunctionJob{
		ObjectMeta: metav1.ObjectMeta{Name: "bounded-job", Namespace: "default"},
		Spec: functionsv1alpha1.FunctionJobSpec{
			FunctionRef: functionsv1alpha1.FunctionReference{Name: "hello"},
			Payloads: []apiruntime.RawExtension{
				rawPayload(`{"message":"one"}`),
				rawPayload(`{"message":"two"}`),
				rawPayload(`{"message":"three"}`),
			},
			Parallelism: 1,
			RetryLimit:  0,
		},
	}
	recorder := record.NewFakeRecorder(10)
	invoker := &scriptedInvoker{}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionJob{}, &functionsv1alpha1.Function{}).
		WithObjects(function, job).
		Build()
	reconciler := &FunctionJobReconciler{Client: client, Scheme: scheme, Invoker: invoker, Recorder: recorder}
	request := ctrl.Request{NamespacedName: types.NamespacedName{Name: "bounded-job", Namespace: "default"}}

	result, err := reconciler.Reconcile(ctx, request)
	if err != nil {
		t.Fatalf("first reconcile failed: %v", err)
	}
	if !result.Requeue {
		t.Fatalf("first reconcile requeue = false, want true")
	}
	assertRequestIndexes(t, invoker.requests, 0)

	result, err = reconciler.Reconcile(ctx, request)
	if err != nil {
		t.Fatalf("second reconcile failed: %v", err)
	}
	if !result.Requeue {
		t.Fatalf("second reconcile requeue = false, want true")
	}
	assertRequestIndexes(t, invoker.requests, 0, 1)

	result, err = reconciler.Reconcile(ctx, request)
	if err != nil {
		t.Fatalf("third reconcile failed: %v", err)
	}
	if result.Requeue {
		t.Fatalf("third reconcile requeue = true, want false")
	}
	assertRequestIndexes(t, invoker.requests, 0, 1, 2)

	if _, err := reconciler.Reconcile(ctx, request); err != nil {
		t.Fatalf("fourth reconcile failed: %v", err)
	}
	assertRequestIndexes(t, invoker.requests, 0, 1, 2)

	var updated functionsv1alpha1.FunctionJob
	if err := client.Get(ctx, types.NamespacedName{Name: "bounded-job", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionJob: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionJobPhaseSucceeded {
		t.Fatalf("phase = %q, want %q", updated.Status.Phase, functionsv1alpha1.FunctionJobPhaseSucceeded)
	}
	if updated.Status.Succeeded != 3 || updated.Status.Failed != 0 {
		t.Fatalf("aggregate status succeeded=%d failed=%d, want 3/0", updated.Status.Succeeded, updated.Status.Failed)
	}
}

func rawPayload(value string) apiruntime.RawExtension {
	return apiruntime.RawExtension{Raw: []byte(value)}
}

func readyFunction(name, namespace, ocid string) *functionsv1alpha1.Function {
	now := metav1.Now()
	invokeEndpoint := "https://functions.us-ashburn-1.oci.oraclecloud.com"
	return &functionsv1alpha1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: namespace},
		Spec: functionsv1alpha1.FunctionSpec{
			Mode:           functionsv1alpha1.FunctionModeExisting,
			FunctionID:     ocid,
			InvokeEndpoint: invokeEndpoint,
		},
		Status: functionsv1alpha1.FunctionStatus{
			Phase:          functionsv1alpha1.FunctionPhaseReady,
			FunctionOCID:   ocid,
			FunctionID:     ocid,
			InvokeEndpoint: invokeEndpoint,
			Conditions: []metav1.Condition{{
				Type:               functionsv1alpha1.FunctionConditionReady,
				Status:             metav1.ConditionTrue,
				Reason:             "ExistingFunctionResolved",
				Message:            "Existing OCI Function OCID and invoke endpoint are configured.",
				ObservedGeneration: 1,
				LastTransitionTime: now,
			}},
		},
	}
}

type scriptedInvoker struct {
	requests         []invoker.Request
	failuresByIndex  map[int32][]error
	responsesByIndex map[int32]invoker.Response
}

func (s *scriptedInvoker) Invoke(_ context.Context, request invoker.Request) (invoker.Response, error) {
	s.requests = append(s.requests, request)
	failures := s.failuresByIndex[request.Index]
	if len(failures) > 0 {
		err := failures[0]
		s.failuresByIndex[request.Index] = failures[1:]
		if err != nil {
			return invoker.Response{}, err
		}
	}
	if response, ok := s.responsesByIndex[request.Index]; ok {
		return response, nil
	}
	return invoker.Response{
		InvocationID: fmt.Sprintf("invoke-%d", request.Index),
		StatusCode:   202,
	}, nil
}

type metadataFailingInvoker struct{}

func (m *metadataFailingInvoker) Invoke(context.Context, invoker.Request) (invoker.Response, error) {
	return invoker.Response{
		OCIRequestID: "opc-request-id",
		StatusCode:   401,
	}, errors.New("oci auth error invoking function ocid1.fnfunc.oc1.iad.exampleuniqueid status=401 ociRequestId=opc-request-id: not authenticated")
}

func assertRequestIndexes(t *testing.T, requests []invoker.Request, indexes ...int32) {
	t.Helper()

	if len(requests) != len(indexes) {
		t.Fatalf("request count = %d, want %d", len(requests), len(indexes))
	}
	for i, want := range indexes {
		if requests[i].Index != want {
			t.Fatalf("request[%d].Index = %d, want %d", i, requests[i].Index, want)
		}
	}
}

func assertRequestTargets(t *testing.T, requests []invoker.Request, functionID, invokeEndpoint string) {
	t.Helper()

	for i, request := range requests {
		if request.Target.FunctionOCID != functionID {
			t.Fatalf("request[%d] function OCID = %q, want %q", i, request.Target.FunctionOCID, functionID)
		}
		if request.Target.InvokeEndpoint != invokeEndpoint {
			t.Fatalf("request[%d] invoke endpoint = %q, want %q", i, request.Target.InvokeEndpoint, invokeEndpoint)
		}
	}
}

func invocationStatusByIndex(t *testing.T, statuses []functionsv1alpha1.FunctionJobInvocationStatus, index int32) functionsv1alpha1.FunctionJobInvocationStatus {
	t.Helper()

	for _, status := range statuses {
		if status.Index == index {
			return status
		}
	}
	t.Fatalf("missing invocation status for index %d", index)
	return functionsv1alpha1.FunctionJobInvocationStatus{}
}

func drainEvents(recorder *record.FakeRecorder) []string {
	events := []string{}
	for {
		select {
		case event := <-recorder.Events:
			events = append(events, event)
		default:
			return events
		}
	}
}

func assertEventContains(t *testing.T, events []string, want string) {
	t.Helper()

	for _, event := range events {
		if strings.Contains(event, want) {
			return
		}
	}
	t.Fatalf("events %q do not contain %q", events, want)
}
