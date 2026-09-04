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
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

const (
	functionFinalizer      = "functions.functions.oci.oracle.com/finalizer"
	functionDeleteRequeue  = 30 * time.Second
	functionDeleteEvent    = "ManagedFunctionDeleted"
	functionDeleteFailed   = "ManagedFunctionDeleteFailed"
	functionDeleteRetained = "ManagedFunctionRetained"
)

// FunctionReconciler reconciles a Function object.
type FunctionReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Manager  lifecycle.Manager
	Recorder record.EventRecorder
}

// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functions,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functions/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functions/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

// Reconcile updates Function status from the requested source of truth.
func (r *FunctionReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var function functionsv1alpha1.Function
	if err := r.Get(ctx, req.NamespacedName, &function); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	if !function.DeletionTimestamp.IsZero() {
		return r.reconcileDelete(ctx, &function)
	}

	now := metav1.Now()
	desiredObject := function.DeepCopy()
	desiredObject.Status = functionsv1alpha1.FunctionStatus{
		ObservedGeneration: function.Generation,
	}

	result := ctrl.Result{}
	mode := resolvedFunctionMode(&function)

	if shouldHaveFunctionFinalizer(&function, mode) && !controllerutil.ContainsFinalizer(&function, functionFinalizer) {
		controllerutil.AddFinalizer(&function, functionFinalizer)
		if err := r.Update(ctx, &function); err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{Requeue: true}, nil
	}
	if !shouldHaveFunctionFinalizer(&function, mode) && controllerutil.ContainsFinalizer(&function, functionFinalizer) {
		controllerutil.RemoveFinalizer(&function, functionFinalizer)
		if err := r.Update(ctx, &function); err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{Requeue: true}, nil
	}

	referencedApplication, waitingForApplication, err := r.resolveFunctionApplicationRef(ctx, &function, desiredObject, now)
	if err != nil {
		return ctrl.Result{}, err
	}
	if waitingForApplication {
		result = ctrl.Result{RequeueAfter: 30 * time.Second}
		patched, err := r.updateFunctionStatusIfChanged(ctx, &function, desiredObject.Status, true)
		if err != nil {
			return ctrl.Result{}, err
		}
		if patched {
			logger.V(1).Info("updated Function status", "phase", desiredObject.Status.Phase)
		}
		return result, nil
	}

	switch mode {
	case functionsv1alpha1.FunctionModeExisting:
		if function.DeletionPolicy() == functionsv1alpha1.FunctionDeletionPolicyDelete {
			reconcileExistingFunctionDeletePolicyError(desiredObject, now)
		} else {
			reconcileExistingFunctionStatus(desiredObject, now)
			if referencedApplication != nil {
				desiredObject.Status.ApplicationID = referencedApplication.Status.ApplicationID
			}
		}
	case functionsv1alpha1.FunctionModeManaged:
		var pending bool
		var err error
		if referencedApplication != nil {
			pending, err = r.reconcileManagedFunctionWithApplicationRef(ctx, desiredObject, referencedApplication, now)
		} else {
			pending, err = r.reconcileManagedFunctionStatus(ctx, desiredObject, now)
		}
		if err != nil {
			return ctrl.Result{}, err
		}
		if pending {
			result = ctrl.Result{RequeueAfter: 30 * time.Second}
		}
	default:
		desiredObject.Status.Phase = functionsv1alpha1.FunctionPhaseError
		desiredObject.Status.Message = "Function must specify functionId, existingFunctionOcid, or config."
		desiredObject.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "InvalidSpec",
			Message:            "Function must specify functionId, existingFunctionOcid, or config.",
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
	}

	patched, err := r.updateFunctionStatusIfChanged(ctx, &function, desiredObject.Status, true)
	if err != nil {
		return ctrl.Result{}, err
	}
	if patched {
		logger.V(1).Info("updated Function status", "phase", desiredObject.Status.Phase)
	}
	return result, nil
}

