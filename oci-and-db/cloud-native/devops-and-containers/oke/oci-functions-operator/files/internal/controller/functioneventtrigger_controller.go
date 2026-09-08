// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package controller

import (
	"context"
	"encoding/json"
	"fmt"
	"hash/fnv"
	"reflect"
	"strings"
	"sync"
	"time"

	functionsv1alpha1 "github.com/oracle/oci-functions-operator/api/v1alpha1"
	"github.com/oracle/oci-functions-operator/internal/eventtrigger"
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
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

const (
	functionEventTriggerFinalizer = "functioneventtriggers.functions.oci.oracle.com/finalizer"

	functionEventTriggerOCIFailureRequeue = 30 * time.Second

	functionEventTriggerEventWaitingForFunction = "WaitingForFunction"
	functionEventTriggerEventRuleCreated        = "RuleCreated"
	functionEventTriggerEventRuleUpdated        = "RuleUpdated"
	functionEventTriggerEventRuleDeleted        = "RuleDeleted"
	functionEventTriggerEventRuleError          = "RuleError"
)

// FunctionEventTriggerReconciler reconciles a FunctionEventTrigger object.
type FunctionEventTriggerReconciler struct {
	client.Client
	Scheme  *runtime.Scheme
	Manager eventtrigger.Manager

	Recorder record.EventRecorder

	eventSignatureMu sync.Mutex
	eventSignatures  map[types.NamespacedName]string
}

// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functioneventtriggers,verbs=get;list;watch;update;patch
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functioneventtriggers/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functioneventtriggers/finalizers,verbs=update
// +kubebuilder:rbac:groups=functions.oci.oracle.com,resources=functions,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

// Reconcile ensures an OCI Events rule invokes the referenced OCI Function.
func (r *FunctionEventTriggerReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var trigger functionsv1alpha1.FunctionEventTrigger
	if err := r.Get(ctx, req.NamespacedName, &trigger); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}
	logger.V(1).Info("reconciling FunctionEventTrigger",
		"generation", trigger.Generation,
		"resourceVersion", trigger.ResourceVersion,
		"statusPhase", trigger.Status.Phase,
		"statusMessageHash", hashString(trigger.Status.Message),
		"statusPatched", false,
	)

	if !trigger.ObjectMeta.DeletionTimestamp.IsZero() {
		return r.reconcileDelete(ctx, &trigger)
	}

	triggerMode := classifyFunctionEventTrigger(&trigger)
	switch triggerMode {
	case functionEventTriggerModeMixed:
		now := metav1.Now()
		desiredObject := trigger.DeepCopy()
		desiredObject.Status.ObservedGeneration = trigger.Generation
		message := "condition.eventType cannot mix functionevent.* and OCI event types."
		markFunctionEventTriggerError(desiredObject, now, "MixedEventTypes", message)
		patched, updateErr := r.patchFunctionEventTriggerStatusIfChanged(ctx, &trigger, desiredObject.Status, false)
		logger.V(1).Info("FunctionEventTrigger status patch evaluated", "statusPatched", patched, "statusPhase", desiredObject.Status.Phase, "statusMessageHash", hashString(desiredObject.Status.Message))
		return ctrl.Result{}, updateErr
	case functionEventTriggerModeFunctionEvent:
		if controllerutil.ContainsFinalizer(&trigger, functionEventTriggerFinalizer) {
			controllerutil.RemoveFinalizer(&trigger, functionEventTriggerFinalizer)
			if err := r.Update(ctx, &trigger); err != nil {
				return ctrl.Result{}, err
			}
			return ctrl.Result{Requeue: true}, nil
		}
		now := metav1.Now()
		desiredObject := trigger.DeepCopy()
		desiredObject.Status.ObservedGeneration = trigger.Generation
		markFunctionEventTriggerRouteReady(desiredObject, now)
		patched, updateErr := r.patchFunctionEventTriggerStatusIfChanged(ctx, &trigger, desiredObject.Status, false)
		logger.V(1).Info("FunctionEventTrigger status patch evaluated", "statusPatched", patched, "statusPhase", desiredObject.Status.Phase, "statusMessageHash", hashString(desiredObject.Status.Message))
		return ctrl.Result{}, updateErr
	}

	if message := validateOCIEventTriggerRequiredFields(&trigger); message != "" {
		now := metav1.Now()
		desiredObject := trigger.DeepCopy()
		desiredObject.Status.ObservedGeneration = trigger.Generation
		markFunctionEventTriggerError(desiredObject, now, "MissingOCIEventFields", message)
		patched, updateErr := r.patchFunctionEventTriggerStatusIfChanged(ctx, &trigger, desiredObject.Status, false)
		logger.V(1).Info("FunctionEventTrigger status patch evaluated", "statusPatched", patched, "statusPhase", desiredObject.Status.Phase, "statusMessageHash", hashString(desiredObject.Status.Message))
		return ctrl.Result{}, updateErr
	}

	if !controllerutil.ContainsFinalizer(&trigger, functionEventTriggerFinalizer) {
		controllerutil.AddFinalizer(&trigger, functionEventTriggerFinalizer)
		if err := r.Update(ctx, &trigger); err != nil {
			return ctrl.Result{}, err
		}
		return ctrl.Result{Requeue: true}, nil
	}

	now := metav1.Now()
	desiredObject := trigger.DeepCopy()
	desiredObject.Status.ObservedGeneration = trigger.Generation

	conditionJSON, err := conditionJSONFromSpec(trigger.Spec.Condition)
	if err != nil {
		message := fmt.Sprintf("Invalid OCI Events condition: %v", err)
		markFunctionEventTriggerError(desiredObject, now, "InvalidCondition", message)
		r.recordEventIfChanged(&trigger, corev1.EventTypeWarning, functionEventTriggerEventRuleError, message)
		patched, updateErr := r.patchFunctionEventTriggerStatusIfChanged(ctx, &trigger, desiredObject.Status, false)
		logger.V(1).Info("FunctionEventTrigger status patch evaluated", "statusPatched", patched, "statusPhase", desiredObject.Status.Phase, "statusMessageHash", hashString(desiredObject.Status.Message))
		return ctrl.Result{}, updateErr
	}

	function, result, ready := r.resolveTriggerFunction(ctx, &trigger, desiredObject, now)
	if !ready {
		patched, updateErr := r.patchFunctionEventTriggerStatusIfChanged(ctx, &trigger, desiredObject.Status, false)
		logger.V(1).Info("FunctionEventTrigger status patch evaluated", "statusPatched", patched, "statusPhase", desiredObject.Status.Phase, "statusMessageHash", hashString(desiredObject.Status.Message))
		return result, updateErr
	}

	if r.Manager == nil {
		message := "Event trigger manager is not configured; run the manager with INVOKER_MODE=oci to manage OCI Events rules."
		markFunctionEventTriggerPending(desiredObject, now, "EventTriggerManagerNotConfigured", message)
		patched, updateErr := r.patchFunctionEventTriggerStatusIfChanged(ctx, &trigger, desiredObject.Status, false)
		logger.V(1).Info("FunctionEventTrigger status patch evaluated", "statusPatched", patched, "statusPhase", desiredObject.Status.Phase, "statusMessageHash", hashString(desiredObject.Status.Message))
		return ctrl.Result{RequeueAfter: functionEventTriggerOCIFailureRequeue}, updateErr
	}

	state, err := r.Manager.EnsureRule(ctx, desiredRuleFromTrigger(&trigger, &function, conditionJSON))
	r.recordRuleEvents(&trigger, state.Events)
	if err != nil {
		desiredObject.Status.RuleID = state.RuleID
		message := normalizeOCIEventRuleError(err)
		logger.Error(err, "FunctionEventTrigger rule reconcile failed", "statusMessage", message)
		markFunctionEventTriggerError(desiredObject, now, "RuleReconcileError", message)
		r.recordEventIfChanged(&trigger, corev1.EventTypeWarning, functionEventTriggerEventRuleError, message)
		patched, updateErr := r.patchFunctionEventTriggerStatusIfChanged(ctx, &trigger, desiredObject.Status, false)
		logger.V(1).Info("FunctionEventTrigger status patch evaluated", "statusPatched", patched, "statusPhase", desiredObject.Status.Phase, "statusMessageHash", hashString(desiredObject.Status.Message))
		return ctrl.Result{RequeueAfter: functionEventTriggerOCIFailureRequeue}, updateErr
	}

	r.clearEventSignature(&trigger)
	desiredObject.Status.RuleID = state.RuleID
	desiredObject.Status.Message = state.Message
	if desiredObject.Status.Message == "" {
		desiredObject.Status.Message = "OCI Events rule is ready."
	}
	if state.Ready {
		desiredObject.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhaseReady
		setFunctionEventTriggerConditions(desiredObject, now, conditionState{Status: metav1.ConditionTrue, Reason: "FunctionReady", Message: "Referenced Function is ready."}, conditionState{Status: metav1.ConditionTrue, Reason: "RuleReady", Message: desiredObject.Status.Message})
	} else {
		desiredObject.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhasePending
		setFunctionEventTriggerConditions(desiredObject, now, conditionState{Status: metav1.ConditionTrue, Reason: "FunctionReady", Message: "Referenced Function is ready."}, conditionState{Status: metav1.ConditionFalse, Reason: "RulePending", Message: desiredObject.Status.Message})
	}

	patched, err := r.patchFunctionEventTriggerStatusIfChanged(ctx, &trigger, desiredObject.Status, true)
	logger.V(1).Info("FunctionEventTrigger status patch evaluated", "statusPatched", patched, "statusPhase", desiredObject.Status.Phase, "statusMessageHash", hashString(desiredObject.Status.Message))
	if err != nil {
		return ctrl.Result{}, err
	}
	if patched {
		logger.V(1).Info("updated FunctionEventTrigger status", "phase", desiredObject.Status.Phase, "ruleID", desiredObject.Status.RuleID)
	}
	if !state.Ready {
		return ctrl.Result{RequeueAfter: 30 * time.Second}, nil
	}
	return ctrl.Result{}, nil
}

