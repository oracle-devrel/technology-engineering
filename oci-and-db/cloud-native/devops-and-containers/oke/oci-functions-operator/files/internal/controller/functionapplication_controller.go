// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package controller

import (
	"context"
	"fmt"
	"reflect"
	"strings"
	"time"

	functionsv1alpha1 "github.com/oracle/oci-functions-operator/api/v1alpha1"
	"github.com/oracle/oci-functions-operator/internal/lifecycle"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

const (
	functionApplicationFinalizer     = "functionapplications.functions.oci.oracle.com/finalizer"
	functionApplicationRequeue       = 30 * time.Second
	functionApplicationDeleteEvent   = "ApplicationDeleted"
	functionApplicationDeleteFailed  = "ApplicationDeleteFailed"
	functionApplicationDeleteBlocked = "ApplicationDeleteBlocked"
	functionApplicationRetained      = "ApplicationRetained"
)

// FunctionApplicationReconciler reconciles a FunctionApplication object.
type FunctionApplicationReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Manager  lifecycle.Manager
	Recorder record.EventRecorder
}

// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functionapplications,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functionapplications/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functionapplications/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

// Reconcile updates FunctionApplication status from OCI Functions application state.
func (r *FunctionApplicationReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var application functionsv1alpha1.FunctionApplication
	if err := r.Get(ctx, req.NamespacedName, &application); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	if !application.DeletionTimestamp.IsZero() {
		return r.reconcileDelete(ctx, &application)
	}

	if shouldHaveFunctionApplicationFinalizer(&application) && !controllerutil.ContainsFinalizer(&application, functionApplicationFinalizer) {
		controllerutil.AddFinalizer(&application, functionApplicationFinalizer)
		if err := r.Update(ctx, &application); err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{Requeue: true}, nil
	}
	if !shouldHaveFunctionApplicationFinalizer(&application) && controllerutil.ContainsFinalizer(&application, functionApplicationFinalizer) {
		controllerutil.RemoveFinalizer(&application, functionApplicationFinalizer)
		if err := r.Update(ctx, &application); err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{Requeue: true}, nil
	}

	now := metav1.Now()
	desiredStatus := functionsv1alpha1.FunctionApplicationStatus{ObservedGeneration: application.Generation}
	result := ctrl.Result{}

	if r.Manager == nil {
		desiredStatus.Phase = functionsv1alpha1.FunctionApplicationPhasePending
		desiredStatus.Message = "FunctionApplication lifecycle manager is not configured; run the manager with INVOKER_MODE=oci."
		setFunctionApplicationConditions(&desiredStatus, application.Generation, now, metav1.ConditionFalse, "LifecycleManagerNotConfigured", desiredStatus.Message)
		result = ctrl.Result{RequeueAfter: functionApplicationRequeue}
	} else {
		state, err := r.Manager.EnsureApplication(ctx, desiredApplicationFromSpec(&application))
		r.recordLifecycleEvents(&application, state.Events)
		desiredStatus.ApplicationID = state.ApplicationID
		desiredStatus.DisplayName = state.DisplayName
		desiredStatus.Region = state.Region
		desiredStatus.Message = state.Message
		if err != nil {
			desiredStatus.Phase = functionsv1alpha1.FunctionApplicationPhaseError
			desiredStatus.Message = normalizeFunctionLifecycleError("Reconcile FunctionApplication", err)
			setFunctionApplicationConditions(&desiredStatus, application.Generation, now, metav1.ConditionFalse, "FunctionApplicationError", desiredStatus.Message)
			result = ctrl.Result{RequeueAfter: functionApplicationRequeue}
		} else if state.Ready {
			desiredStatus.Phase = functionsv1alpha1.FunctionApplicationPhaseReady
			if desiredStatus.Message == "" {
				desiredStatus.Message = "OCI Functions application is ready."
			}
			setFunctionApplicationConditions(&desiredStatus, application.Generation, now, metav1.ConditionTrue, "FunctionApplicationReady", desiredStatus.Message)
		} else {
			desiredStatus.Phase = functionsv1alpha1.FunctionApplicationPhasePending
			if desiredStatus.Message == "" {
				desiredStatus.Message = "OCI Functions application is reconciling."
			}
			setFunctionApplicationConditions(&desiredStatus, application.Generation, now, metav1.ConditionFalse, "FunctionApplicationPending", desiredStatus.Message)
			result = ctrl.Result{RequeueAfter: functionApplicationRequeue}
		}
	}

	patched, err := r.updateFunctionApplicationStatusIfChanged(ctx, &application, desiredStatus, true)
	if err != nil {
		return ctrl.Result{}, err
	}
	if patched {
		logger.V(1).Info("updated FunctionApplication status", "phase", desiredStatus.Phase)
	}
	return result, nil
}