func (r *FunctionReconciler) reconcileDelete(ctx context.Context, function *functionsv1alpha1.Function) (ctrl.Result, error) {
	if !controllerutil.ContainsFinalizer(function, functionFinalizer) {
		return ctrl.Result{}, nil
	}

	mode := resolvedFunctionMode(function)
	if mode != functionsv1alpha1.FunctionModeManaged || function.DeletionPolicy() != functionsv1alpha1.FunctionDeletionPolicyDelete {
		r.recordFunctionEvent(function, corev1.EventTypeNormal, functionDeleteRetained, "Retained OCI resources for Function deletion.")
		controllerutil.RemoveFinalizer(function, functionFinalizer)
		if err := r.Update(ctx, function); err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{}, nil
	}

	now := metav1.Now()
	if requeueAfter, ok := functionDeletionBackoff(function, now.Time); ok {
		return ctrl.Result{RequeueAfter: requeueAfter}, nil
	}

	if r.Manager == nil {
		desired := deletionErrorStatus(function, now, "LifecycleManagerNotConfigured", "Cannot delete managed OCI Function because the lifecycle manager is not configured.")
		patched, err := r.updateFunctionStatusIfChanged(ctx, function, desired, true)
		if err != nil {
			return ctrl.Result{}, err
		}
		if patched {
			r.recordFunctionEvent(function, corev1.EventTypeWarning, functionDeleteFailed, desired.Message)
		}
		return ctrl.Result{RequeueAfter: functionDeleteRequeue}, nil
	}

	if !isFunctionDeleteFailure(function) {
		deleting := function.Status
		deleting.ObservedGeneration = function.Generation
		deleting.Phase = functionsv1alpha1.FunctionPhasePending
		deleting.Message = "Deleting managed OCI Function; OCI Functions application will be retained."
		setFunctionReadyCondition(&deleting, metav1.ConditionFalse, "ManagedFunctionDeleting", deleting.Message, function.Generation, now)
		if _, err := r.updateFunctionStatusIfChanged(ctx, function, deleting, true); err != nil {
			return ctrl.Result{}, err
		}
	}

	state, err := r.Manager.DeleteManagedFunction(ctx, managedFunctionDeleteTarget(function))
	r.recordLifecycleEvents(function, state.Events)
	if err != nil {
		message := normalizeFunctionLifecycleError("Delete managed OCI Function", err)
		desired := deletionErrorStatus(function, now, "ManagedFunctionDeleteFailed", message)
		patched, updateErr := r.updateFunctionStatusIfChanged(ctx, function, desired, true)
		if updateErr != nil {
			return ctrl.Result{}, updateErr
		}
		if patched {
			r.recordFunctionEvent(function, corev1.EventTypeWarning, functionDeleteFailed, message)
		}
		return ctrl.Result{RequeueAfter: functionDeleteRequeue}, nil
	}

	controllerutil.RemoveFinalizer(function, functionFinalizer)
	if err := r.Update(ctx, function); err != nil {
		return ctrl.Result{}, err
	}
	if state.Message != "" {
		r.recordFunctionEvent(function, corev1.EventTypeNormal, functionDeleteEvent, state.Message)
	}
	return ctrl.Result{}, nil
}