func (r *FunctionEventTriggerReconciler) reconcileDelete(ctx context.Context, trigger *functionsv1alpha1.FunctionEventTrigger) (ctrl.Result, error) {
	if !controllerutil.ContainsFinalizer(trigger, functionEventTriggerFinalizer) {
		return ctrl.Result{}, nil
	}

	if trigger.DeletionPolicy() == functionsv1alpha1.FunctionEventTriggerDeletionPolicyDelete && trigger.Status.RuleID != "" {
		if r.Manager == nil {
			r.recordEventIfChanged(trigger, corev1.EventTypeWarning, functionEventTriggerEventRuleError, fmt.Sprintf("Cannot delete OCI Events rule %s because event trigger manager is not configured.", trigger.Status.RuleID))
			return ctrl.Result{RequeueAfter: functionEventTriggerOCIFailureRequeue}, nil
		}
		state, err := r.Manager.DeleteRule(ctx, trigger.Status.RuleID)
		r.recordRuleEvents(trigger, state.Events)
		if err != nil {
			message := normalizeOCIEventRuleError(err)
			log.FromContext(ctx).Error(err, "FunctionEventTrigger rule delete failed", "statusMessage", message)
			r.recordEventIfChanged(trigger, corev1.EventTypeWarning, functionEventTriggerEventRuleError, message)
			return ctrl.Result{RequeueAfter: functionEventTriggerOCIFailureRequeue}, nil
		}
	}

	r.clearEventSignature(trigger)
	controllerutil.RemoveFinalizer(trigger, functionEventTriggerFinalizer)
	if err := r.Update(ctx, trigger); err != nil {
		return ctrl.Result{}, err
	}
	return ctrl.Result{}, nil
}

