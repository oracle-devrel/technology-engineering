// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package controller

import (
	"context"
	"errors"
	"strings"
	"testing"

	functionsv1alpha1 "github.com/oracle/oci-functions-operator/api/v1alpha1"
	"github.com/oracle/oci-functions-operator/internal/lifecycle"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
)

func TestFunctionApplicationReconcilerManagedMarksReady(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	application := managedFunctionApplication("demo-app", "default")
	enabled := true
	application.Spec.Logging = &functionsv1alpha1.FunctionApplicationLogging{
		InvocationLogs: &functionsv1alpha1.FunctionApplicationInvocationLogs{
			Enabled:    &enabled,
			LogGroupID: "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid",
			LineFormat: functionsv1alpha1.FunctionApplicationLogLineFormatJSON,
		},
	}
	manager := &fakeLifecycleManager{
		applicationState: lifecycle.ApplicationState{
			ApplicationID: "ocid1.fnapp.oc1.me-jeddah-1.exampleuniqueid",
			DisplayName:   "demo-app",
			Region:        "me-jeddah-1",
			Ready:         true,
			Message:       "OCI Functions application is ready.",
		},
	}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionApplication{}).
		WithObjects(application).
		Build()
	reconciler := &FunctionApplicationReconciler{Client: client, Scheme: scheme, Manager: manager}

	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "demo-app", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}
	if manager.ensureApplicationCalls != 1 {
		t.Fatalf("ensureApplicationCalls = %d, want 1", manager.ensureApplicationCalls)
	}
	if manager.desiredApplication.DisplayName != application.Spec.DisplayName {
		t.Fatalf("desired displayName = %q, want %q", manager.desiredApplication.DisplayName, application.Spec.DisplayName)
	}
	if !manager.desiredApplication.ManageApplicationNSGIDs {
		t.Fatalf("ManageApplicationNSGIDs = false, want true when nsgIds is set")
	}
	if !manager.desiredApplication.ManageApplicationLogging {
		t.Fatalf("ManageApplicationLogging = false, want true when logging is set")
	}
	if manager.desiredApplication.Logging == nil ||
		manager.desiredApplication.Logging.InvocationLogs == nil ||
		!manager.desiredApplication.Logging.InvocationLogs.Enabled ||
		manager.desiredApplication.Logging.InvocationLogs.LogGroupID != "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid" ||
		manager.desiredApplication.Logging.InvocationLogs.LineFormat != "JSON" {
		t.Fatalf("desired logging = %#v, want enabled JSON invocation logs", manager.desiredApplication.Logging)
	}

	var updated functionsv1alpha1.FunctionApplication
	if err := client.Get(ctx, types.NamespacedName{Name: "demo-app", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionApplication: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionApplicationPhaseReady {
		t.Fatalf("phase = %q, want Ready", updated.Status.Phase)
	}
	if updated.Status.ApplicationID != manager.applicationState.ApplicationID {
		t.Fatalf("applicationId = %q, want %q", updated.Status.ApplicationID, manager.applicationState.ApplicationID)
	}
	if condition := meta.FindStatusCondition(updated.Status.Conditions, functionsv1alpha1.FunctionApplicationConditionReady); condition == nil || condition.Status != metav1.ConditionTrue {
		t.Fatalf("Ready condition = %#v, want true", condition)
	}
}

func TestFunctionApplicationReconcilerRequeuesLifecycleError(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	application := managedFunctionApplication("demo-app", "default")
	manager := &fakeLifecycleManager{
		applicationState: lifecycle.ApplicationState{
			ApplicationID: "ocid1.fnapp.oc1.me-jeddah-1.exampleuniqueid",
			DisplayName:   "demo-app",
			Region:        "me-jeddah-1",
		},
		applicationErr: errors.New("OCI Logging service log is CREATING"),
	}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionApplication{}).
		WithObjects(application).
		Build()
	reconciler := &FunctionApplicationReconciler{Client: client, Scheme: scheme, Manager: manager}

	result, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "demo-app", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}
	if result.RequeueAfter != functionApplicationRequeue {
		t.Fatalf("RequeueAfter = %s, want %s", result.RequeueAfter, functionApplicationRequeue)
	}
	var updated functionsv1alpha1.FunctionApplication
	if err := client.Get(ctx, types.NamespacedName{Name: "demo-app", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionApplication: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionApplicationPhaseError {
		t.Fatalf("phase = %q, want Error", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "OCI Logging service log is CREATING") {
		t.Fatalf("message = %q, want lifecycle error", updated.Status.Message)
	}
}

func TestFunctionApplicationReconcilerRetainDeleteDoesNotDeleteOCIApplication(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	application := managedFunctionApplication("demo-app", "default")
	application.Finalizers = []string{functionApplicationFinalizer}
	application.Status.ApplicationID = "ocid1.fnapp.oc1.me-jeddah-1.exampleuniqueid"
	manager := &fakeLifecycleManager{}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionApplication{}).
		WithObjects(application).
		Build()
	reconciler := &FunctionApplicationReconciler{Client: client, Scheme: scheme, Manager: manager}

	if err := client.Delete(ctx, application); err != nil {
		t.Fatalf("delete FunctionApplication: %v", err)
	}
	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "demo-app", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}
	if manager.deleteApplicationCalls != 0 {
		t.Fatalf("deleteApplicationCalls = %d, want 0 for Retain", manager.deleteApplicationCalls)
	}
	var updated functionsv1alpha1.FunctionApplication
	err = client.Get(ctx, types.NamespacedName{Name: "demo-app", Namespace: "default"}, &updated)
	if err == nil {
		t.Fatalf("FunctionApplication still exists after finalizer removal, finalizers=%#v", updated.Finalizers)
	}
}