func (r *FunctionReconciler) resolveFunctionApplicationRef(ctx context.Context, function *functionsv1alpha1.Function, desiredObject *functionsv1alpha1.Function, now metav1.Time) (*functionsv1alpha1.FunctionApplication, bool, error) {
	if function.Spec.ApplicationRef == nil || strings.TrimSpace(function.Spec.ApplicationRef.Name) == "" {
		return nil, false, nil
	}
	if hasLegacyApplicationFields(function.Spec.Config) {
		desiredObject.Status.Phase = functionsv1alpha1.FunctionPhaseError
		desiredObject.Status.Message = "spec.applicationRef cannot be combined with legacy application fields in spec.config: region, compartmentId, applicationName, subnetIds, nsgIds, or applicationOcid."
		desiredObject.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "InvalidApplicationRef",
			Message:            desiredObject.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return nil, true, nil
	}

	var application functionsv1alpha1.FunctionApplication
	key := client.ObjectKey{Namespace: function.Namespace, Name: strings.TrimSpace(function.Spec.ApplicationRef.Name)}
	if err := r.Get(ctx, key, &application); err != nil {
		if apierrors.IsNotFound(err) {
			desiredObject.Status.Phase = functionsv1alpha1.FunctionPhasePending
			desiredObject.Status.Message = fmt.Sprintf("Waiting for FunctionApplication %q to exist.", key.Name)
			desiredObject.SetCondition(metav1.Condition{
				Type:               functionsv1alpha1.FunctionConditionReady,
				Status:             metav1.ConditionFalse,
				Reason:             "FunctionApplicationNotFound",
				Message:            desiredObject.Status.Message,
				ObservedGeneration: function.Generation,
				LastTransitionTime: now,
			})
			return nil, true, nil
		}
		return nil, false, err
	}
	if !application.DeletionTimestamp.IsZero() {
		desiredObject.Status.ApplicationID = application.Status.ApplicationID
		desiredObject.Status.Phase = functionsv1alpha1.FunctionPhasePending
		desiredObject.Status.Message = fmt.Sprintf("Waiting for FunctionApplication %q deletion to finish.", application.Name)
		desiredObject.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "FunctionApplicationDeleting",
			Message:            desiredObject.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return nil, true, nil
	}
	if !application.IsReady() || strings.TrimSpace(application.Status.ApplicationID) == "" {
		desiredObject.Status.ApplicationID = application.Status.ApplicationID
		desiredObject.Status.Phase = functionsv1alpha1.FunctionPhasePending
		desiredObject.Status.Message = fmt.Sprintf("Waiting for FunctionApplication %q to become Ready.", application.Name)
		desiredObject.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "FunctionApplicationNotReady",
			Message:            desiredObject.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return nil, true, nil
	}
	return &application, false, nil
}

func reconcileExistingFunctionStatus(function *functionsv1alpha1.Function, now metav1.Time) {
	functionID := resolvedSpecFunctionID(function)
	invokeEndpoint := strings.TrimSpace(function.Spec.InvokeEndpoint)
	function.Status.FunctionOCID = functionID
	function.Status.FunctionID = functionID
	function.Status.InvokeEndpoint = invokeEndpoint

	if functionID == "" || invokeEndpoint == "" {
		function.Status.Phase = functionsv1alpha1.FunctionPhaseError
		function.Status.Message = "Existing Function mode requires spec.functionId and spec.invokeEndpoint."
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "InvalidExistingFunction",
			Message:            "Existing Function mode requires spec.functionId or spec.existingFunctionOcid and spec.invokeEndpoint.",
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return
	}

	function.Status.Phase = functionsv1alpha1.FunctionPhaseReady
	function.Status.Message = "Using existing OCI Function."
	function.SetCondition(metav1.Condition{
		Type:               functionsv1alpha1.FunctionConditionReady,
		Status:             metav1.ConditionTrue,
		Reason:             "ExistingFunctionResolved",
		Message:            "Existing OCI Function OCID and invoke endpoint are configured.",
		ObservedGeneration: function.Generation,
		LastTransitionTime: now,
	})
}

func reconcileExistingFunctionDeletePolicyError(function *functionsv1alpha1.Function, now metav1.Time) {
	function.Status.Phase = functionsv1alpha1.FunctionPhaseError
	function.Status.Message = "spec.deletionPolicy=Delete is only supported for Managed mode. Existing mode never deletes OCI resources."
	function.SetCondition(metav1.Condition{
		Type:               functionsv1alpha1.FunctionConditionReady,
		Status:             metav1.ConditionFalse,
		Reason:             "InvalidDeletionPolicy",
		Message:            function.Status.Message,
		ObservedGeneration: function.Generation,
		LastTransitionTime: now,
	})
}