func (r *FunctionEventTriggerReconciler) resolveTriggerFunction(
	ctx context.Context,
	trigger *functionsv1alpha1.FunctionEventTrigger,
	desired *functionsv1alpha1.FunctionEventTrigger,
	now metav1.Time,
) (functionsv1alpha1.Function, ctrl.Result, bool) {
	var function functionsv1alpha1.Function
	if trigger.Spec.FunctionRef.Name == "" {
		message := "spec.functionRef.name is required."
		markFunctionEventTriggerError(desired, now, "InvalidFunctionRef", message)
		return function, ctrl.Result{}, false
	}

	key := types.NamespacedName{Namespace: trigger.Namespace, Name: trigger.Spec.FunctionRef.Name}
	if err := r.Get(ctx, key, &function); err != nil {
		if !apierrors.IsNotFound(err) {
			markFunctionEventTriggerError(desired, now, "FunctionLookupError", err.Error())
			return function, ctrl.Result{RequeueAfter: 30 * time.Second}, false
		}
		message := fmt.Sprintf("Waiting for Function %q to exist in namespace %q.", trigger.Spec.FunctionRef.Name, trigger.Namespace)
		markFunctionEventTriggerWaitingForFunction(desired, now, "FunctionNotFound", message)
		r.recordEventIfChanged(trigger, corev1.EventTypeNormal, functionEventTriggerEventWaitingForFunction, message)
		return function, ctrl.Result{RequeueAfter: 30 * time.Second}, false
	}

	if !meta.IsStatusConditionTrue(function.Status.Conditions, functionsv1alpha1.FunctionConditionReady) || strings.TrimSpace(function.Status.FunctionID) == "" {
		message := functionNotReadyForEventTriggerMessage(&function)
		markFunctionEventTriggerWaitingForFunction(desired, now, "FunctionNotReady", message)
		r.recordEventIfChanged(trigger, corev1.EventTypeNormal, functionEventTriggerEventWaitingForFunction, message)
		return function, ctrl.Result{RequeueAfter: 30 * time.Second}, false
	}

	return function, ctrl.Result{}, true
}

func functionNotReadyForEventTriggerMessage(function *functionsv1alpha1.Function) string {
	details := []string{}
	if function.Status.Phase != "" {
		details = append(details, fmt.Sprintf("phase=%s", function.Status.Phase))
	}
	if function.Status.FunctionID == "" {
		details = append(details, "status.functionId is empty")
	}
	condition := meta.FindStatusCondition(function.Status.Conditions, functionsv1alpha1.FunctionConditionReady)
	if condition != nil {
		details = append(details, fmt.Sprintf("Ready=%s reason=%s", condition.Status, condition.Reason))
	}
	if function.Status.Message != "" {
		details = append(details, "message="+function.Status.Message)
	}
	if len(details) == 0 {
		return fmt.Sprintf("Waiting for Function %q to become Ready and populate status.functionId.", function.Name)
	}
	return fmt.Sprintf("Waiting for Function %q to become Ready and populate status.functionId: %s.", function.Name, strings.Join(details, "; "))
}

