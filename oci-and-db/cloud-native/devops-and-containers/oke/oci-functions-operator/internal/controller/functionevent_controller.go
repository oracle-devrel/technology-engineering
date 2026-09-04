// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package controller

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"reflect"
	"sort"
	"strings"
	"time"

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
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
)

const (
	functionEventTypePrefix = "functionevent."

	functionEventRetryLimit   int32 = 3
	functionEventRetryBackoff       = 30 * time.Second

	functionEventEventProcessed = "Processed"
	functionEventEventFailed    = "Failed"
)

type functionEventTriggerMode string

const (
	functionEventTriggerModeOCI           functionEventTriggerMode = "oci"
	functionEventTriggerModeFunctionEvent functionEventTriggerMode = "functionevent"
	functionEventTriggerModeMixed         functionEventTriggerMode = "mixed"
)

// FunctionEventReconciler reconciles Kubernetes-native FunctionEvent objects.
type FunctionEventReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Invoker  invoker.Interface
	Recorder record.EventRecorder
}

// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functionevents,verbs=get;list;watch;update;patch;delete
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functionevents/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functioneventtriggers,verbs=get;list;watch
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functions,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

// Reconcile routes a FunctionEvent to same-namespace FunctionEventTriggers with matching condition.eventType.
func (r *FunctionEventReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var event functionsv1alpha1.FunctionEvent
	if err := r.Get(ctx, req.NamespacedName, &event); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	if event.Status.ObservedGeneration == event.Generation && event.Status.Phase == functionsv1alpha1.FunctionEventPhaseProcessed {
		return r.reconcileProcessedTTL(ctx, &event)
	}
	if event.Status.ObservedGeneration == event.Generation && event.Status.Phase == functionsv1alpha1.FunctionEventPhaseFailed {
		return ctrl.Result{}, nil
	}

	now := metav1.Now()
	desired := event.DeepCopy()
	desired.Status.ObservedGeneration = event.Generation

	if !isFunctionEventType(event.Spec.EventType) {
		message := fmt.Sprintf("FunctionEvent spec.eventType %q must start with %q.", event.Spec.EventType, functionEventTypePrefix)
		markFunctionEventFailed(desired, now, "InvalidEventType", message)
		r.recordEvent(&event, corev1.EventTypeWarning, functionEventEventFailed, message)
		return ctrl.Result{}, r.updateFunctionEventStatus(ctx, &event, desired.Status)
	}

	triggers, err := r.matchingFunctionEventTriggers(ctx, &event)
	if err != nil {
		return ctrl.Result{}, err
	}
	if len(triggers) == 0 {
		desired.Status.MatchedTriggers = nil
		desired.Status.Invocations = nil
		markFunctionEventProcessed(desired, now, "NoMatchingTriggers", "No matching triggers")
		r.recordEvent(&event, corev1.EventTypeNormal, functionEventEventProcessed, "FunctionEvent processed: no matching triggers.")
		if err := r.updateFunctionEventStatus(ctx, &event, desired.Status); err != nil {
			return ctrl.Result{}, err
		}
		return r.requeueAfterProcessedTTL(desired)
	}

	desired.Status.MatchedTriggers = functionEventTriggerNames(triggers)
	ensureFunctionEventInvocationStatuses(&desired.Status, triggers)

	requeueAfter := time.Duration(0)
	inv := r.Invoker
	if inv == nil {
		for i := range desired.Status.Invocations {
			desired.Status.Invocations[i].Phase = functionsv1alpha1.FunctionEventInvocationPhasePending
			desired.Status.Invocations[i].Message = "invoker is not configured"
		}
		markFunctionEventProcessing(desired, now, "InvokerNotConfigured", "FunctionEvent is waiting for an invoker.")
		requeueAfter = functionEventRetryBackoff
	} else {
		requeueAfter, err = r.invokeMatchedTriggers(ctx, inv, &event, desired, triggers, now)
		if err != nil {
			if errors.Is(err, invoker.ErrNotImplemented) {
				markFunctionEventProcessing(desired, now, "InvokerNotConfigured", "FunctionEvent is waiting for an implemented invoker.")
				requeueAfter = functionEventRetryBackoff
			} else {
				return ctrl.Result{}, err
			}
		}
	}

	if desired.Status.Phase == "" || desired.Status.Phase == functionsv1alpha1.FunctionEventPhasePending || desired.Status.Phase == functionsv1alpha1.FunctionEventPhaseProcessing {
		summarizeFunctionEvent(desired, now)
	}

	if !event.IsTerminal() && desired.IsTerminal() {
		switch desired.Status.Phase {
		case functionsv1alpha1.FunctionEventPhaseProcessed:
			r.recordEvent(&event, corev1.EventTypeNormal, functionEventEventProcessed, "FunctionEvent processed: all matching trigger invocations succeeded.")
		case functionsv1alpha1.FunctionEventPhaseFailed:
			r.recordEvent(&event, corev1.EventTypeWarning, functionEventEventFailed, desired.Status.Message)
		}
	}

	if err := r.updateFunctionEventStatus(ctx, &event, desired.Status); err != nil {
		return ctrl.Result{}, err
	}

	logger.V(1).Info("updated FunctionEvent status", "phase", desired.Status.Phase, "matchedTriggers", len(desired.Status.MatchedTriggers))
	if desired.Status.Phase == functionsv1alpha1.FunctionEventPhaseProcessed {
		return r.requeueAfterProcessedTTL(desired)
	}
	if requeueAfter > 0 {
		return ctrl.Result{RequeueAfter: requeueAfter}, nil
	}
	return ctrl.Result{}, nil
}