func (r *FunctionReconciler) reconcileManagedFunctionWithApplicationRef(ctx context.Context, function *functionsv1alpha1.Function, application *functionsv1alpha1.FunctionApplication, now metav1.Time) (bool, error) {
	if function.Spec.Config == nil {
		function.Status.Phase = functionsv1alpha1.FunctionPhaseError
		function.Status.ApplicationID = application.Status.ApplicationID
		function.Status.Message = "Managed Function mode with applicationRef requires spec.config for function-level fields."
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "InvalidManagedFunction",
			Message:            function.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return false, nil
	}
	if r.Manager == nil {
		function.Status.Phase = functionsv1alpha1.FunctionPhasePending
		function.Status.ApplicationID = application.Status.ApplicationID
		function.Status.Message = "Function lifecycle manager is not configured; run the manager with INVOKER_MODE=oci for managed Functions."
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "LifecycleManagerNotConfigured",
			Message:            function.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return true, nil
	}

	state, err := r.Manager.EnsureFunctionInApplication(ctx, desiredFunctionInApplicationFromSpec(function, application))
	r.recordLifecycleEvents(function, state.Events)
	if err != nil {
		function.Status.ApplicationID = state.ApplicationID
		if function.Status.ApplicationID == "" {
			function.Status.ApplicationID = application.Status.ApplicationID
		}
		function.Status.FunctionOCID = state.FunctionID
		function.Status.FunctionID = state.FunctionID
		function.Status.InvokeEndpoint = state.InvokeEndpoint
		function.Status.Phase = functionsv1alpha1.FunctionPhaseError
		function.Status.Message = err.Error()
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "ManagedFunctionError",
			Message:            err.Error(),
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return false, nil
	}

	function.Status.ApplicationID = application.Status.ApplicationID
	function.Status.FunctionOCID = state.FunctionID
	function.Status.FunctionID = state.FunctionID
	function.Status.InvokeEndpoint = state.InvokeEndpoint
	function.Status.Message = state.Message
	if function.Status.Message == "" {
		function.Status.Message = "Managed OCI Function is reconciling."
	}
	if state.Ready {
		function.Status.Phase = functionsv1alpha1.FunctionPhaseReady
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionTrue,
			Reason:             "ManagedFunctionReady",
			Message:            function.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return false, nil
	}

	function.Status.Phase = functionsv1alpha1.FunctionPhasePending
	function.SetCondition(metav1.Condition{
		Type:               functionsv1alpha1.FunctionConditionReady,
		Status:             metav1.ConditionFalse,
		Reason:             "ManagedFunctionPending",
		Message:            function.Status.Message,
		ObservedGeneration: function.Generation,
		LastTransitionTime: now,
	})
	return true, nil
}