func (r *FunctionApplicationReconciler) reconcileDelete(ctx context.Context, application *functionsv1alpha1.FunctionApplication) (ctrl.Result, error) {
	if !controllerutil.ContainsFinalizer(application, functionApplicationFinalizer) {
		return ctrl.Result{}, nil
	}

	if application.Mode() != functionsv1alpha1.FunctionApplicationModeManaged ||
		application.DeletionPolicy() != functionsv1alpha1.FunctionDeletionPolicyDelete {
		r.recordFunctionApplicationEvent(application, corev1.EventTypeNormal, functionApplicationRetained, "Retained OCI Functions application.")
		controllerutil.RemoveFinalizer(application, functionApplicationFinalizer)
		if err := r.Update(ctx, application); err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{}, nil
	}

	now := metav1.Now()
	if r.Manager == nil {
		desired := functionApplicationDeletionErrorStatus(application, now, "LifecycleManagerNotConfigured", "Cannot delete OCI Functions application because the lifecycle manager is not configured.")
		patched, err := r.updateFunctionApplicationStatusIfChanged(ctx, application, desired, true)
		if err != nil {
			return ctrl.Result{}, err
		}
		if patched {
			r.recordFunctionApplicationEvent(application, corev1.EventTypeWarning, functionApplicationDeleteFailed, desired.Message)
		}
		return ctrl.Result{RequeueAfter: functionApplicationRequeue}, nil
	}

	state, err := r.Manager.DeleteApplication(ctx, applicationDeleteTarget(application))
	r.recordLifecycleEvents(application, state.Events)
	if err != nil {
		message := normalizeFunctionLifecycleError("Delete OCI Functions application", err)
		desired := functionApplicationDeletionErrorStatus(application, now, "ApplicationDeleteFailed", message)
		patched, updateErr := r.updateFunctionApplicationStatusIfChanged(ctx, application, desired, true)
		if updateErr != nil {
			return ctrl.Result{}, updateErr
		}
		if patched {
			r.recordFunctionApplicationEvent(application, corev1.EventTypeWarning, functionApplicationDeleteFailed, message)
		}
		return ctrl.Result{RequeueAfter: functionApplicationRequeue}, nil
	}
	if state.Blocked {
		desired := functionApplicationDeletionErrorStatus(application, now, "ApplicationDeleteBlocked", state.Message)
		patched, updateErr := r.updateFunctionApplicationStatusIfChanged(ctx, application, desired, true)
		if updateErr != nil {
			return ctrl.Result{}, updateErr
		}
		if patched {
			r.recordFunctionApplicationEvent(application, corev1.EventTypeWarning, functionApplicationDeleteBlocked, state.Message)
		}
		return ctrl.Result{RequeueAfter: functionApplicationRequeue}, nil
	}

	controllerutil.RemoveFinalizer(application, functionApplicationFinalizer)
	if err := r.Update(ctx, application); err != nil {
		return ctrl.Result{}, err
	}
	if state.Message != "" {
		r.recordFunctionApplicationEvent(application, corev1.EventTypeNormal, functionApplicationDeleteEvent, state.Message)
	}
	return ctrl.Result{}, nil
}

func shouldHaveFunctionApplicationFinalizer(application *functionsv1alpha1.FunctionApplication) bool {
	return application.Mode() == functionsv1alpha1.FunctionApplicationModeManaged &&
		application.DeletionPolicy() == functionsv1alpha1.FunctionDeletionPolicyDelete
}

func desiredApplicationFromSpec(application *functionsv1alpha1.FunctionApplication) lifecycle.DesiredApplication {
	mode := lifecycle.ApplicationModeManaged
	if application.Mode() == functionsv1alpha1.FunctionApplicationModeExisting {
		mode = lifecycle.ApplicationModeExisting
	}
	return lifecycle.DesiredApplication{
		Mode:                           mode,
		Region:                         strings.TrimSpace(application.Spec.Region),
		CompartmentID:                  strings.TrimSpace(application.Spec.CompartmentID),
		DisplayName:                    strings.TrimSpace(application.Spec.DisplayName),
		SubnetIDs:                      trimStringSlice(application.Spec.SubnetIDs),
		ApplicationNSGIDs:              trimStringSlice(application.Spec.NSGIDs),
		ManageApplicationNSGIDs:        application.Spec.NSGIDs != nil,
		Config:                         copyStringMap(application.Spec.Config),
		Logging:                        applicationLoggingFromSpec(application.Spec.Logging),
		ExistingApplicationID:          strings.TrimSpace(application.Spec.ExistingApplicationID),
		ManageApplicationConfiguration: application.Spec.Config != nil,
		ManageApplicationLogging:       application.Spec.Logging != nil && application.Spec.Logging.InvocationLogs != nil,
	}
}

func applicationLoggingFromSpec(spec *functionsv1alpha1.FunctionApplicationLogging) *lifecycle.ApplicationLogging {
	if spec == nil || spec.InvocationLogs == nil {
		return nil
	}
	invocationLogs := spec.InvocationLogs
	lineFormat := strings.TrimSpace(string(spec.InvocationLogs.LineFormat))
	if lineFormat == "" {
		lineFormat = string(functionsv1alpha1.FunctionApplicationLogLineFormatJSON)
	}
	return &lifecycle.ApplicationLogging{
		InvocationLogs: &lifecycle.ApplicationInvocationLogs{
			Enabled:        invocationLoggingEnabledFromSpec(invocationLogs.Enabled),
			LogGroupID:     strings.TrimSpace(invocationLogs.LogGroupID),
			LogDisplayName: strings.TrimSpace(invocationLogs.LogDisplayName),
			Service:        strings.TrimSpace(invocationLogs.Service),
			Category:       strings.TrimSpace(invocationLogs.Category),
			LineFormat:     lineFormat,
		},
	}
}

