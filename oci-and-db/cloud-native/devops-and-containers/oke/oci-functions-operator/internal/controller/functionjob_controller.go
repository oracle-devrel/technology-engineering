// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package controller

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"reflect"
	"strings"

	functionsv1alpha1 "github.com/oracle/oci-functions-operator/api/v1alpha1"
	"github.com/oracle/oci-functions-operator/internal/invoker"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

const (
	functionJobEventInvocationFailed = "InvocationFailed"
	functionJobEventComplete         = "Complete"
	functionJobEventFailed           = "Failed"
)

// FunctionJobReconciler reconciles a FunctionJob object.
type FunctionJobReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Invoker  invoker.Interface
	Recorder record.EventRecorder
}

// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functionjobs,verbs=get;list;watch
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functionjobs/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functionjobs/finalizers,verbs=update
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functions,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

// Reconcile resolves the referenced Function and invokes pending payloads idempotently.
func (r *FunctionJobReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var job functionsv1alpha1.FunctionJob
	if err := r.Get(ctx, req.NamespacedName, &job); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	if job.IsTerminal() {
		return ctrl.Result{}, nil
	}

	now := metav1.Now()
	desiredObject := job.DeepCopy()
	desiredObject.Status.ObservedGeneration = job.Generation
	if desiredObject.Status.StartTime == nil {
		desiredObject.Status.StartTime = &now
	}

	if job.Spec.FunctionRef.Name == "" {
		desiredObject.Status.Phase = functionsv1alpha1.FunctionJobPhaseFailed
		desiredObject.Status.CompletionTime = &now
		setJobConditions(desiredObject, now, conditionSet{
			Pending:  conditionState{Status: metav1.ConditionFalse, Reason: "InvalidFunctionRef", Message: "FunctionJob has an invalid function reference."},
			Running:  conditionState{Status: metav1.ConditionFalse, Reason: "InvalidFunctionRef", Message: "FunctionJob cannot run with an invalid function reference."},
			Complete: conditionState{Status: metav1.ConditionFalse, Reason: "InvalidFunctionRef", Message: "FunctionJob did not complete."},
			Failed:   conditionState{Status: metav1.ConditionTrue, Reason: "InvalidFunctionRef", Message: "spec.functionRef.name is required."},
		})
		r.recordEvent(&job, corev1.EventTypeWarning, functionJobEventFailed, "FunctionJob failed: spec.functionRef.name is required.")
		return ctrl.Result{}, r.updateFunctionJobStatus(ctx, &job, desiredObject.Status)
	}

	var function functionsv1alpha1.Function
	functionKey := types.NamespacedName{Namespace: job.Namespace, Name: job.Spec.FunctionRef.Name}
	if err := r.Get(ctx, functionKey, &function); err != nil {
		if !apierrors.IsNotFound(err) {
			return ctrl.Result{}, err
		}
		markWaitingForFunction(desiredObject, now, "FunctionNotFound", "Referenced Function was not found in the FunctionJob namespace.")
		return ctrl.Result{}, r.updateFunctionJobStatus(ctx, &job, desiredObject.Status)
	}

	target := invocationTargetForFunction(&function)
	if !functionReadyForInvocation(&function, target) {
		markFunctionNotReady(desiredObject, now, &function, target)
		r.recordEvent(&job, corev1.EventTypeWarning, functionJobEventFailed, desiredObject.Status.LastError)
		return ctrl.Result{}, r.updateFunctionJobStatus(ctx, &job, desiredObject.Status)
	}

	desiredObject.SetCondition(metav1.Condition{
		Type:               functionsv1alpha1.FunctionJobConditionFunctionResolved,
		Status:             metav1.ConditionTrue,
		Reason:             "FunctionReady",
		Message:            "Referenced Function is ready for invocation.",
		ObservedGeneration: job.Generation,
		LastTransitionTime: now,
	})

	payloads := inlinePayloads(&job)
	ensurePayloadStatuses(&desiredObject.Status, payloads)
	recomputeInvocationCounts(&desiredObject.Status)

	inv := r.Invoker
	if inv == nil {
		markInvokerNotConfigured(desiredObject, now)
		return ctrl.Result{}, r.updateFunctionJobStatus(ctx, &job, desiredObject.Status)
	}
	if requiresFunctionID(inv) && target.FunctionOCID == "" {
		markFunctionIDRequired(desiredObject, now, function.Name)
		r.recordEvent(&job, corev1.EventTypeWarning, functionJobEventFailed, desiredObject.Status.LastError)
		return ctrl.Result{}, r.updateFunctionJobStatus(ctx, &job, desiredObject.Status)
	}

	processed, err := r.invokeRunnablePayloads(ctx, inv, &job, target, desiredObject, payloads, now)
	if err != nil {
		if errors.Is(err, invoker.ErrNotImplemented) {
			markInvokerNotConfigured(desiredObject, now)
			return ctrl.Result{}, r.updateFunctionJobStatus(ctx, &job, desiredObject.Status)
		}
		return ctrl.Result{}, err
	}

	recomputeInvocationCounts(&desiredObject.Status)
	terminalBefore := job.IsTerminal()
	r.summarizeInvocationState(&job, desiredObject, payloads, now)

	if !terminalBefore && desiredObject.IsTerminal() {
		if desiredObject.Status.Phase == functionsv1alpha1.FunctionJobPhaseSucceeded {
			r.recordEvent(&job, corev1.EventTypeNormal, functionJobEventComplete, "FunctionJob completed: all payloads succeeded.")
		} else {
			r.recordEvent(&job, corev1.EventTypeWarning, functionJobEventFailed, "FunctionJob failed: one or more payloads failed after retries.")
		}
	}

	if err := r.updateFunctionJobStatus(ctx, &job, desiredObject.Status); err != nil {
		return ctrl.Result{}, err
	}

	logger.V(1).Info("updated FunctionJob status", "phase", desiredObject.Status.Phase, "processed", processed)
	if desiredObject.Status.Phase == functionsv1alpha1.FunctionJobPhaseRunning && hasRunnablePayload(desiredObject.Status.InvocationStatuses, job.DesiredRetryLimit()) {
		return ctrl.Result{Requeue: true}, nil
	}
	return ctrl.Result{}, nil
}