func (r *FunctionEventReconciler) reconcileProcessedTTL(ctx context.Context, event *functionsv1alpha1.FunctionEvent) (ctrl.Result, error) {
	if event.Spec.TTLSecondsAfterProcessed == nil {
		return ctrl.Result{}, nil
	}
	processed := meta.FindStatusCondition(event.Status.Conditions, functionsv1alpha1.FunctionEventConditionProcessed)
	if processed == nil || processed.Status != metav1.ConditionTrue {
		return ctrl.Result{RequeueAfter: time.Second}, nil
	}
	ttl := time.Duration(*event.Spec.TTLSecondsAfterProcessed) * time.Second
	deleteAfter := processed.LastTransitionTime.Time.Add(ttl)
	if time.Now().Before(deleteAfter) {
		return ctrl.Result{RequeueAfter: time.Until(deleteAfter)}, nil
	}
	return ctrl.Result{}, client.IgnoreNotFound(r.Delete(ctx, event))
}

func (r *FunctionEventReconciler) requeueAfterProcessedTTL(event *functionsv1alpha1.FunctionEvent) (ctrl.Result, error) {
	if event.Spec.TTLSecondsAfterProcessed == nil {
		return ctrl.Result{}, nil
	}
	ttl := time.Duration(*event.Spec.TTLSecondsAfterProcessed) * time.Second
	if ttl <= 0 {
		ttl = time.Second
	}
	return ctrl.Result{RequeueAfter: ttl}, nil
}

func (r *FunctionEventReconciler) matchingFunctionEventTriggers(ctx context.Context, event *functionsv1alpha1.FunctionEvent) ([]functionsv1alpha1.FunctionEventTrigger, error) {
	var triggers functionsv1alpha1.FunctionEventTriggerList
	if err := r.List(ctx, &triggers, client.InNamespace(event.Namespace)); err != nil {
		return nil, err
	}

	matches := []functionsv1alpha1.FunctionEventTrigger{}
	for _, trigger := range triggers.Items {
		if !trigger.RuleEnabled() || classifyFunctionEventTrigger(&trigger) != functionEventTriggerModeFunctionEvent {
			continue
		}
		if functionEventTriggerMatchesEvent(&trigger, event.Spec.EventType) {
			matches = append(matches, trigger)
		}
	}
	sort.Slice(matches, func(i, j int) bool { return matches[i].Name < matches[j].Name })
	return matches, nil
}