func desiredRuleFromTrigger(trigger *functionsv1alpha1.FunctionEventTrigger, function *functionsv1alpha1.Function, conditionJSON string) eventtrigger.DesiredRule {
	return eventtrigger.DesiredRule{
		CompartmentID: strings.TrimSpace(trigger.Spec.CompartmentID),
		DisplayName:   strings.TrimSpace(trigger.Spec.DisplayName),
		Description:   strings.TrimSpace(trigger.Spec.Description),
		IsEnabled:     trigger.RuleEnabled(),
		ConditionJSON: conditionJSON,
		FunctionID:    strings.TrimSpace(function.Status.FunctionID),
		RuleID:        strings.TrimSpace(trigger.Status.RuleID),
		TriggerName:   trigger.Name,
		Namespace:     trigger.Namespace,
		UID:           string(trigger.UID),
	}
}

func conditionJSONFromSpec(condition functionsv1alpha1.FunctionEventCondition) (string, error) {
	if strings.TrimSpace(condition.RawJSON) != "" {
		return normalizeConditionJSON(condition.RawJSON)
	}

	document := struct {
		EventType interface{} `json:"eventType,omitempty"`
		Data      interface{} `json:"data,omitempty"`
	}{}
	if len(condition.EventType) > 0 {
		eventType, err := renderConditionEventType(condition.EventType)
		if err != nil {
			return "", err
		}
		document.EventType = eventType
	}
	if condition.Data != nil && len(condition.Data.Raw) > 0 {
		var data interface{}
		if err := json.Unmarshal(condition.Data.Raw, &data); err != nil {
			return "", fmt.Errorf("condition.data must be valid JSON: %w", err)
		}
		normalizedData, err := normalizeConditionData(data, "$.data", true)
		if err != nil {
			return "", err
		}
		if _, ok := normalizedData.(map[string]interface{}); !ok {
			return "", fmt.Errorf("condition.data must be a JSON object")
		}
		document.Data = normalizedData
	}
	if document.EventType == nil && document.Data == nil {
		return "", fmt.Errorf("condition must set rawJson or at least one structured field")
	}
	encoded, err := json.Marshal(document)
	if err != nil {
		return "", err
	}
	return string(encoded), nil
}

func renderConditionEventType(eventTypes []string) (interface{}, error) {
	if len(eventTypes) == 0 {
		return nil, fmt.Errorf("condition.eventType must contain at least one value")
	}
	normalized := make([]string, 0, len(eventTypes))
	for i, value := range eventTypes {
		eventType := strings.TrimSpace(value)
		if eventType == "" {
			return nil, fmt.Errorf("condition.eventType[%d] must not be empty", i)
		}
		normalized = append(normalized, eventType)
	}
	if len(normalized) == 1 {
		return normalized[0], nil
	}
	return normalized, nil
}

func normalizeConditionJSON(value string) (string, error) {
	var decoded interface{}
	if err := json.Unmarshal([]byte(value), &decoded); err != nil {
		return "", err
	}
	document, ok := decoded.(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("rawJson must be a JSON object")
	}
	if len(document) == 0 {
		return "", fmt.Errorf("rawJson must contain at least one OCI Events condition field")
	}
	if err := validateOCIEventsConditionDocument(document); err != nil {
		return "", fmt.Errorf("rawJson is not valid OCI Events condition JSON: %w", err)
	}
	encoded, err := json.Marshal(document)
	if err != nil {
		return "", err
	}
	return string(encoded), nil
}

func normalizeConditionData(value interface{}, path string, collapseSingleArrays bool) (interface{}, error) {
	switch typed := value.(type) {
	case map[string]interface{}:
		normalized := map[string]interface{}{}
		for key, child := range typed {
			childPath := path + "." + key
			value, err := normalizeConditionData(child, childPath, collapseSingleArrays)
			if err != nil {
				return nil, err
			}
			normalized[key] = value
		}
		return normalized, nil
	case []interface{}:
		if len(typed) == 0 {
			return nil, fmt.Errorf("%s is an empty array; OCI Events condition arrays must contain at least one value", path)
		}
		normalized := make([]interface{}, 0, len(typed))
		for i, child := range typed {
			value, err := normalizeConditionData(child, fmt.Sprintf("%s[%d]", path, i), false)
			if err != nil {
				return nil, err
			}
			normalized = append(normalized, value)
		}
		if collapseSingleArrays && len(normalized) == 1 {
			return normalized[0], nil
		}
		return normalized, nil
	case nil:
		return nil, fmt.Errorf("%s is null; OCI Events condition values must not be null", path)
	default:
		return typed, nil
	}
}

