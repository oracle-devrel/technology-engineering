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
	"github.com/oracle/oci-functions-operator/internal/eventtrigger"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/client/interceptor"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/event"
)

func TestFunctionEventTriggerCreatesRuleAfterFunctionReady(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	manager := &fakeEventRuleManager{}
	recorder := record.NewFakeRecorder(20)

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager, Recorder: recorder}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 1 {
		t.Fatalf("createCalls = %d, want 1", manager.createCalls)
	}
	if len(manager.desired) != 1 {
		t.Fatalf("desired calls = %d, want 1", len(manager.desired))
	}
	desired := manager.desired[0]
	if desired.FunctionID != function.Status.FunctionID {
		t.Fatalf("FunctionID = %q, want %q", desired.FunctionID, function.Status.FunctionID)
	}
	if !strings.Contains(desired.ConditionJSON, "com.oraclecloud.objectstorage.createobject") || !strings.Contains(desired.ConditionJSON, "my-bucket") {
		t.Fatalf("ConditionJSON = %s, want object-created bucket condition", desired.ConditionJSON)
	}

	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhaseReady {
		t.Fatalf("phase = %q, want Ready", updated.Status.Phase)
	}
	if updated.Status.RuleID == "" {
		t.Fatalf("ruleId is empty, want OCI Events rule OCID")
	}
	condition := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionEventTriggerConditionRuleReady)
	if condition == nil || condition.Status != metav1.ConditionTrue {
		t.Fatalf("RuleReady condition = %#v, want true", condition)
	}
	assertEventContains(t, drainEvents(recorder), "Normal RuleCreated")
}

func TestFunctionEventTriggerFunctionEventRouteDoesNotCreateOCIRule(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	trigger := orderCreatedFunctionEventTrigger("order-created-trigger", "default", "managed-hello")
	manager := &fakeEventRuleManager{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager}

	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 0 || len(manager.desired) != 0 {
		t.Fatalf("OCI rule calls = create:%d desired:%d, want none for FunctionEvent route", manager.createCalls, len(manager.desired))
	}
	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhaseReady {
		t.Fatalf("phase = %q, want Ready", updated.Status.Phase)
	}
	if updated.Status.RuleID != "" {
		t.Fatalf("ruleId = %q, want empty for FunctionEvent route", updated.Status.RuleID)
	}
	if controllerutil.ContainsFinalizer(&updated, functionEventTriggerFinalizer) {
		t.Fatalf("finalizers = %#v, want no OCI Events finalizer for FunctionEvent route", updated.Finalizers)
	}
}