func markWaitingForFunction(job *functionsv1alpha1.FunctionJob, now metav1.Time, reason, message string) {
	job.Status.Phase = functionsv1alpha1.FunctionJobPhasePending
	job.Status.Active = 0
	job.SetCondition(metav1.Condition{
		Type:               functionsv1alpha1.FunctionJobConditionFunctionResolved,
		Status:             metav1.ConditionFalse,
		Reason:             reason,
		Message:            message,
		ObservedGeneration: job.Generation,
		LastTransitionTime: now,
	})
	setJobConditions(job, now, conditionSet{
		Pending:  conditionState{Status: metav1.ConditionTrue, Reason: reason, Message: message},
		Running:  conditionState{Status: metav1.ConditionFalse, Reason: "WaitingForFunction", Message: "Waiting for the referenced Function to become ready."},
		Complete: conditionState{Status: metav1.ConditionFalse, Reason: "WaitingForFunction", Message: "FunctionJob has not completed."},
		Failed:   conditionState{Status: metav1.ConditionFalse, Reason: "WaitingForFunction", Message: "FunctionJob has not failed."},
	})
}

func markFunctionNotReady(job *functionsv1alpha1.FunctionJob, now metav1.Time, function *functionsv1alpha1.Function, target invoker.Target) {
	job.Status.Phase = functionsv1alpha1.FunctionJobPhaseFailed
	job.Status.Active = 0
	job.Status.LastError = functionNotReadyMessage(function, target)
	if job.Status.CompletionTime == nil {
		job.Status.CompletionTime = &now
	}
	job.SetCondition(metav1.Condition{
		Type:               functionsv1alpha1.FunctionJobConditionFunctionResolved,
		Status:             metav1.ConditionFalse,
		Reason:             "FunctionNotReady",
		Message:            job.Status.LastError,
		ObservedGeneration: job.Generation,
		LastTransitionTime: now,
	})
	setJobConditions(job, now, conditionSet{
		Pending:  conditionState{Status: metav1.ConditionFalse, Reason: "FunctionNotReady", Message: "Referenced Function is not ready."},
		Running:  conditionState{Status: metav1.ConditionFalse, Reason: "FunctionNotReady", Message: "FunctionJob cannot run until the referenced Function is ready."},
		Complete: conditionState{Status: metav1.ConditionFalse, Reason: "FunctionNotReady", Message: "FunctionJob did not complete."},
		Failed:   conditionState{Status: metav1.ConditionTrue, Reason: "FunctionNotReady", Message: job.Status.LastError},
	})
}