func validateOCIEventsConditionDocument(document map[string]interface{}) error {
	if value, ok := document["eventType"]; ok {
		switch typed := value.(type) {
		case string:
			if strings.TrimSpace(typed) == "" {
				return fmt.Errorf("$.eventType must not be empty")
			}
		case []interface{}:
			if _, err := eventTypeStringsFromInterfaces(typed, "$.eventType"); err != nil {
				return err
			}
		default:
			return fmt.Errorf("$.eventType must be a string or array of strings")
		}
	}
	if value, ok := document["data"]; ok {
		normalizedData, err := normalizeConditionData(value, "$.data", false)
		if err != nil {
			return err
		}
		if _, ok := normalizedData.(map[string]interface{}); !ok {
			return fmt.Errorf("$.data must be a JSON object")
		}
	}
	for key, value := range document {
		if key == "eventType" || key == "data" {
			continue
		}
		if _, err := normalizeConditionData(value, "$."+key, false); err != nil {
			return err
		}
	}
	return nil
}

func eventTypeStringsFromInterfaces(values []interface{}, path string) ([]string, error) {
	if len(values) == 0 {
		return nil, fmt.Errorf("%s must contain at least one value", path)
	}
	normalized := make([]string, 0, len(values))
	for i, value := range values {
		text, ok := value.(string)
		if !ok {
			return nil, fmt.Errorf("%s[%d] must be a string", path, i)
		}
		text = strings.TrimSpace(text)
		if text == "" {
			return nil, fmt.Errorf("%s[%d] must not be empty", path, i)
		}
		normalized = append(normalized, text)
	}
	return normalized, nil
}

func normalizeOCIEventRuleError(err error) string {
	if err == nil {
		return "OCI Events rule sync failed."
	}
	raw := strings.TrimSpace(err.Error())
	operation := ociEventRuleErrorOperation(raw)
	status, code, message := parseOCIServiceErrorFields(raw)
	if status != "" || code != "" || message != "" {
		return formatOCIEventRuleError(operation, status, code, message)
	}

	status, code, message = parseLeadingOCIServiceError(raw)
	if status != "" || code != "" || message != "" {
		return formatOCIEventRuleError(operation, status, code, message)
	}

	message = sanitizeOCIErrorText(stripKnownOCIEventRuleErrorPrefix(raw))
	if message == "" {
		message = "OCI Events API request failed"
	}
	return ensureSentence(fmt.Sprintf("%s failed: %s", operation, message))
}

func ociEventRuleErrorOperation(raw string) string {
	if operation := extractLineField(raw, "Operation Name:"); operation != "" {
		return operation
	}
	lower := strings.ToLower(raw)
	switch {
	case strings.Contains(lower, "create oci events rule"):
		return "CreateRule"
	case strings.Contains(lower, "list oci events rules"):
		return "ListRules"
	case strings.Contains(lower, "update oci events rule"):
		return "UpdateRule"
	case strings.Contains(lower, "delete oci events rule"):
		return "DeleteRule"
	case strings.Contains(lower, "get oci events rule"):
		return "GetRule"
	default:
		return "OCI Events rule sync"
	}
}

func parseOCIServiceErrorFields(raw string) (status, code, message string) {
	status = extractPeriodField(raw, "Http Status Code:")
	code = extractPeriodField(raw, "Error Code:")
	message = extractLineField(raw, "Message:")
	message = sanitizeOCIErrorText(message)
	return status, code, message
}

func parseLeadingOCIServiceError(raw string) (status, code, message string) {
	text := sanitizeOCIErrorText(stripKnownOCIEventRuleErrorPrefix(raw))
	fields := strings.Fields(text)
	if len(fields) < 2 || !isHTTPStatusCode(fields[0]) {
		return "", "", ""
	}
	status = fields[0]
	code = strings.Trim(fields[1], ":.")
	rest := strings.TrimSpace(strings.TrimPrefix(text, fields[0]))
	rest = strings.TrimSpace(strings.TrimPrefix(rest, fields[1]))
	message = strings.TrimLeft(strings.TrimSpace(rest), ":. ")
	return status, code, sanitizeOCIErrorText(message)
}

func formatOCIEventRuleError(operation, status, code, message string) string {
	operation = strings.TrimSpace(operation)
	if operation == "" {
		operation = "OCI Events rule sync"
	}
	message = strings.TrimSpace(message)
	if message == "" {
		message = "OCI Events API request failed"
	}

	switch {
	case status != "" && code != "":
		return ensureSentence(fmt.Sprintf("%s failed: %s %s: %s", operation, status, code, message))
	case status != "":
		return ensureSentence(fmt.Sprintf("%s failed: %s: %s", operation, status, message))
	case code != "":
		return ensureSentence(fmt.Sprintf("%s failed: %s: %s", operation, code, message))
	default:
		return ensureSentence(fmt.Sprintf("%s failed: %s", operation, message))
	}
}