func TestFunctionEventTriggerOCITriggerMissingRuleFieldsFailsClearly(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	trigger.Spec.CompartmentID = ""
	trigger.Spec.DisplayName = ""
	manager := &fakeEventRuleManager{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager}

	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 0 {
		t.Fatalf("createCalls = %d, want 0 for invalid OCI Events trigger", manager.createCalls)
	}
	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhaseError {
		t.Fatalf("phase = %q, want Error", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "spec.compartmentId") || !strings.Contains(updated.Status.Message, "spec.displayName") {
		t.Fatalf("message = %q, want missing OCI Events fields", updated.Status.Message)
	}
}

func TestFunctionEventTriggerRejectsMixedFunctionEventAndOCIEventTypes(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	trigger := orderCreatedFunctionEventTrigger("mixed-trigger", "default", "managed-hello")
	trigger.Spec.Condition.EventType = append(trigger.Spec.Condition.EventType, "com.oraclecloud.objectstorage.createobject")
	manager := &fakeEventRuleManager{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager}

	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 0 {
		t.Fatalf("createCalls = %d, want 0 for mixed trigger", manager.createCalls)
	}
	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhaseError {
		t.Fatalf("phase = %q, want Error", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "cannot mix") {
		t.Fatalf("message = %q, want mixed event type guidance", updated.Status.Message)
	}
}

func TestFunctionEventTriggerWaitsWhenFunctionNotFound(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	trigger := objectCreatedTrigger("object-created-trigger", "default", "missing")
	manager := &fakeEventRuleManager{}
	recorder := record.NewFakeRecorder(20)

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager, Recorder: recorder}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 0 {
		t.Fatalf("createCalls = %d, want 0 while Function is missing", manager.createCalls)
	}
	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhasePending {
		t.Fatalf("phase = %q, want Pending", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "Waiting for Function") {
		t.Fatalf("message = %q, want waiting for Function", updated.Status.Message)
	}
	assertEventContains(t, drainEvents(recorder), "Normal WaitingForFunction")
}

func TestFunctionEventTriggerWaitsWhenFunctionNotReady(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := pendingEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	manager := &fakeEventRuleManager{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 0 {
		t.Fatalf("createCalls = %d, want 0 while Function is not Ready", manager.createCalls)
	}
	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhasePending {
		t.Fatalf("phase = %q, want Pending", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "status.functionId") {
		t.Fatalf("message = %q, want status.functionId guidance", updated.Status.Message)
	}
}

func TestFunctionEventTriggerWaitsWhenFunctionIDMissing(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	function.Status.FunctionID = ""
	function.Status.FunctionOCID = ""
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	manager := &fakeEventRuleManager{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 0 {
		t.Fatalf("createCalls = %d, want 0 while Function status.functionId is empty", manager.createCalls)
	}
	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhasePending {
		t.Fatalf("phase = %q, want Pending", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "status.functionId") {
		t.Fatalf("message = %q, want status.functionId guidance", updated.Status.Message)
	}
}

func TestFunctionEventTriggerUpdatesRuleDrift(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	trigger.Status.RuleID = "ocid1.eventrule.oc1.me-jeddah-1.existing"
	trigger.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhaseReady
	trigger.Spec.DisplayName = "object-created-trigger-v2"
	manager := &fakeEventRuleManager{existingRuleID: trigger.Status.RuleID, emitUpdate: true}
	recorder := record.NewFakeRecorder(20)

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager, Recorder: recorder}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if len(manager.desired) != 1 {
		t.Fatalf("desired calls = %d, want 1", len(manager.desired))
	}
	if manager.desired[0].DisplayName != "object-created-trigger-v2" {
		t.Fatalf("displayName = %q, want updated name", manager.desired[0].DisplayName)
	}
	assertEventContains(t, drainEvents(recorder), "Normal RuleUpdated")
}

func TestFunctionEventTriggerDeletesRuleOnTriggerDeletionWithDeletePolicy(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	trigger := objectCreatedTrigger("object-created-trigger", "default", "managed-hello")
	trigger.Finalizers = []string{functionEventTriggerFinalizer}
	trigger.Status.RuleID = "ocid1.eventrule.oc1.me-jeddah-1.existing"
	manager := &fakeEventRuleManager{}
	recorder := record.NewFakeRecorder(20)

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager, Recorder: recorder}

	if err := k8sClient.Delete(ctx, trigger); err != nil {
		t.Fatalf("delete trigger: %v", err)
	}
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.deleteCalls != 1 {
		t.Fatalf("deleteCalls = %d, want 1", manager.deleteCalls)
	}
	if manager.deletedRuleID != trigger.Status.RuleID {
		t.Fatalf("deletedRuleID = %q, want %q", manager.deletedRuleID, trigger.Status.RuleID)
	}
	assertEventContains(t, drainEvents(recorder), "Normal RuleDeleted")
}

func TestFunctionEventTriggerRetainsRuleWithRetainPolicy(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	trigger := objectCreatedTrigger("object-created-trigger", "default", "managed-hello")
	trigger.Spec.DeletionPolicy = functionsv1alpha1.FunctionEventTriggerDeletionPolicyRetain
	trigger.Finalizers = []string{functionEventTriggerFinalizer}
	trigger.Status.RuleID = "ocid1.eventrule.oc1.me-jeddah-1.existing"
	manager := &fakeEventRuleManager{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager}

	if err := k8sClient.Delete(ctx, trigger); err != nil {
		t.Fatalf("delete trigger: %v", err)
	}
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.deleteCalls != 0 {
		t.Fatalf("deleteCalls = %d, want 0 for Retain policy", manager.deleteCalls)
	}
}

func TestFunctionEventTriggerInvalidConditionFailsClearly(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	trigger.Spec.Condition = functionsv1alpha1.FunctionEventCondition{RawJSON: `{"eventType":`}
	manager := &fakeEventRuleManager{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 0 {
		t.Fatalf("createCalls = %d, want 0 for invalid condition", manager.createCalls)
	}
	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhaseError {
		t.Fatalf("phase = %q, want Error", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "Invalid OCI Events condition") {
		t.Fatalf("message = %q, want invalid condition guidance", updated.Status.Message)
	}
	condition := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionEventTriggerConditionRuleReady)
	if condition == nil || condition.Reason != "InvalidCondition" {
		t.Fatalf("RuleReady condition = %#v, want InvalidCondition", condition)
	}
}

func TestFunctionEventTriggerRendersObjectStorageCreateObjectCondition(t *testing.T) {
	condition := functionsv1alpha1.FunctionEventCondition{
		EventType: []string{"com.oraclecloud.objectstorage.createobject"},
		Data:      rawExtension(`{"additionalDetails":{"bucketName":["bucket-20260624-1058"]}}`),
	}

	conditionJSON, err := conditionJSONFromSpec(condition)
	if err != nil {
		t.Fatalf("conditionJSONFromSpec: %v", err)
	}
	want := `{"eventType":"com.oraclecloud.objectstorage.createobject","data":{"additionalDetails":{"bucketName":"bucket-20260624-1058"}}}`
	if conditionJSON != want {
		t.Fatalf("conditionJSON = %s, want %s", conditionJSON, want)
	}
}

func TestFunctionEventTriggerRendersMultipleStructuredEventTypes(t *testing.T) {
	conditionJSON, err := conditionJSONFromSpec(functionsv1alpha1.FunctionEventCondition{
		EventType: []string{
			"com.oraclecloud.objectstorage.createobject",
			"com.oraclecloud.objectstorage.deleteobject",
		},
	})
	if err != nil {
		t.Fatalf("conditionJSONFromSpec: %v", err)
	}
	want := `{"eventType":["com.oraclecloud.objectstorage.createobject","com.oraclecloud.objectstorage.deleteobject"]}`
	if conditionJSON != want {
		t.Fatalf("conditionJSON = %s, want %s", conditionJSON, want)
	}
}

func TestFunctionEventTriggerRendersMultipleStructuredDataValues(t *testing.T) {
	conditionJSON, err := conditionJSONFromSpec(functionsv1alpha1.FunctionEventCondition{
		EventType: []string{"com.oraclecloud.objectstorage.createobject"},
		Data:      rawExtension(`{"additionalDetails":{"bucketName":["bucket-a","bucket-b"]}}`),
	})
	if err != nil {
		t.Fatalf("conditionJSONFromSpec: %v", err)
	}
	want := `{"eventType":"com.oraclecloud.objectstorage.createobject","data":{"additionalDetails":{"bucketName":["bucket-a","bucket-b"]}}}`
	if conditionJSON != want {
		t.Fatalf("conditionJSON = %s, want %s", conditionJSON, want)
	}
}

func TestFunctionEventTriggerAcceptsArrayRawConditionValues(t *testing.T) {
	conditionJSON, err := conditionJSONFromSpec(functionsv1alpha1.FunctionEventCondition{
		RawJSON: `{"eventType":["com.oraclecloud.objectstorage.createobject"],"data":{"additionalDetails":{"bucketName":["bucket-20260624-1058"]}}}`,
	})
	if err != nil {
		t.Fatalf("conditionJSONFromSpec: %v", err)
	}
	want := `{"data":{"additionalDetails":{"bucketName":["bucket-20260624-1058"]}},"eventType":["com.oraclecloud.objectstorage.createobject"]}`
	if conditionJSON != want {
		t.Fatalf("conditionJSON = %s, want %s", conditionJSON, want)
	}
}

func TestFunctionEventTriggerCreateRuleFailureReturnsDelayedRequeue(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	manager := &fakeEventRuleManager{ensureErr: errors.New("404 NotAuthorizedOrNotFound: CreateRule not authorized")}
	recorder := record.NewFakeRecorder(20)

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager, Recorder: recorder}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	result, err := reconcileEventTriggerResult(t, ctx, reconciler, trigger)
	if err != nil {
		t.Fatalf("reconcile returned error = %v, want delayed requeue without raw error", err)
	}
	if result.RequeueAfter != functionEventTriggerOCIFailureRequeue {
		t.Fatalf("RequeueAfter = %s, want %s", result.RequeueAfter, functionEventTriggerOCIFailureRequeue)
	}

	updated := getEventTrigger(t, ctx, k8sClient, trigger)
	if updated.Status.Phase != functionsv1alpha1.FunctionEventTriggerPhaseError {
		t.Fatalf("phase = %q, want Error", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "NotAuthorizedOrNotFound") {
		t.Fatalf("message = %q, want OCI authorization error", updated.Status.Message)
	}
	assertEventContains(t, drainEvents(recorder), "Warning RuleError")
}

func TestFunctionEventTriggerCreateRuleFailureDoesNotRewriteUnchangedStatusOrEvents(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	manager := &fakeEventRuleManager{ensureErr: errors.New("404 NotAuthorizedOrNotFound: CreateRule not authorized")}
	recorder := record.NewFakeRecorder(20)
	statusUpdates := 0

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithInterceptorFuncs(interceptor.Funcs{
			SubResourceUpdate: func(ctx context.Context, c client.Client, subResourceName string, obj client.Object, opts ...client.SubResourceUpdateOption) error {
				if subResourceName == "status" {
					if _, ok := obj.(*functionsv1alpha1.FunctionEventTrigger); ok {
						statusUpdates++
					}
				}
				return c.Status().Update(ctx, obj, opts...)
			},
		}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager, Recorder: recorder}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)
	if statusUpdates != 1 {
		t.Fatalf("status updates after first CreateRule failure = %d, want 1", statusUpdates)
	}
	firstFailure := getEventTrigger(t, ctx, k8sClient, trigger)
	firstRuleReady := meta.FindStatusCondition(firstFailure.Status.Conditions, functionsv1alpha1.FunctionEventTriggerConditionRuleReady)
	if firstFailure.Status.LastSyncTime != nil {
		t.Fatalf("lastSyncTime = %s after first failure, want nil", firstFailure.Status.LastSyncTime)
	}
	if firstRuleReady == nil {
		t.Fatalf("RuleReady condition is nil after first failure")
	}
	assertEventContains(t, drainEvents(recorder), "Warning RuleError")

	result, err := reconcileEventTriggerResult(t, ctx, reconciler, trigger)
	if err != nil {
		t.Fatalf("reconcile returned error = %v, want delayed requeue without raw error", err)
	}
	if result.RequeueAfter != functionEventTriggerOCIFailureRequeue {
		t.Fatalf("RequeueAfter = %s, want %s", result.RequeueAfter, functionEventTriggerOCIFailureRequeue)
	}

	secondFailure := getEventTrigger(t, ctx, k8sClient, trigger)
	secondRuleReady := meta.FindStatusCondition(secondFailure.Status.Conditions, functionsv1alpha1.FunctionEventTriggerConditionRuleReady)
	if statusUpdates != 1 {
		t.Fatalf("status updates after repeated unchanged failure = %d, want 1", statusUpdates)
	}
	if secondFailure.Status.LastSyncTime != nil {
		t.Fatalf("lastSyncTime = %s after repeated failure, want nil", secondFailure.Status.LastSyncTime)
	}
	if secondRuleReady == nil {
		t.Fatalf("RuleReady condition is nil after repeated failure")
	}
	if !firstRuleReady.LastTransitionTime.Time.Equal(secondRuleReady.LastTransitionTime.Time) {
		t.Fatalf("RuleReady LastTransitionTime changed from %s to %s for unchanged failure", firstRuleReady.LastTransitionTime, secondRuleReady.LastTransitionTime)
	}
	if events := drainEvents(recorder); len(events) != 0 {
		t.Fatalf("events after repeated unchanged failure = %q, want none", events)
	}
	if len(manager.desired) != 2 {
		t.Fatalf("desired calls = %d, want 2 after two rule sync attempts", len(manager.desired))
	}
}

func TestFunctionEventTriggerCreateRuleFailureNormalizesVolatileOCIError(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	manager := &fakeEventRuleManager{ensureErrs: []error{
		errors.New(volatileCreateRuleServiceError("opc-request-id-one", "2026-06-24 10:58:01 +0000 UTC")),
		errors.New(volatileCreateRuleServiceError("opc-request-id-two", "2026-06-24 10:58:31 +0000 UTC")),
	}}
	recorder := record.NewFakeRecorder(20)
	statusUpdates := 0

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithInterceptorFuncs(interceptor.Funcs{
			SubResourceUpdate: func(ctx context.Context, c client.Client, subResourceName string, obj client.Object, opts ...client.SubResourceUpdateOption) error {
				if subResourceName == "status" {
					if _, ok := obj.(*functionsv1alpha1.FunctionEventTrigger); ok {
						statusUpdates++
					}
				}
				return c.Status().Update(ctx, obj, opts...)
			},
		}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager, Recorder: recorder}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	result, err := reconcileEventTriggerResult(t, ctx, reconciler, trigger)
	if err != nil {
		t.Fatalf("first reconcile returned error = %v, want delayed requeue without raw error", err)
	}
	if result.RequeueAfter != functionEventTriggerOCIFailureRequeue {
		t.Fatalf("first RequeueAfter = %s, want %s", result.RequeueAfter, functionEventTriggerOCIFailureRequeue)
	}
	firstFailure := getEventTrigger(t, ctx, k8sClient, trigger)
	wantMessage := "CreateRule failed: 404 NotAuthorizedOrNotFound: Authorization failed or requested resource not found."
	if firstFailure.Status.Message != wantMessage {
		t.Fatalf("first status message = %q, want %q", firstFailure.Status.Message, wantMessage)
	}
	if strings.Contains(firstFailure.Status.Message, "opc-request-id-one") || strings.Contains(firstFailure.Status.Message, "Timestamp") || strings.Contains(firstFailure.Status.Message, "Troubleshooting") {
		t.Fatalf("first status message includes volatile SDK text: %q", firstFailure.Status.Message)
	}
	assertEventContains(t, drainEvents(recorder), "Warning RuleError "+wantMessage)
	if statusUpdates != 1 {
		t.Fatalf("status updates after first volatile CreateRule failure = %d, want 1", statusUpdates)
	}

	result, err = reconcileEventTriggerResult(t, ctx, reconciler, trigger)
	if err != nil {
		t.Fatalf("second reconcile returned error = %v, want delayed requeue without raw error", err)
	}
	if result.RequeueAfter != functionEventTriggerOCIFailureRequeue {
		t.Fatalf("second RequeueAfter = %s, want %s", result.RequeueAfter, functionEventTriggerOCIFailureRequeue)
	}
	secondFailure := getEventTrigger(t, ctx, k8sClient, trigger)
	if secondFailure.Status.Message != wantMessage {
		t.Fatalf("second status message = %q, want %q", secondFailure.Status.Message, wantMessage)
	}
	if statusUpdates != 1 {
		t.Fatalf("status updates after second volatile CreateRule failure = %d, want 1", statusUpdates)
	}
	if events := drainEvents(recorder); len(events) != 0 {
		t.Fatalf("events after second normalized CreateRule failure = %q, want none", events)
	}
}

func TestFunctionEventTriggerPrimaryPredicateIgnoresStatusOnlyUpdate(t *testing.T) {
	oldTrigger := objectCreatedTrigger("object-created-trigger", "default", "managed-hello")
	oldTrigger.Generation = 2
	oldTrigger.ResourceVersion = "10"
	oldTrigger.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhasePending
	oldTrigger.Status.Message = "waiting"

	newTrigger := oldTrigger.DeepCopy()
	newTrigger.ResourceVersion = "11"
	newTrigger.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhaseError
	newTrigger.Status.Message = "create OCI Events rule failed"

	if functionEventTriggerPrimaryPredicate().Update(event.UpdateEvent{ObjectOld: oldTrigger, ObjectNew: newTrigger}) {
		t.Fatalf("status-only update passed primary predicate, want it filtered")
	}

	specChanged := newTrigger.DeepCopy()
	specChanged.Generation = 3
	if !functionEventTriggerPrimaryPredicate().Update(event.UpdateEvent{ObjectOld: newTrigger, ObjectNew: specChanged}) {
		t.Fatalf("generation update was filtered, want it to trigger reconcile")
	}

	deleting := newTrigger.DeepCopy()
	deletionTime := metav1.Now()
	deleting.SetDeletionTimestamp(&deletionTime)
	if !functionEventTriggerPrimaryPredicate().Update(event.UpdateEvent{ObjectOld: newTrigger, ObjectNew: deleting}) {
		t.Fatalf("deletion timestamp update was filtered, want finalizer cleanup to trigger reconcile")
	}
}

func TestFunctionEventTriggerFunctionWatchMapsReferencingTriggers(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	referencing := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	other := objectCreatedTrigger("other-trigger", "default", "other-function")

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, referencing, other).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme}

	requests := reconciler.functionToEventTriggerRequests(ctx, function)
	if len(requests) != 1 {
		t.Fatalf("requests = %v, want one referencing trigger", requests)
	}
	want := types.NamespacedName{Name: referencing.Name, Namespace: referencing.Namespace}
	if requests[0].NamespacedName != want {
		t.Fatalf("request = %s, want %s", requests[0].NamespacedName, want)
	}
}

func TestFunctionEventTriggerDoesNotDuplicateRuleOnRepeatedReconcile(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	function := readyEventTriggerFunction("managed-hello", "default")
	trigger := objectCreatedTrigger("object-created-trigger", "default", function.Name)
	manager := &fakeEventRuleManager{}

	k8sClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionEventTrigger{}).
		WithObjects(function, trigger).
		Build()
	reconciler := &FunctionEventTriggerReconciler{Client: k8sClient, Scheme: scheme, Manager: manager}

	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)
	reconcileEventTrigger(t, ctx, reconciler, trigger)

	if manager.createCalls != 1 {
		t.Fatalf("createCalls = %d, want 1 after repeated reconcile", manager.createCalls)
	}
	if len(manager.desired) != 2 {
		t.Fatalf("desired calls = %d, want 2 after repeated reconcile post-finalizer", len(manager.desired))
	}
}

