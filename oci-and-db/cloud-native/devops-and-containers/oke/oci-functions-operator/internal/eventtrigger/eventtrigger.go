// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package eventtrigger

import "context"

// DesiredRule is the SDK-free desired state for an OCI Events rule targeting an OCI Function.
type DesiredRule struct {
	CompartmentID string
	DisplayName   string
	Description   string
	IsEnabled     bool
	ConditionJSON string
	FunctionID    string
	RuleID        string
	TriggerName   string
	Namespace     string
	UID           string
}

// EventType is the SDK-free severity for rule lifecycle events.
type EventType string

const (
	// EventTypeNormal describes an expected rule lifecycle change.
	EventTypeNormal EventType = "Normal"
	// EventTypeWarning describes a rule lifecycle failure.
	EventTypeWarning EventType = "Warning"
)

// Event describes an operator-visible OCI Events rule lifecycle action.
type Event struct {
	Type    EventType
	Reason  string
	Message string
}

// RuleState is the SDK-free observed state of an OCI Events rule.
type RuleState struct {
	RuleID  string
	Ready   bool
	Message string
	Events  []Event
}

// Manager reconciles OCI Events rules behind a small SDK-free contract.
type Manager interface {
	EnsureRule(ctx context.Context, desired DesiredRule) (RuleState, error)
	DeleteRule(ctx context.Context, ruleID string) (RuleState, error)
}