func markInvokerNotConfigured(job *functionsv1alpha1.FunctionJob, now metav1.Time) {
	job.Status.Phase = functionsv1alpha1.FunctionJobPhasePending
	job.Status.Active = 0
	job.Status.LastError = "invoker is not configured"
	setJobConditions(job, now, conditionSet{
		Pending:  conditionState{Status: metav1.ConditionTrue, Reason: "InvokerNotConfigured", Message: "OCI Functions invocation is not implemented yet."},
		Running:  conditionState{Status: metav1.ConditionFalse, Reason: "InvokerNotConfigured", Message: "FunctionJob cannot run until an invoker is configured."},
		Complete: conditionState{Status: metav1.ConditionFalse, Reason: "InvokerNotConfigured", Message: "FunctionJob has not completed."},
		Failed:   conditionState{Status: metav1.ConditionFalse, Reason: "InvokerNotConfigured", Message: "FunctionJob has not failed."},
	})
}

func markFunctionIDRequired(job *functionsv1alpha1.FunctionJob, now metav1.Time, functionName string) {
	job.Status.Phase = functionsv1alpha1.FunctionJobPhaseFailed
	job.Status.Active = 0
	job.Status.LastError = fmt.Sprintf("OCI mode requires referenced Function %q to resolve status.functionId", functionName)
	if job.Status.CompletionTime == nil {
		job.Status.CompletionTime = &now
	}
	setJobConditions(job, now, conditionSet{
		Pending:  conditionState{Status: metav1.ConditionFalse, Reason: "FunctionIDRequired", Message: "Referenced Function is missing status.functionId."},
		Running:  conditionState{Status: metav1.ConditionFalse, Reason: "FunctionIDRequired", Message: "FunctionJob cannot run without status.functionId in OCI mode."},
		Complete: conditionState{Status: metav1.ConditionFalse, Reason: "FunctionIDRequired", Message: "FunctionJob did not complete."},
		Failed:   conditionState{Status: metav1.ConditionTrue, Reason: "FunctionIDRequired", Message: job.Status.LastError},
	})
}

func (r *FunctionJobReconciler) invokeRunnablePayloads(ctx context.Context, inv invoker.Interface, job *functionsv1alpha1.FunctionJob, target invoker.Target, desired *functionsv1alpha1.FunctionJob, payloads [][]byte, now metav1.Time) (int32, error) {
	limit := job.DesiredParallelism()
	retryLimit := job.DesiredRetryLimit()
	maxAttempts := retryLimit + 1
	var processed int32

	for i := range desired.Status.InvocationStatuses {
		if processed >= limit {
			break
		}

		status := &desired.Status.InvocationStatuses[i]
		if !isRunnablePayload(*status, retryLimit) {
			continue
		}

		processed++
		status.Phase = functionsv1alpha1.InvocationPhaseRunning
		for status.Attempts < maxAttempts {
			response, err := inv.Invoke(ctx, invoker.Request{
				Target: target,
				Index:  status.Index,
				Body:   payloads[status.Index],
			})
			if errors.Is(err, invoker.ErrNotImplemented) {
				status.Phase = functionsv1alpha1.InvocationPhasePending
				return processed, err
			}

			status.Attempts++
			status.InvocationID = response.InvocationID
			status.OCIRequestID = response.OCIRequestID
			status.StatusCode = response.StatusCode
			if response.OCIRequestID != "" {
				desired.Status.LastOCIRequestID = response.OCIRequestID
			}
			if err == nil {
				status.Phase = functionsv1alpha1.InvocationPhaseSucceeded
				status.Error = ""
				status.CompletedAt = &now
				break
			}

			status.Error = err.Error()
			desired.Status.LastError = status.Error
			if status.Attempts >= maxAttempts {
				status.Phase = functionsv1alpha1.InvocationPhaseFailed
				status.CompletedAt = &now
				r.recordEvent(job, corev1.EventTypeWarning, functionJobEventInvocationFailed, fmt.Sprintf("Payload index %d failed after %d attempt(s): %s", status.Index, status.Attempts, status.Error))
				break
			}
		}
	}

	return processed, nil
}