func objectCreatedTrigger(name, namespace, functionName string) *functionsv1alpha1.FunctionEventTrigger {
	enabled := true
	return &functionsv1alpha1.FunctionEventTrigger{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			UID:       types.UID("uid-" + name),
		},
		Spec: functionsv1alpha1.FunctionEventTriggerSpec{
			FunctionRef:   functionsv1alpha1.FunctionReference{Name: functionName},
			CompartmentID: "ocid1.compartment.oc1..exampleuniqueid",
			DisplayName:   name,
			Description:   "Invoke managed-hello when objects are created",
			IsEnabled:     &enabled,
			Condition: functionsv1alpha1.FunctionEventCondition{
				EventType: []string{"com.oraclecloud.objectstorage.createobject"},
				Data:      rawExtension(`{"additionalDetails":{"bucketName":["my-bucket"]}}`),
			},
		},
	}
}

func readyEventTriggerFunction(name, namespace string) *functionsv1alpha1.Function {
	return &functionsv1alpha1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: namespace},
		Spec: functionsv1alpha1.FunctionSpec{
			Mode:           functionsv1alpha1.FunctionModeExisting,
			FunctionID:     "ocid1.fnfunc.oc1.me-jeddah-1.exampleuniqueid",
			InvokeEndpoint: "https://functions.me-jeddah-1.oci.oraclecloud.com",
		},
		Status: functionsv1alpha1.FunctionStatus{
			Phase:        functionsv1alpha1.FunctionPhaseReady,
			FunctionID:   "ocid1.fnfunc.oc1.me-jeddah-1.exampleuniqueid",
			FunctionOCID: "ocid1.fnfunc.oc1.me-jeddah-1.exampleuniqueid",
			Conditions: []metav1.Condition{{
				Type:               functionsv1alpha1.FunctionConditionReady,
				Status:             metav1.ConditionTrue,
				Reason:             "ExistingFunctionResolved",
				Message:            "Existing OCI Function OCID and invoke endpoint are configured.",
				ObservedGeneration: 1,
				LastTransitionTime: metav1.Now(),
			}},
		},
	}
}

