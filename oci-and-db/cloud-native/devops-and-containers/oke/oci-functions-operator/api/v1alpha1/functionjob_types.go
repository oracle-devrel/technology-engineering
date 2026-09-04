// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package v1alpha1

import (
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

const (
	// FunctionJobConditionPending indicates whether the job is waiting to invoke payloads.
	FunctionJobConditionPending = "Pending"
	// FunctionJobConditionRunning indicates whether the job has remaining invocation work.
	FunctionJobConditionRunning = "Running"
	// FunctionJobConditionFunctionResolved indicates whether the referenced Function was resolved.
	FunctionJobConditionFunctionResolved = "FunctionResolved"
	// FunctionJobConditionComplete indicates whether all requested invocations succeeded.
	FunctionJobConditionComplete = "Complete"
	// FunctionJobConditionFailed indicates whether the job has failed.
	FunctionJobConditionFailed = "Failed"
)

// FunctionJobPhase summarizes job progress.
// +kubebuilder:validation:Enum=Pending;Running;Succeeded;Failed
type FunctionJobPhase string

const (
	FunctionJobPhasePending   FunctionJobPhase = "Pending"
	FunctionJobPhaseRunning   FunctionJobPhase = "Running"
	FunctionJobPhaseSucceeded FunctionJobPhase = "Succeeded"
	FunctionJobPhaseFailed    FunctionJobPhase = "Failed"
)

// InvocationPhase summarizes one invocation attempt.
// +kubebuilder:validation:Enum=Pending;Running;Succeeded;Failed
type InvocationPhase string

const (
	InvocationPhasePending   InvocationPhase = "Pending"
	InvocationPhaseRunning   InvocationPhase = "Running"
	InvocationPhaseSucceeded InvocationPhase = "Succeeded"
	InvocationPhaseFailed    InvocationPhase = "Failed"
)

// FunctionJobSpec defines the desired state of FunctionJob.
// +kubebuilder:validation:XValidation:rule="!(has(self.payload) && has(self.payloads))",message="spec.payload and spec.payloads are mutually exclusive"
type FunctionJobSpec struct {
	// FunctionRef references a Function in the same namespace.
	FunctionRef FunctionReference `json:"functionRef"`

	// Payload is an inline JSON object passed to each invocation.
	// +optional
	// +kubebuilder:validation:Schemaless
	// +kubebuilder:validation:Type=object
	// +kubebuilder:pruning:PreserveUnknownFields
	Payload *runtime.RawExtension `json:"payload,omitempty"`

	// Payloads is a small ordered set of inline JSON objects passed to invocations.
	// +optional
	// +listType=atomic
	// +kubebuilder:validation:MinItems=1
	// +kubebuilder:validation:MaxItems=100
	Payloads []runtime.RawExtension `json:"payloads,omitempty"`

	// Parallelism is the maximum number of payloads invoked during one reconciliation.
	// +optional
	// +kubebuilder:default=1
	// +kubebuilder:validation:Minimum=1
	// +kubebuilder:validation:Maximum=100
	Parallelism int32 `json:"parallelism,omitempty"`

	// RetryLimit is the number of retries allowed for a failed invocation.
	// +optional
	// +kubebuilder:default=0
	// +kubebuilder:validation:Minimum=0
	// +kubebuilder:validation:Maximum=10
	RetryLimit int32 `json:"retryLimit,omitempty"`
}

// FunctionReference names a Function in the same namespace as the FunctionJob.
type FunctionReference struct {
	// Name is the referenced Function name.
	// +kubebuilder:validation:MinLength=1
	Name string `json:"name"`
}

// FunctionJobStatus defines the observed state of FunctionJob.
type FunctionJobStatus struct {
	// ObservedGeneration is the last metadata.generation observed by the controller.
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// Phase is a compact state summary for kubectl output.
	// +optional
	Phase FunctionJobPhase `json:"phase,omitempty"`

	// StartTime is when the controller first observed the job.
	// +optional
	StartTime *metav1.Time `json:"startTime,omitempty"`

	// CompletionTime is when the job reached a terminal phase.
	// +optional
	CompletionTime *metav1.Time `json:"completionTime,omitempty"`

	// Active is the number of invocations currently in progress.
	// +optional
	Active int32 `json:"active,omitempty"`

	// Succeeded is the number of successful invocations.
	// +optional
	Succeeded int32 `json:"succeeded,omitempty"`

	// Failed is the number of failed invocations.
	// +optional
	Failed int32 `json:"failed,omitempty"`

	// Retries is the total number of retry attempts used across invocations.
	// +optional
	Retries int32 `json:"retries,omitempty"`

	// LastError is the most recent invocation or validation error observed by the controller.
	// +optional
	LastError string `json:"lastError,omitempty"`

	// LastOCIRequestID is the most recent OCI request ID or function call ID observed by the controller.
	// +optional
	LastOCIRequestID string `json:"lastOciRequestId,omitempty"`

	// InvocationStatuses records per-payload invocation status for aggregation and describe output.
	// +optional
	// +listType=map
	// +listMapKey=index
	InvocationStatuses []FunctionJobInvocationStatus `json:"invocationStatuses,omitempty"`

	// Conditions contain detailed state transitions.
	// +optional
	// +patchMergeKey=type
	// +patchStrategy=merge
	// +listType=map
	// +listMapKey=type
	Conditions []metav1.Condition `json:"conditions,omitempty" patchStrategy:"merge" patchMergeKey:"type"`
}

// FunctionJobInvocationStatus records the state of one requested payload invocation.
type FunctionJobInvocationStatus struct {
	// Index is the zero-based requested invocation index.
	Index int32 `json:"index"`

	// PayloadDigest is a stable digest of the inline payload observed for this index.
	// +optional
	PayloadDigest string `json:"payloadDigest,omitempty"`

	// Phase is the observed invocation state.
	// +optional
	Phase InvocationPhase `json:"phase,omitempty"`

	// Attempts is the number of attempts made for this invocation.
	// +optional
	Attempts int32 `json:"attempts,omitempty"`

	// InvocationID is the OCI invocation ID when the invoker returns one.
	// +optional
	InvocationID string `json:"invocationId,omitempty"`

	// OCIRequestID is the OCI opc-request-id for this invocation when available.
	// +optional
	OCIRequestID string `json:"ociRequestId,omitempty"`

	// StatusCode is an invoker-specific status code when available.
	// +optional
	StatusCode int32 `json:"statusCode,omitempty"`

	// Error contains the last invocation error, if any.
	// +optional
	Error string `json:"error,omitempty"`

	// CompletedAt is when this invocation reached a terminal phase.
	// +optional
	CompletedAt *metav1.Time `json:"completedAt,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:resource:scope=Namespaced,categories={oci,functions}
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=".status.phase"
// +kubebuilder:printcolumn:name="Succeeded",type=integer,JSONPath=".status.succeeded"
// +kubebuilder:printcolumn:name="Failed",type=integer,JSONPath=".status.failed"
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=".metadata.creationTimestamp"
// FunctionJob is the Schema for the functionjobs API.
type FunctionJob struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   FunctionJobSpec   `json:"spec,omitempty"`
	Status FunctionJobStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
// FunctionJobList contains a list of FunctionJob.
type FunctionJobList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []FunctionJob `json:"items"`
}

// DesiredParallelism returns the effective parallelism when API defaulting has not run.
func (j *FunctionJob) DesiredParallelism() int32 {
	if j.Spec.Parallelism < 1 {
		return 1
	}
	return j.Spec.Parallelism
}

// DesiredRetryLimit returns the effective retry limit when API defaulting has not run.
func (j *FunctionJob) DesiredRetryLimit() int32 {
	if j.Spec.RetryLimit < 0 {
		return 0
	}
	return j.Spec.RetryLimit
}

// SetCondition adds or updates a FunctionJob status condition.
func (j *FunctionJob) SetCondition(condition metav1.Condition) {
	meta.SetStatusCondition(&j.Status.Conditions, condition)
}

// IsTerminal reports whether the FunctionJob has reached a final state.
func (j *FunctionJob) IsTerminal() bool {
	return j.Status.Phase == FunctionJobPhaseSucceeded || j.Status.Phase == FunctionJobPhaseFailed
}

func init() {
	SchemeBuilder.Register(&FunctionJob{}, &FunctionJobList{})
}