func (r *FunctionJobReconciler) summarizeInvocationState(original *functionsv1alpha1.FunctionJob, desired *functionsv1alpha1.FunctionJob, payloads [][]byte, now metav1.Time) {
	total := int32(len(payloads))
	terminal := desired.Status.Succeeded+desired.Status.Failed == total

	switch {
	case total == 0:
		desired.Status.Phase = functionsv1alpha1.FunctionJobPhaseSucceeded
		if desired.Status.CompletionTime == nil {
			desired.Status.CompletionTime = &now
		}
		setJobConditions(desired, now, conditionSet{
			Pending:  conditionState{Status: metav1.ConditionFalse, Reason: "NoPayloads", Message: "FunctionJob has no payloads to invoke."},
			Running:  conditionState{Status: metav1.ConditionFalse, Reason: "NoPayloads", Message: "FunctionJob has no running payloads."},
			Complete: conditionState{Status: metav1.ConditionTrue, Reason: "NoPayloads", Message: "FunctionJob completed without payloads."},
			Failed:   conditionState{Status: metav1.ConditionFalse, Reason: "NoFailedInvocations", Message: "No payload failures were observed."},
		})
	case desired.Status.Failed > 0 && terminal:
		desired.Status.Phase = functionsv1alpha1.FunctionJobPhaseFailed
		if desired.Status.CompletionTime == nil {
			desired.Status.CompletionTime = &now
		}
		setJobConditions(desired, now, conditionSet{
			Pending:  conditionState{Status: metav1.ConditionFalse, Reason: "PayloadsTerminal", Message: "All payloads reached a terminal state."},
			Running:  conditionState{Status: metav1.ConditionFalse, Reason: "PayloadsTerminal", Message: "FunctionJob has no remaining runnable payloads."},
			Complete: conditionState{Status: metav1.ConditionFalse, Reason: "InvocationFailed", Message: "One or more function invocations failed after retries."},
			Failed:   conditionState{Status: metav1.ConditionTrue, Reason: "InvocationFailed", Message: "One or more function invocations failed after retries."},
		})
	case desired.Status.Succeeded == total:
		desired.Status.Phase = functionsv1alpha1.FunctionJobPhaseSucceeded
		desired.Status.LastError = ""
		if desired.Status.CompletionTime == nil {
			desired.Status.CompletionTime = &now
		}
		setJobConditions(desired, now, conditionSet{
			Pending:  conditionState{Status: metav1.ConditionFalse, Reason: "AllInvocationsSucceeded", Message: "All requested payloads were invoked."},
			Running:  conditionState{Status: metav1.ConditionFalse, Reason: "AllInvocationsSucceeded", Message: "FunctionJob has no remaining runnable payloads."},
			Complete: conditionState{Status: metav1.ConditionTrue, Reason: "AllInvocationsSucceeded", Message: "All requested function invocations succeeded."},
			Failed:   conditionState{Status: metav1.ConditionFalse, Reason: "NoFailedInvocations", Message: "No invocation failures were observed."},
		})
	default:
		desired.Status.Phase = functionsv1alpha1.FunctionJobPhaseRunning
		desired.Status.CompletionTime = nil
		setJobConditions(desired, now, conditionSet{
			Pending:  conditionState{Status: metav1.ConditionFalse, Reason: "FunctionReady", Message: "FunctionJob has started invoking payloads."},
			Running:  conditionState{Status: metav1.ConditionTrue, Reason: "PayloadsRemaining", Message: "FunctionJob has remaining payloads to invoke."},
			Complete: conditionState{Status: metav1.ConditionFalse, Reason: "PayloadsRemaining", Message: "FunctionJob has not completed."},
			Failed:   conditionState{Status: metav1.ConditionFalse, Reason: "PayloadsRemaining", Message: "FunctionJob has not failed."},
		})
	}

	if original.Status.Phase != desired.Status.Phase {
		desired.Status.ObservedGeneration = desired.Generation
	}
}