func pendingEventTriggerFunction(name, namespace string) *functionsv1alpha1.Function {
	return &functionsv1alpha1.Function{
		ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: namespace},
		Spec: functionsv1alpha1.FunctionSpec{
			Mode: functionsv1alpha1.FunctionModeManaged,
			Config: &functionsv1alpha1.FunctionConfig{
				Region:           "me-jeddah-1",
				CompartmentID:    "ocid1.compartment.oc1..exampleuniqueid",
				ApplicationName:  "demo-app",
				SubnetIDs:        []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
				DisplayName:      "hello",
				Image:            "jed.ocir.io/example/hello-function:fn-v1",
				MemoryInMBs:      256,
				TimeoutInSeconds: 60,
			},
		},
		Status: functionsv1alpha1.FunctionStatus{
			Phase: functionsv1alpha1.FunctionPhasePending,
			Conditions: []metav1.Condition{{
				Type:               functionsv1alpha1.FunctionConditionReady,
				Status:             metav1.ConditionFalse,
				Reason:             "ManagedFunctionPending",
				Message:            "Managed OCI Function is reconciling.",
				ObservedGeneration: 1,
				LastTransitionTime: metav1.Now(),
			}},
		},
	}
}

func rawExtension(value string) *runtime.RawExtension {
	return &runtime.RawExtension{Raw: []byte(value)}
}