func (r *FunctionEventReconciler) invokeMatchedTriggers(ctx context.Context, inv invoker.Interface, original *functionsv1alpha1.FunctionEvent, desired *functionsv1alpha1.FunctionEvent, triggers []functionsv1alpha1.FunctionEventTrigger, now metav1.Time) (time.Duration, error) {
	statusByTrigger := functionEventInvocationStatusIndexes(desired.Status.Invocations)
	body, err := functionEventInvocationBody(original)
	if err != nil {
		message := fmt.Sprintf("FunctionEvent payload could not be rendered as invocation JSON: %v", err)
		markFunctionEventFailed(desired, now, "InvalidPayload", message)
		return 0, nil
	}

	requeueAfter := time.Duration(0)
	for i := range triggers {
		trigger := &triggers[i]
		status := &desired.Status.Invocations[statusByTrigger[trigger.Name]]
		if status.Phase == functionsv1alpha1.FunctionEventInvocationPhaseSucceeded ||
			(status.Phase == functionsv1alpha1.FunctionEventInvocationPhaseFailed && status.Attempts >= functionEventRetryLimit) {
			continue
		}

		var function functionsv1alpha1.Function
		key := types.NamespacedName{Namespace: original.Namespace, Name: trigger.Spec.FunctionRef.Name}
		if err := r.Get(ctx, key, &function); err != nil {
			if !apierrors.IsNotFound(err) {
				return 0, err
			}
			status.Phase = functionsv1alpha1.FunctionEventInvocationPhasePending
			status.Message = fmt.Sprintf("Waiting for Function %q to exist.", trigger.Spec.FunctionRef.Name)
			requeueAfter = functionEventRetryBackoff
			continue
		}

		target := invocationTargetForFunction(&function)
		if !functionReadyForInvocation(&function, target) {
			status.Phase = functionsv1alpha1.FunctionEventInvocationPhasePending
			status.Message = functionNotReadyMessage(&function, target)
			requeueAfter = functionEventRetryBackoff
			continue
		}
		if requiresFunctionID(inv) && target.FunctionOCID == "" {
			status.Phase = functionsv1alpha1.FunctionEventInvocationPhasePending
			status.Message = fmt.Sprintf("OCI mode requires referenced Function %q to resolve status.functionId.", function.Name)
			requeueAfter = functionEventRetryBackoff
			continue
		}

		response, err := inv.Invoke(ctx, invoker.Request{
			Target: target,
			Index:  int32(i),
			Body:   body,
		})
		if errors.Is(err, invoker.ErrNotImplemented) {
			return 0, err
		}

		status.Attempts++
		status.LastAttemptTime = &now
		if err == nil {
			status.Phase = functionsv1alpha1.FunctionEventInvocationPhaseSucceeded
			status.Message = invocationSuccessMessage(response)
			continue
		}

		status.Message = normalizeFunctionEventInvocationError(err)
		if status.Attempts >= functionEventRetryLimit {
			status.Phase = functionsv1alpha1.FunctionEventInvocationPhaseFailed
			continue
		}
		status.Phase = functionsv1alpha1.FunctionEventInvocationPhasePending
		requeueAfter = functionEventRetryBackoff
	}
	return requeueAfter, nil
}

func functionEventInvocationBody(event *functionsv1alpha1.FunctionEvent) ([]byte, error) {
	id := strings.TrimSpace(event.Spec.ID)
	if id == "" {
		id = string(event.UID)
	}
	if id == "" {
		id = event.Namespace + "/" + event.Name
	}
	envelope := struct {
		ID        string          `json:"id"`
		EventType string          `json:"eventType"`
		Source    string          `json:"source,omitempty"`
		Subject   string          `json:"subject,omitempty"`
		Payload   json.RawMessage `json:"payload,omitempty"`
	}{
		ID:        id,
		EventType: strings.TrimSpace(event.Spec.EventType),
		Source:    strings.TrimSpace(event.Spec.Source),
		Subject:   strings.TrimSpace(event.Spec.Subject),
	}
	if event.Spec.Payload != nil && len(event.Spec.Payload.Raw) > 0 {
		envelope.Payload = json.RawMessage(event.Spec.Payload.Raw)
	}
	return json.Marshal(envelope)
}