func (r *FunctionReconciler) reconcileManagedFunctionStatus(ctx context.Context, function *functionsv1alpha1.Function, now metav1.Time) (bool, error) {
	if function.Spec.Config == nil {
		function.Status.Phase = functionsv1alpha1.FunctionPhaseError
		function.Status.Message = "Managed Function mode requires spec.config."
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "InvalidManagedFunction",
			Message:            "Managed Function mode requires spec.config.",
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return false, nil
	}
	if err := validateLegacyManagedFunctionConfig(function.Spec.Config); err != nil {
		function.Status.Phase = functionsv1alpha1.FunctionPhaseError
		function.Status.Message = err.Error()
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "InvalidManagedFunction",
			Message:            function.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return false, nil
	}
	if r.Manager == nil {
		function.Status.Phase = functionsv1alpha1.FunctionPhasePending
		function.Status.Message = "Function lifecycle manager is not configured; run the manager with INVOKER_MODE=oci for managed Functions."
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "LifecycleManagerNotConfigured",
			Message:            function.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return true, nil
	}

	state, err := r.Manager.EnsureFunction(ctx, desiredFunctionFromSpec(function))
	r.recordLifecycleEvents(function, state.Events)
	if err != nil {
		function.Status.ApplicationID = state.ApplicationID
		function.Status.FunctionOCID = state.FunctionID
		function.Status.FunctionID = state.FunctionID
		function.Status.InvokeEndpoint = state.InvokeEndpoint
		function.Status.Phase = functionsv1alpha1.FunctionPhaseError
		function.Status.Message = err.Error()
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionFalse,
			Reason:             "ManagedFunctionError",
			Message:            err.Error(),
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return false, nil
	}

	function.Status.ApplicationID = state.ApplicationID
	function.Status.FunctionOCID = state.FunctionID
	function.Status.FunctionID = state.FunctionID
	function.Status.InvokeEndpoint = state.InvokeEndpoint
	function.Status.Message = state.Message
	if function.Status.Message == "" {
		function.Status.Message = "Managed OCI Function is reconciling."
	}

	if state.Ready {
		function.Status.Phase = functionsv1alpha1.FunctionPhaseReady
		function.SetCondition(metav1.Condition{
			Type:               functionsv1alpha1.FunctionConditionReady,
			Status:             metav1.ConditionTrue,
			Reason:             "ManagedFunctionReady",
			Message:            function.Status.Message,
			ObservedGeneration: function.Generation,
			LastTransitionTime: now,
		})
		return false, nil
	}

	function.Status.Phase = functionsv1alpha1.FunctionPhasePending
	function.SetCondition(metav1.Condition{
		Type:               functionsv1alpha1.FunctionConditionReady,
		Status:             metav1.ConditionFalse,
		Reason:             "ManagedFunctionPending",
		Message:            function.Status.Message,
		ObservedGeneration: function.Generation,
		LastTransitionTime: now,
	})
	return true, nil
}

func resolvedFunctionMode(function *functionsv1alpha1.Function) functionsv1alpha1.FunctionMode {
	switch function.Spec.Mode {
	case functionsv1alpha1.FunctionModeExisting, functionsv1alpha1.FunctionModeManaged:
		return function.Spec.Mode
	}
	if resolvedSpecFunctionID(function) != "" {
		return functionsv1alpha1.FunctionModeExisting
	}
	if function.Spec.Config != nil {
		return functionsv1alpha1.FunctionModeManaged
	}
	if function.Spec.ApplicationRef != nil {
		return functionsv1alpha1.FunctionModeManaged
	}
	return ""
}

func resolvedSpecFunctionID(function *functionsv1alpha1.Function) string {
	if function.Spec.FunctionID != "" {
		return strings.TrimSpace(function.Spec.FunctionID)
	}
	return strings.TrimSpace(function.Spec.ExistingFunctionOCID)
}

func shouldHaveFunctionFinalizer(function *functionsv1alpha1.Function, mode functionsv1alpha1.FunctionMode) bool {
	return mode == functionsv1alpha1.FunctionModeManaged &&
		function.DeletionPolicy() == functionsv1alpha1.FunctionDeletionPolicyDelete
}

func desiredFunctionFromSpec(function *functionsv1alpha1.Function) lifecycle.DesiredFunction {
	config := function.Spec.Config
	return lifecycle.DesiredFunction{
		Region:                  strings.TrimSpace(config.Region),
		CompartmentID:           strings.TrimSpace(config.CompartmentID),
		ApplicationName:         strings.TrimSpace(config.ApplicationName),
		SubnetIDs:               trimStringSlice(config.SubnetIDs),
		ApplicationNSGIDs:       trimStringSlice(config.NSGIDs),
		ManageApplicationNSGIDs: config.NSGIDs != nil,
		DisplayName:             strings.TrimSpace(config.DisplayName),
		Image:                   strings.TrimSpace(config.Image),
		MemoryInMBs:             desiredMemoryInMBs(config),
		TimeoutInSeconds:        desiredTimeoutInSeconds(config),
		Config:                  desiredConfigMap(config),
		FreeformTags:            copyStringMap(config.FreeformTags),
	}
}