func reconcileEventTrigger(t *testing.T, ctx context.Context, reconciler *FunctionEventTriggerReconciler, trigger *functionsv1alpha1.FunctionEventTrigger) {
	t.Helper()

	if _, err := reconcileEventTriggerResult(t, ctx, reconciler, trigger); err != nil {
		t.Fatalf("reconcile FunctionEventTrigger: %v", err)
	}
}

func reconcileEventTriggerResult(t *testing.T, ctx context.Context, reconciler *FunctionEventTriggerReconciler, trigger *functionsv1alpha1.FunctionEventTrigger) (ctrl.Result, error) {
	t.Helper()

	request := ctrl.Request{NamespacedName: types.NamespacedName{Name: trigger.Name, Namespace: trigger.Namespace}}
	return reconciler.Reconcile(ctx, request)
}

func getEventTrigger(t *testing.T, ctx context.Context, k8sClient client.Client, trigger *functionsv1alpha1.FunctionEventTrigger) functionsv1alpha1.FunctionEventTrigger {
	t.Helper()

	var updated functionsv1alpha1.FunctionEventTrigger
	key := types.NamespacedName{Name: trigger.Name, Namespace: trigger.Namespace}
	if err := k8sClient.Get(ctx, key, &updated); err != nil {
		t.Fatalf("get FunctionEventTrigger: %v", err)
	}
	return updated
}