func invocationSuccessMessage(response invoker.Response) string {
	details := []string{"Invocation succeeded."}
	if response.StatusCode != 0 {
		details = append(details, fmt.Sprintf("status=%d", response.StatusCode))
	}
	if response.InvocationID != "" {
		details = append(details, "invocationId="+response.InvocationID)
	}
	return strings.Join(details, " ")
}

func normalizeFunctionEventInvocationError(err error) string {
	if err == nil {
		return ""
	}
	message := sanitizeOCIErrorText(err.Error())
	if message == "" {
		message = "function invocation failed"
	}
	return ensureSentence(message)
}

func summarizeFunctionEvent(event *functionsv1alpha1.FunctionEvent, now metav1.Time) {
	if len(event.Status.Invocations) == 0 {
		markFunctionEventProcessed(event, now, "NoMatchingTriggers", "No matching triggers")
		return
	}

	var succeeded, failed, pending int
	for _, invocation := range event.Status.Invocations {
		switch invocation.Phase {
		case functionsv1alpha1.FunctionEventInvocationPhaseSucceeded:
			succeeded++
		case functionsv1alpha1.FunctionEventInvocationPhaseFailed:
			failed++
		default:
			pending++
		}
	}

	switch {
	case failed > 0:
		markFunctionEventFailed(event, now, "InvocationFailed", "One or more FunctionEvent trigger invocations failed.")
	case pending == 0 && succeeded == len(event.Status.Invocations):
		markFunctionEventProcessed(event, now, "AllInvocationsSucceeded", "All matching trigger invocations succeeded.")
	default:
		markFunctionEventProcessing(event, now, "InvocationsPending", "FunctionEvent is processing matching trigger invocations.")
	}
}

func ensureFunctionEventInvocationStatuses(status *functionsv1alpha1.FunctionEventStatus, triggers []functionsv1alpha1.FunctionEventTrigger) {
	existing := map[string]functionsv1alpha1.FunctionEventInvocationStatus{}
	for _, invocation := range status.Invocations {
		existing[invocation.TriggerName] = invocation
	}

	next := make([]functionsv1alpha1.FunctionEventInvocationStatus, 0, len(triggers))
	for _, trigger := range triggers {
		invocation := existing[trigger.Name]
		if invocation.TriggerName == "" {
			invocation.TriggerName = trigger.Name
			invocation.Phase = functionsv1alpha1.FunctionEventInvocationPhasePending
		}
		invocation.FunctionName = trigger.Spec.FunctionRef.Name
		if invocation.Phase == "" {
			invocation.Phase = functionsv1alpha1.FunctionEventInvocationPhasePending
		}
		next = append(next, invocation)
	}
	status.Invocations = next
}

func functionEventInvocationStatusIndexes(invocations []functionsv1alpha1.FunctionEventInvocationStatus) map[string]int {
	indexes := make(map[string]int, len(invocations))
	for i, invocation := range invocations {
		indexes[invocation.TriggerName] = i
	}
	return indexes
}

func functionEventTriggerNames(triggers []functionsv1alpha1.FunctionEventTrigger) []string {
	names := make([]string, 0, len(triggers))
	for _, trigger := range triggers {
		names = append(names, trigger.Name)
	}
	return names
}

func markFunctionEventProcessed(event *functionsv1alpha1.FunctionEvent, now metav1.Time, reason, message string) {
	event.Status.Phase = functionsv1alpha1.FunctionEventPhaseProcessed
	event.Status.Message = message
	setFunctionEventConditions(event, now,
		conditionState{Status: metav1.ConditionTrue, Reason: reason, Message: message},
		conditionState{Status: metav1.ConditionFalse, Reason: "NoFailedInvocations", Message: "No permanent invocation failures were observed."},
	)
}