func inlinePayloads(job *functionsv1alpha1.FunctionJob) [][]byte {
	if len(job.Spec.Payloads) > 0 {
		payloads := make([][]byte, 0, len(job.Spec.Payloads))
		for i := range job.Spec.Payloads {
			payloads = append(payloads, job.Spec.Payloads[i].Raw)
		}
		return payloads
	}
	if job.Spec.Payload != nil {
		return [][]byte{job.Spec.Payload.Raw}
	}
	return [][]byte{nil}
}

func ensurePayloadStatuses(status *functionsv1alpha1.FunctionJobStatus, payloads [][]byte) {
	existingByIndex := make(map[int32]functionsv1alpha1.FunctionJobInvocationStatus, len(status.InvocationStatuses))
	for _, invocationStatus := range status.InvocationStatuses {
		existingByIndex[invocationStatus.Index] = invocationStatus
	}

	next := make([]functionsv1alpha1.FunctionJobInvocationStatus, 0, len(payloads))
	for i, payload := range payloads {
		index := int32(i)
		digest := digestPayload(payload)
		invocationStatus, ok := existingByIndex[index]
		if !ok || invocationStatus.PayloadDigest != digest {
			invocationStatus = functionsv1alpha1.FunctionJobInvocationStatus{
				Index:         index,
				PayloadDigest: digest,
				Phase:         functionsv1alpha1.InvocationPhasePending,
			}
		}
		if invocationStatus.PayloadDigest == "" {
			invocationStatus.PayloadDigest = digest
		}
		if invocationStatus.Phase == "" {
			invocationStatus.Phase = functionsv1alpha1.InvocationPhasePending
		}
		next = append(next, invocationStatus)
	}
	status.InvocationStatuses = next
}

func digestPayload(payload []byte) string {
	sum := sha256.Sum256(payload)
	return "sha256:" + hex.EncodeToString(sum[:])
}

func recomputeInvocationCounts(status *functionsv1alpha1.FunctionJobStatus) {
	status.Active = 0
	status.Succeeded = 0
	status.Failed = 0
	status.Retries = 0

	for _, invocationStatus := range status.InvocationStatuses {
		switch invocationStatus.Phase {
		case functionsv1alpha1.InvocationPhaseRunning:
			status.Active++
		case functionsv1alpha1.InvocationPhaseSucceeded:
			status.Succeeded++
		case functionsv1alpha1.InvocationPhaseFailed:
			status.Failed++
		}
		if invocationStatus.Attempts > 1 {
			status.Retries += invocationStatus.Attempts - 1
		}
	}
}

func isRunnablePayload(status functionsv1alpha1.FunctionJobInvocationStatus, retryLimit int32) bool {
	if status.Phase == functionsv1alpha1.InvocationPhaseSucceeded {
		return false
	}
	if status.Phase == functionsv1alpha1.InvocationPhaseFailed && status.Attempts >= retryLimit+1 {
		return false
	}
	return true
}

func hasRunnablePayload(statuses []functionsv1alpha1.FunctionJobInvocationStatus, retryLimit int32) bool {
	for _, status := range statuses {
		if isRunnablePayload(status, retryLimit) {
			return true
		}
	}
	return false
}