func desiredFunctionInApplicationFromSpec(function *functionsv1alpha1.Function, application *functionsv1alpha1.FunctionApplication) lifecycle.DesiredFunctionInApplication {
	config := function.Spec.Config
	return lifecycle.DesiredFunctionInApplication{
		Region:           strings.TrimSpace(application.Status.Region),
		ApplicationID:    strings.TrimSpace(application.Status.ApplicationID),
		DisplayName:      strings.TrimSpace(config.DisplayName),
		Image:            strings.TrimSpace(config.Image),
		MemoryInMBs:      desiredMemoryInMBs(config),
		TimeoutInSeconds: desiredTimeoutInSeconds(config),
		Config:           desiredConfigMap(config),
		FreeformTags:     copyStringMap(config.FreeformTags),
	}
}

func managedFunctionDeleteTarget(function *functionsv1alpha1.Function) lifecycle.ManagedFunctionDeleteTarget {
	functionID := strings.TrimSpace(function.Status.FunctionID)
	if functionID == "" {
		functionID = strings.TrimSpace(function.Status.FunctionOCID)
	}
	target := lifecycle.ManagedFunctionDeleteTarget{FunctionID: functionID}
	target.ApplicationID = strings.TrimSpace(function.Status.ApplicationID)
	if function.Spec.Config == nil {
		return target
	}
	target.Region = strings.TrimSpace(function.Spec.Config.Region)
	target.CompartmentID = strings.TrimSpace(function.Spec.Config.CompartmentID)
	target.ApplicationName = strings.TrimSpace(function.Spec.Config.ApplicationName)
	target.DisplayName = strings.TrimSpace(function.Spec.Config.DisplayName)
	return target
}

func hasLegacyApplicationFields(config *functionsv1alpha1.FunctionConfig) bool {
	if config == nil {
		return false
	}
	return strings.TrimSpace(config.Region) != "" ||
		strings.TrimSpace(config.CompartmentID) != "" ||
		strings.TrimSpace(config.ApplicationName) != "" ||
		strings.TrimSpace(config.ApplicationOCID) != "" ||
		len(config.SubnetIDs) > 0 ||
		config.NSGIDs != nil
}

func validateLegacyManagedFunctionConfig(config *functionsv1alpha1.FunctionConfig) error {
	switch {
	case strings.TrimSpace(config.Region) == "":
		return fmt.Errorf("managed Function requires spec.config.region when spec.applicationRef is not set")
	case strings.TrimSpace(config.CompartmentID) == "":
		return fmt.Errorf("managed Function requires spec.config.compartmentId when spec.applicationRef is not set")
	case strings.TrimSpace(config.ApplicationName) == "":
		return fmt.Errorf("managed Function requires spec.config.applicationName when spec.applicationRef is not set")
	case len(config.SubnetIDs) == 0:
		return fmt.Errorf("managed Function requires spec.config.subnetIds when spec.applicationRef is not set")
	}
	return nil
}

func deletionErrorStatus(function *functionsv1alpha1.Function, now metav1.Time, reason, message string) functionsv1alpha1.FunctionStatus {
	status := function.Status
	status.ObservedGeneration = function.Generation
	status.Phase = functionsv1alpha1.FunctionPhaseError
	status.Message = message
	setFunctionReadyCondition(&status, metav1.ConditionFalse, reason, message, function.Generation, now)
	return status
}