func invocationLoggingEnabledFromSpec(enabled *bool) bool {
	return enabled == nil || *enabled
}

func applicationDeleteTarget(application *functionsv1alpha1.FunctionApplication) lifecycle.ApplicationDeleteTarget {
	applicationID := strings.TrimSpace(application.Status.ApplicationID)
	if applicationID == "" {
		applicationID = strings.TrimSpace(application.Spec.ExistingApplicationID)
	}
	region := strings.TrimSpace(application.Status.Region)
	if region == "" {
		region = strings.TrimSpace(application.Spec.Region)
	}
	return lifecycle.ApplicationDeleteTarget{
		Region:        region,
		ApplicationID: applicationID,
		DisplayName:   strings.TrimSpace(application.Spec.DisplayName),
		CompartmentID: strings.TrimSpace(application.Spec.CompartmentID),
	}
}

func setFunctionApplicationConditions(status *functionsv1alpha1.FunctionApplicationStatus, generation int64, now metav1.Time, conditionStatus metav1.ConditionStatus, reason, message string) {
	setFunctionApplicationCondition(status, functionsv1alpha1.FunctionApplicationConditionReady, conditionStatus, reason, message, generation, now)
	setFunctionApplicationCondition(status, functionsv1alpha1.FunctionApplicationConditionApplicationResolved, conditionStatus, reason, message, generation, now)
	setFunctionApplicationCondition(status, functionsv1alpha1.FunctionApplicationConditionApplicationReady, conditionStatus, reason, message, generation, now)
}

func setFunctionApplicationCondition(status *functionsv1alpha1.FunctionApplicationStatus, conditionType string, conditionStatus metav1.ConditionStatus, reason, message string, generation int64, now metav1.Time) {
	condition := metav1.Condition{
		Type:               conditionType,
		Status:             conditionStatus,
		Reason:             reason,
		Message:            message,
		ObservedGeneration: generation,
		LastTransitionTime: now,
	}
	for i := range status.Conditions {
		existing := &status.Conditions[i]
		if existing.Type != condition.Type {
			continue
		}
		if existing.Status == condition.Status {
			condition.LastTransitionTime = existing.LastTransitionTime
		}
		status.Conditions[i] = condition
		return
	}
	status.Conditions = append(status.Conditions, condition)
}

func functionApplicationDeletionErrorStatus(application *functionsv1alpha1.FunctionApplication, now metav1.Time, reason, message string) functionsv1alpha1.FunctionApplicationStatus {
	status := application.Status
	status.ObservedGeneration = application.Generation
	status.Phase = functionsv1alpha1.FunctionApplicationPhaseError
	status.Message = message
	setFunctionApplicationConditions(&status, application.Generation, now, metav1.ConditionFalse, reason, message)
	return status
}

func (r *FunctionApplicationReconciler) updateFunctionApplicationStatusIfChanged(ctx context.Context, application *functionsv1alpha1.FunctionApplication, desired functionsv1alpha1.FunctionApplicationStatus, updateLastSync bool) (bool, error) {
	current := application.Status
	current.LastSyncTime = nil
	comparableDesired := desired
	comparableDesired.LastSyncTime = nil
	if reflect.DeepEqual(current, comparableDesired) {
		return false, nil
	}
	if updateLastSync {
		now := metav1.Now()
		desired.LastSyncTime = &now
	}
	application.Status = desired
	if err := r.Status().Update(ctx, application); err != nil {
		return false, err
	}
	return true, nil
}

func (r *FunctionApplicationReconciler) recordFunctionApplicationEvent(application *functionsv1alpha1.FunctionApplication, eventType, reason, message string) {
	if r.Recorder == nil {
		return
	}
	r.Recorder.Event(application, eventType, reason, message)
}

func (r *FunctionApplicationReconciler) recordLifecycleEvents(application *functionsv1alpha1.FunctionApplication, events []lifecycle.Event) {
	if r.Recorder == nil {
		return
	}
	for _, event := range events {
		eventType := corev1.EventTypeNormal
		if event.Type == lifecycle.EventTypeWarning {
			eventType = corev1.EventTypeWarning
		}
		r.Recorder.Event(application, eventType, event.Reason, event.Message)
	}
}

// SetupWithManager sets up the controller with the Manager.
func (r *FunctionApplicationReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&functionsv1alpha1.FunctionApplication{}).
		Complete(r)
}

func normalizeFunctionApplicationLifecycleError(operation string, err error) string {
	if err == nil {
		return ensureSentence(fmt.Sprintf("%s failed", operation))
	}
	message := sanitizeOCIErrorText(err.Error())
	if message == "" {
		message = "OCI Functions API request failed"
	}
	return ensureSentence(fmt.Sprintf("%s failed: %s", operation, message))
}