func markFunctionEventProcessing(event *functionsv1alpha1.FunctionEvent, now metav1.Time, reason, message string) {
	event.Status.Phase = functionsv1alpha1.FunctionEventPhaseProcessing
	event.Status.Message = message
	setFunctionEventConditions(event, now,
		conditionState{Status: metav1.ConditionFalse, Reason: reason, Message: "FunctionEvent has not completed processing."},
		conditionState{Status: metav1.ConditionFalse, Reason: reason, Message: "FunctionEvent has not failed."},
	)
}

func markFunctionEventFailed(event *functionsv1alpha1.FunctionEvent, now metav1.Time, reason, message string) {
	event.Status.Phase = functionsv1alpha1.FunctionEventPhaseFailed
	event.Status.Message = message
	setFunctionEventConditions(event, now,
		conditionState{Status: metav1.ConditionFalse, Reason: reason, Message: "FunctionEvent did not complete successfully."},
		conditionState{Status: metav1.ConditionTrue, Reason: reason, Message: message},
	)
}

func setFunctionEventConditions(event *functionsv1alpha1.FunctionEvent, now metav1.Time, processed, failed conditionState) {
	setFunctionEventCondition(event, now, functionsv1alpha1.FunctionEventConditionProcessed, processed)
	setFunctionEventCondition(event, now, functionsv1alpha1.FunctionEventConditionFailed, failed)
}

func setFunctionEventCondition(event *functionsv1alpha1.FunctionEvent, now metav1.Time, conditionType string, condition conditionState) {
	lastTransitionTime := now
	if existing := meta.FindStatusCondition(event.Status.Conditions, conditionType); existing != nil &&
		existing.Status == condition.Status &&
		existing.Reason == condition.Reason &&
		existing.Message == condition.Message &&
		existing.ObservedGeneration == event.Generation {
		lastTransitionTime = existing.LastTransitionTime
	}

	event.SetCondition(metav1.Condition{
		Type:               conditionType,
		Status:             condition.Status,
		Reason:             condition.Reason,
		Message:            condition.Message,
		ObservedGeneration: event.Generation,
		LastTransitionTime: lastTransitionTime,
	})
}

func (r *FunctionEventReconciler) updateFunctionEventStatus(ctx context.Context, event *functionsv1alpha1.FunctionEvent, desired functionsv1alpha1.FunctionEventStatus) error {
	if reflect.DeepEqual(event.Status, desired) {
		return nil
	}
	event.Status = desired
	return r.Status().Update(ctx, event)
}

func (r *FunctionEventReconciler) recordEvent(event *functionsv1alpha1.FunctionEvent, eventType, reason, message string) {
	if r.Recorder == nil {
		return
	}
	r.Recorder.Event(event, eventType, reason, message)
}

func isFunctionEventType(eventType string) bool {
	return strings.HasPrefix(strings.TrimSpace(eventType), functionEventTypePrefix)
}

func classifyFunctionEventTrigger(trigger *functionsv1alpha1.FunctionEventTrigger) functionEventTriggerMode {
	hasFunctionEvent := false
	hasOCIEvent := false
	for _, eventType := range trigger.Spec.Condition.EventType {
		if isFunctionEventType(eventType) {
			hasFunctionEvent = true
		} else if strings.TrimSpace(eventType) != "" {
			hasOCIEvent = true
		}
	}
	switch {
	case hasFunctionEvent && hasOCIEvent:
		return functionEventTriggerModeMixed
	case hasFunctionEvent:
		return functionEventTriggerModeFunctionEvent
	default:
		return functionEventTriggerModeOCI
	}
}

func functionEventTriggerMatchesEvent(trigger *functionsv1alpha1.FunctionEventTrigger, eventType string) bool {
	if classifyFunctionEventTrigger(trigger) != functionEventTriggerModeFunctionEvent {
		return false
	}
	for _, triggerEventType := range trigger.Spec.Condition.EventType {
		if strings.TrimSpace(triggerEventType) == strings.TrimSpace(eventType) {
			return true
		}
	}
	return false
}

// SetupWithManager sets up the controller with the Manager.
func (r *FunctionEventReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&functionsv1alpha1.FunctionEvent{}, builder.WithPredicates(predicate.GenerationChangedPredicate{})).
		Complete(r)
}
