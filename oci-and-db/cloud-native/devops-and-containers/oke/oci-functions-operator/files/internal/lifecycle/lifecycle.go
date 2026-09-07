// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package lifecycle

import "context"

// DesiredFunction is the SDK-free desired state for a managed OCI Function.
type DesiredFunction struct {
	Region                  string
	CompartmentID           string
	ApplicationName         string
	SubnetIDs               []string
	ApplicationNSGIDs       []string
	ManageApplicationNSGIDs bool
	DisplayName             string
	Image                   string
	MemoryInMBs             int64
	TimeoutInSeconds        int
	Config                  map[string]string
	FreeformTags            map[string]string
}

// DesiredFunctionInApplication is the SDK-free desired state for a function in an already resolved OCI application.
type DesiredFunctionInApplication struct {
	Region           string
	ApplicationID    string
	DisplayName      string
	Image            string
	MemoryInMBs      int64
	TimeoutInSeconds int
	Config           map[string]string
	FreeformTags     map[string]string
}

// ManagedFunctionDeleteTarget identifies a managed OCI Function to delete.
type ManagedFunctionDeleteTarget struct {
	Region          string
	CompartmentID   string
	ApplicationName string
	ApplicationID   string
	DisplayName     string
	FunctionID      string
}

// ApplicationMode selects managed or existing application behavior in the lifecycle manager.
type ApplicationMode string

const (
	// ApplicationModeManaged creates or updates the OCI Functions application.
	ApplicationModeManaged ApplicationMode = "Managed"
	// ApplicationModeExisting only resolves an existing OCI Functions application.
	ApplicationModeExisting ApplicationMode = "Existing"
)

// DesiredApplication is the SDK-free desired state for an OCI Functions application.
type DesiredApplication struct {
	Mode                           ApplicationMode
	Region                         string
	CompartmentID                  string
	DisplayName                    string
	SubnetIDs                      []string
	ApplicationNSGIDs              []string
	ManageApplicationNSGIDs        bool
	Config                         map[string]string
	FreeformTags                   map[string]string
	Logging                        *ApplicationLogging
	ExistingApplicationID          string
	ManageApplicationConfiguration bool
	ManageApplicationLogging       bool
}

// ApplicationLogging is the SDK-free desired logging configuration for an OCI Functions application.
type ApplicationLogging struct {
	InvocationLogs *ApplicationInvocationLogs
}

// ApplicationInvocationLogs describes OCI Functions invocation log configuration.
type ApplicationInvocationLogs struct {
	Enabled        bool
	LogGroupID     string
	LogDisplayName string
	Service        string
	Category       string
	LineFormat     string
}

// ApplicationState is the SDK-free observed state for an OCI Functions application.
type ApplicationState struct {
	ApplicationID string
	DisplayName   string
	Region        string
	Ready         bool
	Message       string
	Events        []Event
}

// ApplicationDeleteTarget identifies an OCI Functions application to delete.
type ApplicationDeleteTarget struct {
	Region        string
	ApplicationID string
	DisplayName   string
	CompartmentID string
}

// ApplicationDeletionState is the SDK-free outcome of OCI Functions application cleanup.
type ApplicationDeletionState struct {
	ApplicationID string
	Deleted       bool
	Blocked       bool
	Message       string
	Events        []Event
}

// EventType is the SDK-free severity for lifecycle events.
type EventType string

const (
	// EventTypeNormal describes an expected lifecycle change.
	EventTypeNormal EventType = "Normal"
	// EventTypeWarning describes a lifecycle failure.
	EventTypeWarning EventType = "Warning"
)

// Event describes an operator-visible lifecycle action.
type Event struct {
	Type    EventType
	Reason  string
	Message string
}

// FunctionState is the SDK-free observed state for a managed OCI Function.
type FunctionState struct {
	ApplicationID  string
	FunctionID     string
	InvokeEndpoint string
	Ready          bool
	Message        string
	Events         []Event
}

// FunctionDeletionState is the SDK-free outcome of managed OCI Function cleanup.
type FunctionDeletionState struct {
	ApplicationID string
	FunctionID    string
	Deleted       bool
	Message       string
	Events        []Event
}

// Manager reconciles OCI Functions lifecycle behind a small SDK-free contract.
type Manager interface {
	EnsureFunction(ctx context.Context, desired DesiredFunction) (FunctionState, error)
	EnsureFunctionInApplication(ctx context.Context, desired DesiredFunctionInApplication) (FunctionState, error)
	DeleteManagedFunction(ctx context.Context, target ManagedFunctionDeleteTarget) (FunctionDeletionState, error)
	EnsureApplication(ctx context.Context, desired DesiredApplication) (ApplicationState, error)
	DeleteApplication(ctx context.Context, target ApplicationDeleteTarget) (ApplicationDeletionState, error)
}