func volatileCreateRuleServiceError(opcRequestID, timestamp string) string {
	return fmt.Sprintf(`create OCI Events rule "object-created-trigger": Error returned by Events Service. Http Status Code: 404. Error Code: NotAuthorizedOrNotFound. Opc request id: %s. Message: Authorization failed or requested resource not found.
Operation Name: CreateRule
Timestamp: %s
Client Version: Oracle-GoSDK/65.118.0
Request Endpoint: POST https://events.me-jeddah-1.oci.oraclecloud.com/20181201/rules
Troubleshooting Tips: See https://docs.oracle.com/iaas/Content/API/References/apierrors.htm for more information about resolving this error.
To get more info on the failing request, you can set OCI_GO_SDK_DEBUG env var to info or higher level to log the request/response details.
If you are unable to resolve this Events issue, please contact Oracle support and provide them this full error message.`, opcRequestID, timestamp)
}

type fakeEventRuleManager struct {
	existingRuleID string
	emitUpdate     bool
	ensureErr      error
	ensureErrs     []error
	createCalls    int
	deleteCalls    int
	deletedRuleID  string
	desired        []eventtrigger.DesiredRule
}

func (f *fakeEventRuleManager) EnsureRule(_ context.Context, desired eventtrigger.DesiredRule) (eventtrigger.RuleState, error) {
	f.desired = append(f.desired, desired)
	if len(f.ensureErrs) > 0 {
		err := f.ensureErrs[0]
		if len(f.ensureErrs) > 1 {
			f.ensureErrs = f.ensureErrs[1:]
		}
		return eventtrigger.RuleState{RuleID: f.existingRuleID}, err
	}
	if f.ensureErr != nil {
		return eventtrigger.RuleState{RuleID: f.existingRuleID}, f.ensureErr
	}
	ruleID := desired.RuleID
	if ruleID == "" {
		if f.existingRuleID == "" {
			f.existingRuleID = "ocid1.eventrule.oc1.me-jeddah-1.exampleuniqueid"
			f.createCalls++
		}
		ruleID = f.existingRuleID
	}
	state := eventtrigger.RuleState{
		RuleID:  ruleID,
		Ready:   true,
		Message: "OCI Events rule is ready.",
	}
	if f.emitUpdate {
		state.Events = append(state.Events, eventtrigger.Event{Type: eventtrigger.EventTypeNormal, Reason: "RuleUpdated", Message: "Updated OCI Events rule."})
	}
	if f.createCalls == 1 && len(f.desired) == 1 {
		state.Events = append(state.Events, eventtrigger.Event{Type: eventtrigger.EventTypeNormal, Reason: "RuleCreated", Message: "Created OCI Events rule."})
	}
	return state, nil
}

func (f *fakeEventRuleManager) DeleteRule(_ context.Context, ruleID string) (eventtrigger.RuleState, error) {
	f.deleteCalls++
	f.deletedRuleID = ruleID
	if ruleID == "" {
		return eventtrigger.RuleState{}, errors.New("missing rule ID")
	}
	return eventtrigger.RuleState{
		RuleID:  ruleID,
		Ready:   true,
		Message: "OCI Events rule deleted.",
		Events: []eventtrigger.Event{{
			Type:    eventtrigger.EventTypeNormal,
			Reason:  "RuleDeleted",
			Message: "Deleted OCI Events rule.",
		}},
	}, nil
}