func extractPeriodField(value, marker string) string {
	remaining := substringAfterCaseInsensitive(value, marker)
	if remaining == "" {
		return ""
	}
	if idx := strings.Index(remaining, "."); idx >= 0 {
		remaining = remaining[:idx]
	}
	if idx := strings.Index(remaining, "\n"); idx >= 0 {
		remaining = remaining[:idx]
	}
	return strings.TrimSpace(remaining)
}

func extractLineField(value, marker string) string {
	remaining := substringAfterCaseInsensitive(value, marker)
	if remaining == "" {
		return ""
	}
	if idx := strings.Index(remaining, "\n"); idx >= 0 {
		remaining = remaining[:idx]
	}
	return strings.TrimSpace(remaining)
}

func substringAfterCaseInsensitive(value, marker string) string {
	lowerValue := strings.ToLower(value)
	lowerMarker := strings.ToLower(marker)
	idx := strings.Index(lowerValue, lowerMarker)
	if idx < 0 {
		return ""
	}
	return value[idx+len(marker):]
}

func stripKnownOCIEventRuleErrorPrefix(raw string) string {
	lower := strings.ToLower(raw)
	knownPrefixes := []string{
		"create oci events rule",
		"list oci events rules",
		"update oci events rule",
		"delete oci events rule",
		"get oci events rule",
	}
	for _, prefix := range knownPrefixes {
		if !strings.Contains(lower, prefix) {
			continue
		}
		if idx := strings.Index(raw, ":"); idx >= 0 {
			return strings.TrimSpace(raw[idx+1:])
		}
	}
	return raw
}

func sanitizeOCIErrorText(value string) string {
	value = strings.ReplaceAll(value, "\r\n", "\n")
	lines := strings.Split(value, "\n")
	kept := make([]string, 0, len(lines))
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || isVolatileOCIErrorLine(line) {
			continue
		}
		line = removeInlineOCIErrorField(line, "Opc request id:")
		line = removeInlineOCIErrorField(line, "Opc-Request-Id:")
		line = removeInlineOCIErrorField(line, "opc-request-id:")
		line = removeInlineOCIErrorField(line, "opc-request-id=")
		line = removeInlineOCIErrorField(line, "request id:")
		line = removeInlineOCIErrorField(line, "ociRequestId=")
		line = strings.TrimSpace(line)
		if line != "" {
			kept = append(kept, line)
		}
	}
	return strings.Join(strings.Fields(strings.Join(kept, " ")), " ")
}

func isVolatileOCIErrorLine(line string) bool {
	lower := strings.ToLower(line)
	volatilePrefixes := []string{
		"operation name:",
		"timestamp:",
		"client version:",
		"request endpoint:",
		"troubleshooting tips:",
		"to get more info",
		"if you are unable",
	}
	for _, prefix := range volatilePrefixes {
		if strings.HasPrefix(lower, prefix) {
			return true
		}
	}
	return false
}

func removeInlineOCIErrorField(value, marker string) string {
	for {
		remaining := substringAfterCaseInsensitive(value, marker)
		if remaining == "" {
			return value
		}
		start := len(value) - len(remaining) - len(marker)
		end := len(value)
		for _, delimiter := range []string{". ", "; ", ", "} {
			if idx := strings.Index(remaining, delimiter); idx >= 0 {
				end = start + len(marker) + idx + len(delimiter)
				break
			}
		}
		value = strings.TrimSpace(value[:start] + value[end:])
	}
}

func isHTTPStatusCode(value string) bool {
	return len(value) == 3 && value[0] >= '1' && value[0] <= '5' && value[1] >= '0' && value[1] <= '9' && value[2] >= '0' && value[2] <= '9'
}

func ensureSentence(value string) string {
	value = strings.TrimSpace(value)
	if value == "" {
		return value
	}
	switch value[len(value)-1] {
	case '.', '!', '?':
		return value
	default:
		return value + "."
	}
}

func markFunctionEventTriggerWaitingForFunction(trigger *functionsv1alpha1.FunctionEventTrigger, now metav1.Time, reason, message string) {
	trigger.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhasePending
	trigger.Status.Message = message
	setFunctionEventTriggerConditions(trigger, now,
		conditionState{Status: metav1.ConditionFalse, Reason: reason, Message: message},
		conditionState{Status: metav1.ConditionFalse, Reason: "WaitingForFunction", Message: "OCI Events rule is waiting for the referenced Function."},
	)
}

