// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package v1alpha1

import (
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const (
	// FunctionConditionReady indicates whether the referenced or desired OCI Function is ready to invoke.
	FunctionConditionReady = "Ready"
)

// FunctionMode declares whether a Function references an existing OCI Function or manages one.
// +kubebuilder:validation:Enum=Existing;Managed
type FunctionMode string

const (
	// FunctionModeExisting references an existing OCI Function.
	FunctionModeExisting FunctionMode = "Existing"
	// FunctionModeManaged creates and updates an OCI Function.
	FunctionModeManaged FunctionMode = "Managed"
)

// FunctionPhase summarizes the controller-observed state of a Function.
// +kubebuilder:validation:Enum=Pending;Ready;Error
type FunctionPhase string

const (
	FunctionPhasePending FunctionPhase = "Pending"
	FunctionPhaseReady   FunctionPhase = "Ready"
	FunctionPhaseError   FunctionPhase = "Error"
)

// FunctionSpec defines the desired state of Function.
// +kubebuilder:validation:XValidation:rule="has(self.functionId) || has(self.existingFunctionOcid) || has(self.config)",message="one of spec.functionId, spec.existingFunctionOcid, or spec.config is required"
// +kubebuilder:validation:XValidation:rule="!(has(self.config) && (has(self.functionId) || has(self.existingFunctionOcid)))",message="spec.config is mutually exclusive with existing function references"
// +kubebuilder:validation:XValidation:rule="!(has(self.functionId) && has(self.existingFunctionOcid))",message="spec.functionId and spec.existingFunctionOcid are mutually exclusive"
// +kubebuilder:validation:XValidation:rule="!(has(self.functionId) || has(self.existingFunctionOcid)) || has(self.invokeEndpoint)",message="existing Function mode requires spec.invokeEndpoint"
// +kubebuilder:validation:XValidation:rule="!has(self.mode) || self.mode != 'Existing' || ((has(self.functionId) || has(self.existingFunctionOcid)) && has(self.invokeEndpoint))",message="mode Existing requires spec.functionId or spec.existingFunctionOcid and spec.invokeEndpoint"
// +kubebuilder:validation:XValidation:rule="!has(self.mode) || self.mode != 'Managed' || has(self.config)",message="mode Managed requires spec.config"
type FunctionSpec struct {
	// Mode selects whether the operator references an existing OCI Function or manages one.
	// When omitted, mode is inferred from functionId/existingFunctionOcid or config.
	// +optional
	Mode FunctionMode `json:"mode,omitempty"`

	// FunctionID points at an existing OCI Functions function OCID.
	// +optional
	// +kubebuilder:validation:Pattern=^ocid1\.fnfunc\..+
	FunctionID string `json:"functionId,omitempty"`

	// ExistingFunctionOCID points at an existing OCI Functions function.
	// Deprecated: use FunctionID.
	// +optional
	// +kubebuilder:validation:Pattern=^ocid1\.fnfunc\..+
	ExistingFunctionOCID string `json:"existingFunctionOcid,omitempty"`

	// InvokeEndpoint is the OCI Functions invoke endpoint for an existing function.
	// Managed functions discover this endpoint into status.
	// +optional
	// +kubebuilder:validation:Pattern="^https?://.+"
	InvokeEndpoint string `json:"invokeEndpoint,omitempty"`

	// Config describes desired function configuration for managed lifecycle.
	// +optional
	Config *FunctionConfig `json:"config,omitempty"`
}

// FunctionConfig contains the minimal OCI Functions configuration this API manages.
type FunctionConfig struct {
	// Region is the OCI region identifier, such as me-jeddah-1.
	// +kubebuilder:validation:MinLength=1
	Region string `json:"region"`

	// CompartmentID is the compartment OCID for the managed application/function.
	// +kubebuilder:validation:Pattern=^ocid1\.compartment\..+
	CompartmentID string `json:"compartmentId"`

	// ApplicationName is the display name of the OCI Functions application to ensure.
	// +kubebuilder:validation:MinLength=1
	// +kubebuilder:validation:MaxLength=255
	ApplicationName string `json:"applicationName"`

	// SubnetIDs are the subnet OCIDs for a newly created application.
	// +kubebuilder:validation:MinItems=1
	// +listType=atomic
	SubnetIDs []string `json:"subnetIds"`

	// NSGIDs are the Network Security Group OCIDs to attach to the managed OCI Functions application.
	// When omitted, the operator leaves NSGs unmanaged on existing applications.
	// Set an empty list to explicitly clear all NSGs from an existing application.
	// Set a non-empty list to create new applications with those NSGs and reconcile existing applications to that set.
	// +optional
	// +kubebuilder:validation:items:Pattern=^ocid1\.networksecuritygroup\..+
	// +listType=atomic
	NSGIDs []string `json:"nsgIds,omitempty"`

	// ApplicationOCID is an existing OCI Functions application OCID.
	// Deprecated: use applicationName and subnetIds for managed application reconciliation.
	// +optional
	// +kubebuilder:validation:Pattern=^ocid1\.fnapp\..+
	ApplicationOCID string `json:"applicationOcid,omitempty"`

	// DisplayName is the OCI function display name.
	// +kubebuilder:validation:MinLength=1
	// +kubebuilder:validation:MaxLength=255
	DisplayName string `json:"displayName"`

	// Image is the OCI Functions-compatible runtime image reference.
	// Managed functions should use a same-region OCIR image, such as jed.ocir.io/... for me-jeddah-1.
	// +kubebuilder:validation:MinLength=1
	Image string `json:"image"`

	// MemoryInMBs is the memory size to configure.
	// +optional
	// +kubebuilder:default=128
	// +kubebuilder:validation:Enum=128;256;512;1024;2048
	MemoryInMBs int32 `json:"memoryInMBs,omitempty"`

	// MemoryInMB is a deprecated alias for MemoryInMBs.
	// Deprecated: use memoryInMBs.
	// +optional
	// +kubebuilder:validation:Enum=128;256;512;1024;2048
	MemoryInMB int32 `json:"memoryInMB,omitempty"`

	// TimeoutInSeconds is the max execution time for the function.
	// +optional
	// +kubebuilder:default=30
	// +kubebuilder:validation:Minimum=1
	// +kubebuilder:validation:Maximum=300
	TimeoutInSeconds int32 `json:"timeoutInSeconds,omitempty"`

	// Config is the OCI function configuration map.
	// +optional
	Config map[string]string `json:"config,omitempty"`

	// Environment is a deprecated alias for Config.
	// Deprecated: use config.
	// +optional
	Environment map[string]string `json:"environment,omitempty"`

	// FreeformTags are OCI freeform tags to apply to managed resources.
	// +optional
	FreeformTags map[string]string `json:"freeformTags,omitempty"`
}

// FunctionStatus defines the observed state of Function.
type FunctionStatus struct {
	// ObservedGeneration is the last metadata.generation observed by the controller.
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// Phase is a compact state summary for kubectl output.
	// +optional
	Phase FunctionPhase `json:"phase,omitempty"`

	// FunctionOCID is the resolved OCI function OCID when known.
	// +optional
	FunctionOCID string `json:"functionOcid,omitempty"`

	// FunctionID is the resolved OCI function OCID when known.
	// +optional
	FunctionID string `json:"functionId,omitempty"`

	// ApplicationID is the resolved OCI application OCID when known.
	// +optional
	ApplicationID string `json:"applicationId,omitempty"`

	// InvokeEndpoint is the resolved OCI Functions invoke endpoint when known.
	// +optional
	InvokeEndpoint string `json:"invokeEndpoint,omitempty"`

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
// +kubebuilder:printcolumn:name="Function ID",type=string,JSONPath=".status.functionId"
// +kubebuilder:printcolumn:name="Ready",type=string,JSONPath=".status.conditions[?(@.type=='Ready')].status"
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=".metadata.creationTimestamp"
// Function is the Schema for the functions API.
type Function struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   FunctionSpec   `json:"spec,omitempty"`
	Status FunctionStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
// FunctionList contains a list of Function.
type FunctionList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Function `json:"items"`
}

// SetCondition adds or updates a Function status condition.
func (f *Function) SetCondition(condition metav1.Condition) {
	meta.SetStatusCondition(&f.Status.Conditions, condition)
}

// IsReady reports whether the Function is ready to invoke.
func (f *Function) IsReady() bool {
	return meta.IsStatusConditionTrue(f.Status.Conditions, FunctionConditionReady)
}

func init() {
	SchemeBuilder.Register(&Function{}, &FunctionList{})
}
