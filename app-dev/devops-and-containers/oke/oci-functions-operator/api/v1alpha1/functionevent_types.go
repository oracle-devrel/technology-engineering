// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package v1alpha1

import (
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

const (
	// FunctionEventConditionProcessed indicates whether all matching trigger invocations completed.
	FunctionEventConditionProcessed = "Processed"
	// FunctionEventConditionFailed indicates whether one or more trigger invocations failed permanently.
	FunctionEventConditionFailed = "Failed"
)

// FunctionEventPhase summarizes FunctionEvent routing progress.
// +kubebuilder:validation:Enum=Pending;Processing;Processed;Failed
type FunctionEventPhase string

const (
	FunctionEventPhasePending    FunctionEventPhase = "Pending"
	FunctionEventPhaseProcessing FunctionEventPhase = "Processing"
	FunctionEventPhaseProcessed  FunctionEventPhase = "Processed"
	FunctionEventPhaseFailed     FunctionEventPhase = "Failed"
)

// FunctionEventInvocationPhase summarizes one trigger invocation for a FunctionEvent.
// +kubebuilder:validation:Enum=Pending;Succeeded;Failed
type FunctionEventInvocationPhase string

const (
	FunctionEventInvocationPhasePending   FunctionEventInvocationPhase = "Pending"
	FunctionEventInvocationPhaseSucceeded FunctionEventInvocationPhase = "Succeeded"
	FunctionEventInvocationPhaseFailed    FunctionEventInvocationPhase = "Failed"
)

// FunctionEventSpec defines a Kubernetes-native event to route to matching FunctionEventTriggers.
type FunctionEventSpec struct {
	// EventType is the Kubernetes-native event type. It must use the reserved functionevent. prefix.
	// +kubebuilder:validation:MinLength=1
	// +kubebuilder:validation:Pattern=^functionevent\..+
	EventType string `json:"eventType"`

	// Source identifies the application or component that emitted the event.
	// +optional
	Source string `json:"source,omitempty"`

	// Subject identifies the resource or business object the event is about.
	// +optional
	Subject string `json:"subject,omitempty"`

	// Payload is the event payload passed to the invoked Function inside a FunctionEvent envelope.
	// +optional
	// +kubebuilder:validation:Schemaless
	// +kubebuilder:validation:Type=object
	// +kubebuilder:pruning:PreserveUnknownFields
	Payload *runtime.RawExtension `json:"payload,omitempty"`

	// ID is an optional user-provided idempotency key carried in the invocation payload.
	// When omitted, the controller uses metadata.uid in the invocation envelope.
	// +optional
	ID string `json:"id,omitempty"`

	// TTLSecondsAfterProcessed deletes the FunctionEvent this many seconds after it reaches Processed.
	// +optional
	// +kubebuilder:validation:Minimum=0
	TTLSecondsAfterProcessed *int32 `json:"ttlSecondsAfterProcessed,omitempty"`
}

// FunctionEventStatus defines observed routing and invocation state.
type FunctionEventStatus struct {
	// ObservedGeneration is the last metadata.generation observed by the controller.
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// Phase is a compact state summary for kubectl output.
	// +optional
	Phase FunctionEventPhase `json:"phase,omitempty"`

	// MatchedTriggers lists matching FunctionEventTrigger names.
	// +optional
	// +listType=set
	MatchedTriggers []string `json:"matchedTriggers,omitempty"`

	// Invocations records one invocation per matched trigger.
	// +optional
	// +listType=map
	// +listMapKey=triggerName
	Invocations []FunctionEventInvocationStatus `json:"invocations,omitempty"`

	// Message is a short human-readable status summary.
	// +optional
	Message string `json:"message,omitempty"`

	// Conditions contain detailed state transitions.
	// +optional
	// +patchMergeKey=type
	// +patchStrategy=merge
	// +listType=map
	// +listMapKey=type
	Conditions []metav1.Condition `json:"conditions,omitempty" patchStrategy:"merge" patchMergeKey:"type"`
}

// FunctionEventInvocationStatus records one matched trigger invocation.
type FunctionEventInvocationStatus struct {
	// TriggerName is the matched FunctionEventTrigger name.
	TriggerName string `json:"triggerName"`

	// FunctionName is the referenced Function name for the matched trigger.
	// +optional
	FunctionName string `json:"functionName,omitempty"`

	// Phase is the observed invocation phase.
	// +optional
	Phase FunctionEventInvocationPhase `json:"phase,omitempty"`

	// Attempts is the number of invocation attempts made.
	// +optional
	Attempts int32 `json:"attempts,omitempty"`

	// LastAttemptTime is the most recent invocation attempt time.
	// +optional
	LastAttemptTime *metav1.Time `json:"lastAttemptTime,omitempty"`

	// Message is the current invocation summary or last stable error.
	// +optional
	Message string `json:"message,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:resource:scope=Namespaced,categories={oci,functions}
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=".status.phase"
// +kubebuilder:printcolumn:name="Event Type",type=string,JSONPath=".spec.eventType"
// +kubebuilder:printcolumn:name="Matched",type=string,JSONPath=".status.matchedTriggers"
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=".metadata.creationTimestamp"
// FunctionEvent is the Schema for Kubernetes-native events routed to Functions.
type FunctionEvent struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   FunctionEventSpec   `json:"spec,omitempty"`
	Status FunctionEventStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
// FunctionEventList contains a list of FunctionEvent.
type FunctionEventList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []FunctionEvent `json:"items"`
}

// SetCondition adds or updates a FunctionEvent status condition.
func (e *FunctionEvent) SetCondition(condition metav1.Condition) {
	meta.SetStatusCondition(&e.Status.Conditions, condition)
}

// IsTerminal reports whether the FunctionEvent has reached a final phase.
func (e *FunctionEvent) IsTerminal() bool {
	return e.Status.Phase == FunctionEventPhaseProcessed || e.Status.Phase == FunctionEventPhaseFailed
}

func init() {
	SchemeBuilder.Register(&FunctionEvent{}, &FunctionEventList{})
}