func markFunctionEventTriggerPending(trigger *functionsv1alpha1.FunctionEventTrigger, now metav1.Time, reason, message string) {
	trigger.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhasePending
	trigger.Status.Message = message
	setFunctionEventTriggerConditions(trigger, now,
		conditionState{Status: metav1.ConditionTrue, Reason: "FunctionReady", Message: "Referenced Function is ready."},
		conditionState{Status: metav1.ConditionFalse, Reason: reason, Message: message},
	)
}

func markFunctionEventTriggerError(trigger *functionsv1alpha1.FunctionEventTrigger, now metav1.Time, reason, message string) {
	trigger.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhaseError
	trigger.Status.Message = message
	setFunctionEventTriggerConditions(trigger, now,
		conditionState{Status: metav1.ConditionUnknown, Reason: reason, Message: "Function resolution did not complete."},
		conditionState{Status: metav1.ConditionFalse, Reason: reason, Message: message},
	)
}

func markFunctionEventTriggerRouteReady(trigger *functionsv1alpha1.FunctionEventTrigger, now metav1.Time) {
	message := "FunctionEventTrigger routes Kubernetes FunctionEvent objects."
	if functionEventTriggerHasIgnoredOCIFields(trigger) {
		message = "FunctionEventTrigger routes Kubernetes FunctionEvent objects; OCI Events rule fields are ignored for functionevent.* routes."
	}
	trigger.Status.Phase = functionsv1alpha1.FunctionEventTriggerPhaseReady
	trigger.Status.RuleID = ""
	trigger.Status.Message = message
	setFunctionEventTriggerConditions(trigger, now,
		conditionState{Status: metav1.ConditionUnknown, Reason: "FunctionEventRoute", Message: "Function readiness is checked when matching FunctionEvents are processed."},
		conditionState{Status: metav1.ConditionTrue, Reason: "FunctionEventRouteReady", Message: message},
	)
}

func functionEventTriggerHasIgnoredOCIFields(trigger *functionsv1alpha1.FunctionEventTrigger) bool {
	return strings.TrimSpace(trigger.Spec.CompartmentID) != "" ||
		strings.TrimSpace(trigger.Spec.DisplayName) != "" ||
		trigger.Spec.DeletionPolicy == functionsv1alpha1.FunctionEventTriggerDeletionPolicyRetain
}

func validateOCIEventTriggerRequiredFields(trigger *functionsv1alpha1.FunctionEventTrigger) string {
	missing := []string{}
	if strings.TrimSpace(trigger.Spec.CompartmentID) == "" {
		missing = append(missing, "spec.compartmentId")
	}
	if strings.TrimSpace(trigger.Spec.DisplayName) == "" {
		missing = append(missing, "spec.displayName")
	}
	if len(missing) == 0 {
		return ""
	}
	return fmt.Sprintf("OCI Events triggers require %s. FunctionEvent-only triggers can omit these fields by using only functionevent.* condition.eventType values.", strings.Join(missing, " and "))
}

func setFunctionEventTriggerConditions(trigger *functionsv1alpha1.FunctionEventTrigger, now metav1.Time, functionResolved, ruleReady conditionState) {
	setFunctionEventTriggerCondition(trigger, now, functionsv1alpha1.FunctionEventTriggerConditionFunctionResolved, functionResolved)
	setFunctionEventTriggerCondition(trigger, now, functionsv1alpha1.FunctionEventTriggerConditionRuleReady, ruleReady)
}

func setFunctionEventTriggerCondition(trigger *functionsv1alpha1.FunctionEventTrigger, now metav1.Time, conditionType string, condition conditionState) {
	lastTransitionTime := now
	if existing := meta.FindStatusCondition(trigger.Status.Conditions, conditionType); existing != nil &&
		existing.Status == condition.Status &&
		existing.Reason == condition.Reason &&
		existing.Message == condition.Message &&
		existing.ObservedGeneration == trigger.Generation {
		lastTransitionTime = existing.LastTransitionTime
	}

	trigger.SetCondition(metav1.Condition{
		Type:               conditionType,
		Status:             condition.Status,
		Reason:             condition.Reason,
		Message:            condition.Message,
		ObservedGeneration: trigger.Generation,
		LastTransitionTime: lastTransitionTime,
	})
}

func (r *FunctionEventTriggerReconciler) patchFunctionEventTriggerStatusIfChanged(ctx context.Context, trigger *functionsv1alpha1.FunctionEventTrigger, desired functionsv1alpha1.FunctionEventTriggerStatus, updateLastSyncTime bool) (bool, error) {
	if functionEventTriggerStatusEqual(trigger.Status, desired) {
		return false, nil
	}
	desired.LastSyncTime = trigger.Status.LastSyncTime
	if updateLastSyncTime {
		now := metav1.Now()
		desired.LastSyncTime = &now
	}
	trigger.Status = desired
	return true, r.Status().Update(ctx, trigger)
}

