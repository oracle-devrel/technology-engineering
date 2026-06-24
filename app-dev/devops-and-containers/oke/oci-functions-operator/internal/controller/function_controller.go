// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package controller

import (
	"context"
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
	"sigs.k8s.io/controller-runtime/pkg/log"
)

// FunctionReconciler reconciles a Function object.
type FunctionReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Manager  lifecycle.Manager
	Recorder record.EventRecorder
}

// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functions,verbs=get;list;watch
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

	now := metav1.Now()
	desiredObject := function.DeepCopy()
	desiredObject.Status = functionsv1alpha1.FunctionStatus{
		ObservedGeneration: function.Generation,
	}

	result := ctrl.Result{}
	mode := resolvedFunctionMode(&function)

	switch mode {
	case functionsv1alpha1.FunctionModeExisting:
		reconcileExistingFunctionStatus(desiredObject, now)
	case functionsv1alpha1.FunctionModeManaged:
		pending, err := r.reconcileManagedFunctionStatus(ctx, desiredObject, now)
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

	desired := desiredObject.Status
	if reflect.DeepEqual(function.Status, desired) {
		return result, nil
	}

	desired.LastSyncTime = &now
	function.Status = desired
	if err := r.Status().Update(ctx, &function); err != nil {
		return ctrl.Result{}, err
	}

	logger.V(1).Info("updated Function status", "phase", function.Status.Phase)
	return result, nil
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
	return ""
}

func resolvedSpecFunctionID(function *functionsv1alpha1.Function) string {
	if function.Spec.FunctionID != "" {
		return strings.TrimSpace(function.Spec.FunctionID)
	}
	return strings.TrimSpace(function.Spec.ExistingFunctionOCID)
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

// SetupWithManager sets up the controller with the Manager.
func (r *FunctionReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&functionsv1alpha1.Function{}).
		Complete(r)
}
