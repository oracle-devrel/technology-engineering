// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package v1alpha1

import (
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const (
	// FunctionApplicationConditionReady indicates whether the OCI Functions application is ready to use.
	FunctionApplicationConditionReady = "Ready"
	// FunctionApplicationConditionApplicationResolved indicates whether the OCI application was created or resolved.
	FunctionApplicationConditionApplicationResolved = "ApplicationResolved"
	// FunctionApplicationConditionApplicationReady indicates whether the OCI application lifecycle is usable.
	FunctionApplicationConditionApplicationReady = "ApplicationReady"
)

// FunctionApplicationMode selects whether the operator manages or only resolves an OCI Functions application.
// +kubebuilder:validation:Enum=Managed;Existing
type FunctionApplicationMode string

const (
	// FunctionApplicationModeManaged creates and updates an OCI Functions application.
	FunctionApplicationModeManaged FunctionApplicationMode = "Managed"
	// FunctionApplicationModeExisting resolves an existing OCI Functions application.
	FunctionApplicationModeExisting FunctionApplicationMode = "Existing"
)

// FunctionApplicationPhase summarizes the observed state of a FunctionApplication.
// +kubebuilder:validation:Enum=Pending;Ready;Error
type FunctionApplicationPhase string

const (
	FunctionApplicationPhasePending FunctionApplicationPhase = "Pending"
	FunctionApplicationPhaseReady   FunctionApplicationPhase = "Ready"
	FunctionApplicationPhaseError   FunctionApplicationPhase = "Error"
)

// FunctionApplicationLogLineFormat selects the emitted function invocation log line format.
// +kubebuilder:validation:Enum=JSON;PLAIN_TEXT
type FunctionApplicationLogLineFormat string

const (
	// FunctionApplicationLogLineFormatJSON emits invocation logs as JSON lines.
	FunctionApplicationLogLineFormatJSON FunctionApplicationLogLineFormat = "JSON"
	// FunctionApplicationLogLineFormatPlainText emits invocation logs as plain text.
	FunctionApplicationLogLineFormatPlainText FunctionApplicationLogLineFormat = "PLAIN_TEXT"
)

// FunctionApplicationSpec defines the desired state of FunctionApplication.
// +kubebuilder:validation:XValidation:rule="!has(self.mode) || self.mode != 'Existing' || has(self.existingApplicationId) || (has(self.displayName) && has(self.compartmentId))",message="mode Existing requires spec.existingApplicationId or spec.displayName and spec.compartmentId"
// +kubebuilder:validation:XValidation:rule="!has(self.logging) || !has(self.logging.invocationLogs) || (has(self.logging.invocationLogs.enabled) && self.logging.invocationLogs.enabled == false) || has(self.logging.invocationLogs.logGroupId)",message="spec.logging.invocationLogs.logGroupId is required when invocation logs are enabled"
type FunctionApplicationSpec struct {
	// Mode selects whether the operator manages or only resolves an existing OCI Functions application.
	// Defaults to Managed.
	// +optional
	// +kubebuilder:default=Managed
	Mode FunctionApplicationMode `json:"mode,omitempty"`

	// CompartmentID is the compartment OCID for the OCI Functions application.
	// +kubebuilder:validation:Pattern=^ocid1\.compartment\..+
	CompartmentID string `json:"compartmentId"`

	// DisplayName is the OCI Functions application display name.
	// +kubebuilder:validation:MinLength=1
	// +kubebuilder:validation:MaxLength=255
	DisplayName string `json:"displayName"`

	// Region is the OCI region identifier, such as me-jeddah-1.
	// +optional
	// +kubebuilder:validation:MinLength=1
	Region string `json:"region,omitempty"`

	// SubnetIDs are the subnet OCIDs for a newly created managed OCI Functions application.
	// +optional
	// +kubebuilder:validation:MinItems=1
	// +listType=atomic
	SubnetIDs []string `json:"subnetIds,omitempty"`

	// NSGIDs are the Network Security Group OCIDs to attach to the OCI Functions application.
	// When omitted, the operator leaves NSGs unmanaged on existing applications.
	// Set an empty list to explicitly clear all NSGs.
	// Set a non-empty list to create new applications with those NSGs and reconcile existing applications to that set.
	// +optional
	// +kubebuilder:validation:items:Pattern=^ocid1\.networksecuritygroup\..+
	// +listType=atomic
	NSGIDs []string `json:"nsgIds,omitempty"`

	// Config is application-level OCI Functions configuration shared by functions in this application.
	// +optional
	Config map[string]string `json:"config,omitempty"`

	// Logging configures function invocation logs for this OCI Functions application.
	// Omit this field to leave application logging unmanaged.
	// +optional
	Logging *FunctionApplicationLogging `json:"logging,omitempty"`

	// ExistingApplicationID points at an existing OCI Functions application.
	// +optional
	// +kubebuilder:validation:Pattern=^ocid1\.fnapp\..+
	ExistingApplicationID string `json:"existingApplicationId,omitempty"`

	// DeletionPolicy controls OCI application cleanup when this Kubernetes FunctionApplication is deleted.
	// Defaults to Retain for safety. Delete is honored only for Managed mode and only when no functions remain in the application.
	// +optional
	// +kubebuilder:default=Retain
	DeletionPolicy FunctionDeletionPolicy `json:"deletionPolicy,omitempty"`
}

// FunctionApplicationLogging contains application-level logging settings.
type FunctionApplicationLogging struct {
	// InvocationLogs configures OCI Functions invocation logs for this application.
	// +optional
	InvocationLogs *FunctionApplicationInvocationLogs `json:"invocationLogs,omitempty"`
}

// FunctionApplicationInvocationLogs configures OCI Functions invocation logs.
type FunctionApplicationInvocationLogs struct {
	// Enabled enables invocation log configuration on the OCI Functions application.
	// Omit spec.logging entirely to leave invocation logging unmanaged.
	// +optional
	// +kubebuilder:default=true
	Enabled *bool `json:"enabled,omitempty"`

	// LogGroupID is the OCID of an existing OCI Logging log group where the Functions service log should be created or updated.
	// Required when invocation logs are enabled.
	// +optional
	// +kubebuilder:validation:Pattern=^ocid1\.loggroup\..+
	LogGroupID string `json:"logGroupId,omitempty"`

	// LogDisplayName is the display name for the OCI Logging service log.
	// Defaults to "<function-application-display-name>-invocation".
	// +optional
	// +kubebuilder:validation:MaxLength=255
	LogDisplayName string `json:"logDisplayName,omitempty"`

	// Service is the OCI Logging service source name.
	// Defaults to functions.
	// +optional
	// +kubebuilder:validation:MinLength=1
	Service string `json:"service,omitempty"`

	// Category is the OCI Logging service log category.
	// Defaults to invoke.
	// +optional
	// +kubebuilder:validation:MinLength=1
	Category string `json:"category,omitempty"`

	// LineFormat is the emitted function log line format.
	// Defaults to JSON when invocation logging is enabled and no format is set.
	// +optional
	// +kubebuilder:default=JSON
	LineFormat FunctionApplicationLogLineFormat `json:"lineFormat,omitempty"`
}

// FunctionApplicationStatus defines the observed state of FunctionApplication.
type FunctionApplicationStatus struct {
	// ObservedGeneration is the last metadata.generation observed by the controller.
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// Phase is a compact state summary for kubectl output.
	// +optional
	Phase FunctionApplicationPhase `json:"phase,omitempty"`

	// ApplicationID is the resolved OCI Functions application OCID.
	// +optional
	ApplicationID string `json:"applicationId,omitempty"`

	// DisplayName is the resolved OCI Functions application display name.
	// +optional
	DisplayName string `json:"displayName,omitempty"`

	// Region is the resolved OCI region.
	// +optional
	Region string `json:"region,omitempty"`

	// Message is a short human-readable status summary.
	// +optional
	Message string `json:"message,omitempty"`

	// LastSyncTime is the last time the controller updated observed status.
	// +optional
	LastSyncTime *metav1.Time `json:"lastSyncTime,omitempty"`

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
// +kubebuilder:printcolumn:name="Application ID",type=string,JSONPath=".status.applicationId"
// +kubebuilder:printcolumn:name="Ready",type=string,JSONPath=".status.conditions[?(@.type=='Ready')].status"
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=".metadata.creationTimestamp"
// FunctionApplication is the Schema for OCI Functions applications.
type FunctionApplication struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   FunctionApplicationSpec   `json:"spec,omitempty"`
	Status FunctionApplicationStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
// FunctionApplicationList contains a list of FunctionApplication.
type FunctionApplicationList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []FunctionApplication `json:"items"`
}

// SetCondition adds or updates a FunctionApplication status condition.
func (f *FunctionApplication) SetCondition(condition metav1.Condition) {
	meta.SetStatusCondition(&f.Status.Conditions, condition)
}

// IsReady reports whether the FunctionApplication is ready to use.
func (f *FunctionApplication) IsReady() bool {
	return meta.IsStatusConditionTrue(f.Status.Conditions, FunctionApplicationConditionReady)
}

// Mode returns the effective FunctionApplication mode when API defaulting has not run.
func (f *FunctionApplication) Mode() FunctionApplicationMode {
	if f.Spec.Mode == FunctionApplicationModeExisting {
		return FunctionApplicationModeExisting
	}
	return FunctionApplicationModeManaged
}

// DeletionPolicy returns the effective deletion policy when API defaulting has not run.
func (f *FunctionApplication) DeletionPolicy() FunctionDeletionPolicy {
	if f.Spec.DeletionPolicy == FunctionDeletionPolicyDelete {
		return FunctionDeletionPolicyDelete
	}
	return FunctionDeletionPolicyRetain
}

func init() {
	SchemeBuilder.Register(&FunctionApplication{}, &FunctionApplicationList{})
}