func functionEventTriggerStatusEqual(current, desired functionsv1alpha1.FunctionEventTriggerStatus) bool {
	current.LastSyncTime = nil
	desired.LastSyncTime = nil
	return reflect.DeepEqual(current, desired)
}

func hashString(value string) string {
	hash := fnv.New32a()
	_, _ = hash.Write([]byte(value))
	return fmt.Sprintf("%08x", hash.Sum32())
}

func (r *FunctionEventTriggerReconciler) recordRuleEvents(trigger *functionsv1alpha1.FunctionEventTrigger, events []eventtrigger.Event) {
	for _, event := range events {
		eventType := corev1.EventTypeNormal
		if event.Type == eventtrigger.EventTypeWarning {
			eventType = corev1.EventTypeWarning
		}
		reason := event.Reason
		switch reason {
		case "RuleCreated":
			reason = functionEventTriggerEventRuleCreated
		case "RuleUpdated":
			reason = functionEventTriggerEventRuleUpdated
		case "RuleDeleted":
			reason = functionEventTriggerEventRuleDeleted
		case "":
			reason = functionEventTriggerEventRuleError
		}
		r.recordEventIfChanged(trigger, eventType, reason, event.Message)
	}
}

func (r *FunctionEventTriggerReconciler) recordEventIfChanged(trigger *functionsv1alpha1.FunctionEventTrigger, eventType, reason, message string) {
	if r.Recorder == nil {
		return
	}

	key := types.NamespacedName{Name: trigger.Name, Namespace: trigger.Namespace}
	signature := eventType + "\x00" + reason + "\x00" + message

	r.eventSignatureMu.Lock()
	if r.eventSignatures == nil {
		r.eventSignatures = map[types.NamespacedName]string{}
	}
	if r.eventSignatures[key] == signature {
		r.eventSignatureMu.Unlock()
		return
	}
	r.eventSignatures[key] = signature
	r.eventSignatureMu.Unlock()

	r.recordEvent(trigger, eventType, reason, message)
}

func (r *FunctionEventTriggerReconciler) clearEventSignature(trigger *functionsv1alpha1.FunctionEventTrigger) {
	r.eventSignatureMu.Lock()
	delete(r.eventSignatures, types.NamespacedName{Name: trigger.Name, Namespace: trigger.Namespace})
	r.eventSignatureMu.Unlock()
}

func (r *FunctionEventTriggerReconciler) recordEvent(trigger *functionsv1alpha1.FunctionEventTrigger, eventType, reason, message string) {
	if r.Recorder == nil {
		return
	}
	r.Recorder.Event(trigger, eventType, reason, message)
}

// SetupWithManager sets up the controller with the Manager.
func (r *FunctionEventTriggerReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&functionsv1alpha1.FunctionEventTrigger{}, builder.WithPredicates(functionEventTriggerPrimaryPredicate())).
		Watches(&functionsv1alpha1.Function{}, handler.EnqueueRequestsFromMapFunc(r.functionToEventTriggerRequests)).
		Complete(r)
}

func functionEventTriggerPrimaryPredicate() predicate.Predicate {
	return predicate.Funcs{
		CreateFunc: func(event.CreateEvent) bool {
			return true
		},
		DeleteFunc: func(event.DeleteEvent) bool {
			return true
		},
		UpdateFunc: func(e event.UpdateEvent) bool {
			if e.ObjectOld == nil || e.ObjectNew == nil {
				return true
			}
			if e.ObjectOld.GetGeneration() != e.ObjectNew.GetGeneration() {
				return true
			}
			return hasDeletionTimestamp(e.ObjectOld) != hasDeletionTimestamp(e.ObjectNew)
		},
		GenericFunc: func(event.GenericEvent) bool {
			return true
		},
	}
}

func hasDeletionTimestamp(obj client.Object) bool {
	deletionTimestamp := obj.GetDeletionTimestamp()
	return deletionTimestamp != nil && !deletionTimestamp.IsZero()
}

func (r *FunctionEventTriggerReconciler) functionToEventTriggerRequests(ctx context.Context, obj client.Object) []reconcile.Request {
	function, ok := obj.(*functionsv1alpha1.Function)
	if !ok {
		return nil
	}

	var triggers functionsv1alpha1.FunctionEventTriggerList
	if err := r.List(ctx, &triggers, client.InNamespace(function.Namespace)); err != nil {
		log.FromContext(ctx).Error(err, "list FunctionEventTriggers for Function watch", "namespace", function.Namespace, "function", function.Name)
		return nil
	}

	requests := []reconcile.Request{}
	for _, trigger := range triggers.Items {
		if trigger.Spec.FunctionRef.Name != function.Name {
			continue
		}
		requests = append(requests, reconcile.Request{NamespacedName: types.NamespacedName{
			Namespace: trigger.Namespace,
			Name:      trigger.Name,
		}})
	}
	return requests
}
