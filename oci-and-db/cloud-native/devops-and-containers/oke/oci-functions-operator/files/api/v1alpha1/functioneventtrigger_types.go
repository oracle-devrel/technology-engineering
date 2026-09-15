// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package v1alpha1

import (
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

const (
	// FunctionEventTriggerConditionFunctionResolved indicates whether the referenced Function is ready.
	FunctionEventTriggerConditionFunctionResolved = "FunctionResolved"
	// FunctionEventTriggerConditionRuleReady indicates whether the OCI Events rule is ready.
	FunctionEventTriggerConditionRuleReady = "RuleReady"
)

// FunctionEventTriggerPhase summarizes trigger reconciliation.
// +kubebuilder:validation:Enum=Pending;Ready;Error
type FunctionEventTriggerPhase string

const (
	FunctionEventTriggerPhasePending FunctionEventTriggerPhase = "Pending"
	FunctionEventTriggerPhaseReady   FunctionEventTriggerPhase = "Ready"
	FunctionEventTriggerPhaseError   FunctionEventTriggerPhase = "Error"
)

// FunctionEventTriggerDeletionPolicy controls OCI Events rule cleanup.
// +kubebuilder:validation:Enum=Delete;Retain
type FunctionEventTriggerDeletionPolicy string

const (
	// FunctionEventTriggerDeletionPolicyDelete deletes the OCI Events rule when the trigger is deleted.
	FunctionEventTriggerDeletionPolicyDelete FunctionEventTriggerDeletionPolicy = "Delete"
	// FunctionEventTriggerDeletionPolicyRetain leaves the OCI Events rule in OCI when the trigger is deleted.
	FunctionEventTriggerDeletionPolicyRetain FunctionEventTriggerDeletionPolicy = "Retain"
)

// FunctionEventTriggerSpec defines an OCI Events rule or FunctionEvent route that invokes an OCI Function.
type FunctionEventTriggerSpec struct {
	// FunctionRef references a Function in the same namespace.
	FunctionRef FunctionReference `json:"functionRef"`

	// CompartmentID is the compartment OCID where the OCI Events rule is created.
	// Required for OCI Events rule triggers. Omit for FunctionEvent-only triggers.
	// +optional
	// +kubebuilder:validation:Optional
	// +kubebuilder:validation:Pattern=^ocid1\.compartment\..+
	CompartmentID string `json:"compartmentId,omitempty"`

	// DisplayName is the OCI Events rule display name.
	// Required for OCI Events rule triggers. Omit for FunctionEvent-only triggers.
	// +optional
	// +kubebuilder:validation:Optional
	// +kubebuilder:validation:MinLength=1
	// +kubebuilder:validation:MaxLength=255
	DisplayName string `json:"displayName,omitempty"`

	// Description describes the OCI Events rule.
	// +optional
	// +kubebuilder:validation:MaxLength=400
	Description string `json:"description,omitempty"`

	// IsEnabled controls whether the OCI Events rule and Function action are enabled.
	// Defaults to true when omitted.
	// +optional
	// +kubebuilder:default=true
	IsEnabled *bool `json:"isEnabled,omitempty"`

	// Condition is the OCI Events matching condition.
	Condition FunctionEventCondition `json:"condition"`

	// DeletionPolicy controls whether deleting this Kubernetes object deletes the OCI Events rule.
	// +optional
	// +kubebuilder:default=Delete
	DeletionPolicy FunctionEventTriggerDeletionPolicy `json:"deletionPolicy,omitempty"`
}

// FunctionEventCondition defines the OCI Events rule condition.
// +kubebuilder:validation:XValidation:rule="has(self.rawJson) || has(self.eventType) || has(self.data)",message="condition must set rawJson or at least one structured field"
// +kubebuilder:validation:XValidation:rule="!has(self.rawJson) || (!has(self.eventType) && !has(self.data))",message="condition.rawJson is mutually exclusive with structured condition fields"
type FunctionEventCondition struct {
	// RawJSON is the exact OCI Events rule condition JSON string.
	// +optional
	// +kubebuilder:validation:MinLength=2
	RawJSON string `json:"rawJson,omitempty"`

	// EventType matches OCI eventType values, for example com.oraclecloud.objectstorage.createobject.
	// +optional
	// +kubebuilder:validation:MinItems=1
	// +kubebuilder:validation:MaxItems=32
	// +kubebuilder:validation:items:MinLength=1
	// +kubebuilder:validation:items:MaxLength=256
	// +listType=set
	EventType []string `json:"eventType,omitempty"`

	// Data matches OCI event data fields using the same nested shape as the event payload.
	// +optional
	// +kubebuilder:validation:Schemaless
	// +kubebuilder:validation:Type=object
	// +kubebuilder:pruning:PreserveUnknownFields
	Data *runtime.RawExtension `json:"data,omitempty"`
}

// FunctionEventTriggerStatus defines the observed state of FunctionEventTrigger.
type FunctionEventTriggerStatus struct {
	// ObservedGeneration is the last metadata.generation observed by the controller.
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// Phase is a compact state summary for kubectl output.
	// +optional
	Phase FunctionEventTriggerPhase `json:"phase,omitempty"`

	// RuleID is the OCI Events rule OCID.
	// +optional
	RuleID string `json:"ruleId,omitempty"`

	// LastSyncTime is the last time the controller updated observed status.
	// +optional
	LastSyncTime *metav1.Time `json:"lastSyncTime,omitempty"`

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

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:resource:scope=Namespaced,categories={oci,functions}
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=".status.phase"
// +kubebuilder:printcolumn:name="Rule ID",type=string,JSONPath=".status.ruleId"
// +kubebuilder:printcolumn:name="Function",type=string,JSONPath=".spec.functionRef.name"
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=".metadata.creationTimestamp"
// FunctionEventTrigger is the Schema for OCI Events rules that invoke OCI Functions.
type FunctionEventTrigger struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   FunctionEventTriggerSpec   `json:"spec,omitempty"`
	Status FunctionEventTriggerStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
// FunctionEventTriggerList contains a list of FunctionEventTrigger.
type FunctionEventTriggerList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []FunctionEventTrigger `json:"items"`
}

// DeletionPolicy returns the effective deletion policy when API defaulting has not run.
func (t *FunctionEventTrigger) DeletionPolicy() FunctionEventTriggerDeletionPolicy {
	if t.Spec.DeletionPolicy == FunctionEventTriggerDeletionPolicyRetain {
		return FunctionEventTriggerDeletionPolicyRetain
	}
	return FunctionEventTriggerDeletionPolicyDelete
}

// RuleEnabled returns the effective rule enabled flag when API defaulting has not run.
func (t *FunctionEventTrigger) RuleEnabled() bool {
	return t.Spec.IsEnabled == nil || *t.Spec.IsEnabled
}

// SetCondition adds or updates a FunctionEventTrigger status condition.
func (t *FunctionEventTrigger) SetCondition(condition metav1.Condition) {
	meta.SetStatusCondition(&t.Status.Conditions, condition)
}

func init() {
	SchemeBuilder.Register(&FunctionEventTrigger{}, &FunctionEventTriggerList{})
}