func TestFunctionApplicationReconcilerDeletePolicyDeletesEmptyOCIApplication(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	application := managedFunctionApplication("demo-app", "default")
	application.Spec.DeletionPolicy = functionsv1alpha1.FunctionDeletionPolicyDelete
	application.Finalizers = []string{functionApplicationFinalizer}
	application.Status.ApplicationID = "ocid1.fnapp.oc1.me-jeddah-1.exampleuniqueid"
	application.Status.Region = "me-jeddah-1"
	manager := &fakeLifecycleManager{
		deleteApplicationState: lifecycle.ApplicationDeletionState{
			ApplicationID: application.Status.ApplicationID,
			Deleted:       true,
			Message:       "Deleted OCI Functions application.",
		},
	}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionApplication{}).
		WithObjects(application).
		Build()
	reconciler := &FunctionApplicationReconciler{Client: client, Scheme: scheme, Manager: manager}

	if err := client.Delete(ctx, application); err != nil {
		t.Fatalf("delete FunctionApplication: %v", err)
	}
	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "demo-app", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}
	if manager.deleteApplicationCalls != 1 {
		t.Fatalf("deleteApplicationCalls = %d, want 1", manager.deleteApplicationCalls)
	}
	if manager.deleteApplicationTarget.ApplicationID != application.Status.ApplicationID {
		t.Fatalf("delete application ID = %q, want %q", manager.deleteApplicationTarget.ApplicationID, application.Status.ApplicationID)
	}
	var updated functionsv1alpha1.FunctionApplication
	err = client.Get(ctx, types.NamespacedName{Name: "demo-app", Namespace: "default"}, &updated)
	if err == nil {
		t.Fatalf("FunctionApplication still exists after delete, finalizers=%#v", updated.Finalizers)
	}
}

func TestFunctionApplicationReconcilerDeletePolicyBlocksWhenFunctionsRemain(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	application := managedFunctionApplication("demo-app", "default")
	application.Spec.DeletionPolicy = functionsv1alpha1.FunctionDeletionPolicyDelete
	application.Finalizers = []string{functionApplicationFinalizer}
	application.Status.ApplicationID = "ocid1.fnapp.oc1.me-jeddah-1.exampleuniqueid"
	application.Status.Region = "me-jeddah-1"
	manager := &fakeLifecycleManager{
		deleteApplicationState: lifecycle.ApplicationDeletionState{
			ApplicationID: application.Status.ApplicationID,
			Blocked:       true,
			Message:       "Retained OCI Functions application because 1 function(s) remain in it.",
		},
	}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionApplication{}).
		WithObjects(application).
		Build()
	reconciler := &FunctionApplicationReconciler{Client: client, Scheme: scheme, Manager: manager}

	if err := client.Delete(ctx, application); err != nil {
		t.Fatalf("delete FunctionApplication: %v", err)
	}
	result, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "demo-app", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}
	if result.RequeueAfter == 0 {
		t.Fatalf("requeueAfter = 0, want retry while delete is blocked")
	}
	if manager.deleteApplicationCalls != 1 {
		t.Fatalf("deleteApplicationCalls = %d, want 1", manager.deleteApplicationCalls)
	}
	var updated functionsv1alpha1.FunctionApplication
	if err := client.Get(ctx, types.NamespacedName{Name: "demo-app", Namespace: "default"}, &updated); err != nil {
		t.Fatalf("get updated FunctionApplication: %v", err)
	}
	if updated.Status.Phase != functionsv1alpha1.FunctionApplicationPhaseError {
		t.Fatalf("phase = %q, want Error while delete is blocked", updated.Status.Phase)
	}
	if !strings.Contains(updated.Status.Message, "remain") {
		t.Fatalf("message = %q, want blocked cleanup guidance", updated.Status.Message)
	}
}

func TestFunctionApplicationReconcilerExistingNeverDeletesOCIApplication(t *testing.T) {
	ctx := context.Background()
	scheme := newTestScheme(t)
	application := managedFunctionApplication("demo-app", "default")
	application.Spec.Mode = functionsv1alpha1.FunctionApplicationModeExisting
	application.Spec.ExistingApplicationID = "ocid1.fnapp.oc1.me-jeddah-1.exampleuniqueid"
	application.Spec.DeletionPolicy = functionsv1alpha1.FunctionDeletionPolicyDelete
	application.Finalizers = []string{functionApplicationFinalizer}
	manager := &fakeLifecycleManager{}

	client := fake.NewClientBuilder().
		WithScheme(scheme).
		WithStatusSubresource(&functionsv1alpha1.FunctionApplication{}).
		WithObjects(application).
		Build()
	reconciler := &FunctionApplicationReconciler{Client: client, Scheme: scheme, Manager: manager}

	if err := client.Delete(ctx, application); err != nil {
		t.Fatalf("delete FunctionApplication: %v", err)
	}
	_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: types.NamespacedName{Name: "demo-app", Namespace: "default"}})
	if err != nil {
		t.Fatalf("reconcile failed: %v", err)
	}
	if manager.deleteApplicationCalls != 0 {
		t.Fatalf("deleteApplicationCalls = %d, want 0 for Existing mode", manager.deleteApplicationCalls)
	}
}