func functionDeletionBackoff(function *functionsv1alpha1.Function, now time.Time) (time.Duration, bool) {
	if !isFunctionDeleteFailure(function) || function.Status.LastSyncTime == nil {
		return 0, false
	}
	elapsed := now.Sub(function.Status.LastSyncTime.Time)
	if elapsed >= functionDeleteRequeue {
		return 0, false
	}
	return functionDeleteRequeue - elapsed, true
}

func isFunctionDeleteFailure(function *functionsv1alpha1.Function) bool {
	if function.Status.Phase != functionsv1alpha1.FunctionPhaseError {
		return false
	}
	for _, condition := range function.Status.Conditions {
		if condition.Type != functionsv1alpha1.FunctionConditionReady {
			continue
		}
		return condition.Status == metav1.ConditionFalse &&
			(condition.Reason == "ManagedFunctionDeleteFailed" || condition.Reason == "LifecycleManagerNotConfigured")
	}
	return false
}

func setFunctionReadyCondition(status *functionsv1alpha1.FunctionStatus, conditionStatus metav1.ConditionStatus, reason, message string, generation int64, now metav1.Time) {
	condition := metav1.Condition{
		Type:               functionsv1alpha1.FunctionConditionReady,
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

func (r *FunctionReconciler) updateFunctionStatusIfChanged(ctx context.Context, function *functionsv1alpha1.Function, desired functionsv1alpha1.FunctionStatus, updateLastSync bool) (bool, error) {
	current := function.Status
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
	function.Status = desired
	if err := r.Status().Update(ctx, function); err != nil {
		return false, err
	}
	return true, nil
}

func normalizeFunctionLifecycleError(operation string, err error) string {
	if err == nil {
		return ensureSentence(fmt.Sprintf("%s failed", operation))
	}
	message := sanitizeOCIErrorText(err.Error())
	if message == "" {
		message = "OCI Functions API request failed"
	}
	return ensureSentence(fmt.Sprintf("%s failed: %s", operation, message))
}

func desiredMemoryInMBs(config *functionsv1alpha1.FunctionConfig) int64 {
	if config.MemoryInMBs > 0 {
		return int64(config.MemoryInMBs)
	}
	if config.MemoryInMB > 0 {
		return int64(config.MemoryInMB)
	}
	return 128
}

func desiredTimeoutInSeconds(config *functionsv1alpha1.FunctionConfig) int {
	if config.TimeoutInSeconds > 0 {
		return int(config.TimeoutInSeconds)
	}
	return 30
}

func desiredConfigMap(config *functionsv1alpha1.FunctionConfig) map[string]string {
	if len(config.Config) > 0 {
		return copyStringMap(config.Config)
	}
	return copyStringMap(config.Environment)
}

func copyStringMap(values map[string]string) map[string]string {
	if len(values) == 0 {
		return nil
	}
	copied := make(map[string]string, len(values))
	for key, value := range values {
		copied[key] = value
	}
	return copied
}

func trimStringSlice(values []string) []string {
	if values == nil {
		return nil
	}
	trimmed := make([]string, len(values))
	for i := range values {
		trimmed[i] = strings.TrimSpace(values[i])
	}
	return trimmed
}

func (r *FunctionReconciler) recordLifecycleEvents(function *functionsv1alpha1.Function, events []lifecycle.Event) {
	if r.Recorder == nil {
		return
	}
	for _, event := range events {
		eventType := corev1.EventTypeNormal
		if event.Type == lifecycle.EventTypeWarning {
			eventType = corev1.EventTypeWarning
		}
		r.Recorder.Event(function, eventType, event.Reason, event.Message)
	}
}

func (r *FunctionReconciler) recordFunctionEvent(function *functionsv1alpha1.Function, eventType, reason, message string) {
	if r.Recorder == nil {
		return
	}
	r.Recorder.Event(function, eventType, reason, message)
}

// SetupWithManager sets up the controller with the Manager.
func (r *FunctionReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&functionsv1alpha1.Function{}).
		Complete(r)
}