func invocationTargetForFunction(function *functionsv1alpha1.Function) invoker.Target {
	functionID := strings.TrimSpace(function.Status.FunctionID)
	if functionID == "" {
		functionID = strings.TrimSpace(function.Status.FunctionOCID)
	}
	invokeEndpoint := strings.TrimSpace(function.Status.InvokeEndpoint)

	if resolvedFunctionMode(function) == functionsv1alpha1.FunctionModeExisting {
		if functionID == "" {
			functionID = resolvedSpecFunctionID(function)
		}
		if invokeEndpoint == "" {
			invokeEndpoint = strings.TrimSpace(function.Spec.InvokeEndpoint)
		}
	}

	return invoker.Target{
		Namespace:      function.Namespace,
		FunctionName:   function.Name,
		FunctionOCID:   functionID,
		InvokeEndpoint: invokeEndpoint,
	}
}

func functionReadyForInvocation(function *functionsv1alpha1.Function, target invoker.Target) bool {
	if target.FunctionOCID == "" || target.InvokeEndpoint == "" {
		return false
	}
	return function.IsReady()
}

func functionNotReadyMessage(function *functionsv1alpha1.Function, target invoker.Target) string {
	details := []string{}
	condition := meta.FindStatusCondition(function.Status.Conditions, functionsv1alpha1.FunctionConditionReady)
	switch {
	case condition == nil:
		details = append(details, "Ready condition is missing")
	case condition.Status != metav1.ConditionTrue:
		message := fmt.Sprintf("Ready=%s", condition.Status)
		if condition.Reason != "" {
			message += " reason=" + condition.Reason
		}
		if condition.Message != "" {
			message += " message=" + condition.Message
		}
		details = append(details, message)
	}
	if target.FunctionOCID == "" {
		details = append(details, "function OCID is missing")
	}
	if target.InvokeEndpoint == "" {
		details = append(details, "invoke endpoint is missing")
	}
	if len(details) == 0 {
		details = append(details, "Ready condition is false")
	}
	return fmt.Sprintf("referenced Function %q is not Ready: %s", function.Name, strings.Join(details, "; "))
}

func requiresFunctionID(inv invoker.Interface) bool {
	requirement, ok := inv.(invoker.FunctionIDRequirement)
	return ok && requirement.RequiresFunctionID()
}

type conditionSet struct {
	Pending  conditionState
	Running  conditionState
	Complete conditionState
	Failed   conditionState
}

type conditionState struct {
	Status  metav1.ConditionStatus
	Reason  string
	Message string
}

func setJobConditions(job *functionsv1alpha1.FunctionJob, now metav1.Time, conditions conditionSet) {
	setJobCondition(job, now, functionsv1alpha1.FunctionJobConditionPending, conditions.Pending)
	setJobCondition(job, now, functionsv1alpha1.FunctionJobConditionRunning, conditions.Running)
	setJobCondition(job, now, functionsv1alpha1.FunctionJobConditionComplete, conditions.Complete)
	setJobCondition(job, now, functionsv1alpha1.FunctionJobConditionFailed, conditions.Failed)
}

func setJobCondition(job *functionsv1alpha1.FunctionJob, now metav1.Time, conditionType string, condition conditionState) {
	job.SetCondition(metav1.Condition{
		Type:               conditionType,
		Status:             condition.Status,
		Reason:             condition.Reason,
		Message:            condition.Message,
		ObservedGeneration: job.Generation,
		LastTransitionTime: now,
	})
}

func (r *FunctionJobReconciler) recordEvent(job *functionsv1alpha1.FunctionJob, eventType, reason, message string) {
	if r.Recorder == nil {
		return
	}
	r.Recorder.Event(job, eventType, reason, message)
}

func (r *FunctionJobReconciler) updateFunctionJobStatus(ctx context.Context, job *functionsv1alpha1.FunctionJob, desired functionsv1alpha1.FunctionJobStatus) error {
	if reflect.DeepEqual(job.Status, desired) {
		return nil
	}
	job.Status = desired
	return r.Status().Update(ctx, job)
}

// SetupWithManager sets up the controller with the Manager.
func (r *FunctionJobReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&functionsv1alpha1.FunctionJob{}).
		Complete(r)
}
