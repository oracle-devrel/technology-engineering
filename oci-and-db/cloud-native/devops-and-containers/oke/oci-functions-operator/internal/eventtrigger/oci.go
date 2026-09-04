// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package eventtrigger

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strings"

	operatorauth "github.com/oracle/oci-functions-operator/internal/ociauth"
	"github.com/oracle/oci-go-sdk/v65/common"
	ocievents "github.com/oracle/oci-go-sdk/v65/events"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

const (
	triggerNameTag      = "oci-functions-operator-trigger-name"
	triggerNamespaceTag = "oci-functions-operator-trigger-namespace"
	triggerUIDTag       = "oci-functions-operator-trigger-uid"
)

type eventsClient interface {
	SetRegion(region string)
	ListRules(context.Context, ocievents.ListRulesRequest) (ocievents.ListRulesResponse, error)
	CreateRule(context.Context, ocievents.CreateRuleRequest) (ocievents.CreateRuleResponse, error)
	GetRule(context.Context, ocievents.GetRuleRequest) (ocievents.GetRuleResponse, error)
	UpdateRule(context.Context, ocievents.UpdateRuleRequest) (ocievents.UpdateRuleResponse, error)
	DeleteRule(context.Context, ocievents.DeleteRuleRequest) (ocievents.DeleteRuleResponse, error)
}

type eventsClientFactory func(common.ConfigurationProvider) (eventsClient, error)
type workloadIdentityProviderFactory = operatorauth.WorkloadIdentityProviderFactory
type configFileProviderFactory = operatorauth.ConfigFileProviderFactory

// OCIOptions configures an OCI Events rule manager.
type OCIOptions struct {
	AuthMode                        string
	Region                          string
	ConfigProvider                  common.ConfigurationProvider
	WorkloadIdentityProviderFactory workloadIdentityProviderFactory
	ConfigFileProviderFactory       configFileProviderFactory
	ClientFactory                   eventsClientFactory
}

// OCI manages OCI Events rules through the OCI Go SDK.
type OCI struct {
	client eventsClient
	region string
}

// NewOCIFromEnvironment constructs an OCI Events manager from OCI-related environment variables.
func NewOCIFromEnvironment() (*OCI, error) {
	return NewOCI(OCIOptions{
		AuthMode: os.Getenv(operatorauth.EnvOCIAuthMode),
		Region:   os.Getenv(operatorauth.EnvOCIRegion),
	})
}

// NewOCI constructs an OCI Events manager.
func NewOCI(options OCIOptions) (*OCI, error) {
	configProvider := options.ConfigProvider
	var err error
	if configProvider == nil {
		configProvider, err = configProviderForAuthMode(options)
		if err != nil {
			return nil, err
		}
	}

	clientFactory := options.ClientFactory
	if clientFactory == nil {
		clientFactory = newEventsClient
	}

	client, err := clientFactory(configProvider)
	if err != nil {
		return nil, fmt.Errorf("configure OCI Events client: %w", err)
	}

	region := strings.TrimSpace(options.Region)
	if region == "" {
		if providerRegion, regionErr := configProvider.Region(); regionErr == nil {
			region = strings.TrimSpace(providerRegion)
		}
	}
	if region != "" {
		client.SetRegion(region)
	}
	return &OCI{client: client, region: region}, nil
}

func newEventsClient(configProvider common.ConfigurationProvider) (eventsClient, error) {
	client, err := ocievents.NewEventsClientWithConfigurationProvider(configProvider)
	if err != nil {
		return nil, err
	}
	return &client, nil
}

// EnsureRule ensures an OCI Events rule exists and targets the desired OCI Function.
func (o *OCI) EnsureRule(ctx context.Context, desired DesiredRule) (RuleState, error) {
	if o == nil || o.client == nil {
		return RuleState{}, fmt.Errorf("oci events manager is not configured")
	}
	if err := validateDesiredRule(desired); err != nil {
		return RuleState{}, err
	}

	region := regionFromOCID(desired.CompartmentID)
	if region != "" {
		o.client.SetRegion(region)
	}

	rule, found, err := o.findRule(ctx, desired)
	if err != nil {
		return RuleState{}, err
	}
	if !found {
		created, err := o.createRule(ctx, desired)
		if err != nil {
			return RuleState{}, fmt.Errorf("create OCI Events rule %q: %w", desired.DisplayName, err)
		}
		ruleID := stringValue(created.Id)
		return RuleState{
			RuleID:  ruleID,
			Ready:   ruleReady(created),
			Message: ruleStateMessage(created, "OCI Events rule created."),
			Events: []Event{{
				Type:    EventTypeNormal,
				Reason:  "RuleCreated",
				Message: fmt.Sprintf("Created OCI Events rule %q targeting Function %s.", desired.DisplayName, desired.FunctionID),
			}},
		}, nil
	}

	if ruleNeedsUpdate(rule, desired) {
		updated, err := o.updateRule(ctx, desired, stringValue(rule.Id))
		if err != nil {
			return RuleState{RuleID: stringValue(rule.Id)}, fmt.Errorf("update OCI Events rule %s: %w", stringValue(rule.Id), err)
		}
		return RuleState{
			RuleID:  stringValue(updated.Id),
			Ready:   ruleReady(updated),
			Message: ruleStateMessage(updated, "OCI Events rule updated."),
			Events: []Event{{
				Type:    EventTypeNormal,
				Reason:  "RuleUpdated",
				Message: fmt.Sprintf("Updated OCI Events rule %q targeting Function %s.", desired.DisplayName, desired.FunctionID),
			}},
		}, nil
	}

	return RuleState{
		RuleID:  stringValue(rule.Id),
		Ready:   ruleReady(rule),
		Message: ruleStateMessage(rule, "OCI Events rule is ready."),
	}, nil
}

// DeleteRule deletes an OCI Events rule by OCID.
func (o *OCI) DeleteRule(ctx context.Context, ruleID string) (RuleState, error) {
	if o == nil || o.client == nil {
		return RuleState{}, fmt.Errorf("oci events manager is not configured")
	}
	ruleID = strings.TrimSpace(ruleID)
	if ruleID == "" {
		return RuleState{Ready: true, Message: "OCI Events rule was not created."}, nil
	}
	_, err := o.client.DeleteRule(ctx, ocievents.DeleteRuleRequest{RuleId: common.String(ruleID)})
	if err != nil {
		if isNotFound(err) {
			return RuleState{RuleID: ruleID, Ready: true, Message: "OCI Events rule was already deleted."}, nil
		}
		return RuleState{RuleID: ruleID}, fmt.Errorf("delete OCI Events rule %s: %w", ruleID, err)
	}
	return RuleState{
		RuleID:  ruleID,
		Ready:   true,
		Message: "OCI Events rule deleted.",
		Events: []Event{{
			Type:    EventTypeNormal,
			Reason:  "RuleDeleted",
			Message: fmt.Sprintf("Deleted OCI Events rule %s.", ruleID),
		}},
	}, nil
}

func (o *OCI) findRule(ctx context.Context, desired DesiredRule) (ocievents.Rule, bool, error) {
	if desired.RuleID != "" {
		response, err := o.client.GetRule(ctx, ocievents.GetRuleRequest{RuleId: common.String(desired.RuleID)})
		if err == nil {
			return response.Rule, true, nil
		}
		if !isNotFound(err) {
			return ocievents.Rule{}, false, fmt.Errorf("get OCI Events rule %s: %w", desired.RuleID, err)
		}
	}

	page := (*string)(nil)
	for {
		response, err := o.client.ListRules(ctx, ocievents.ListRulesRequest{
			CompartmentId: common.String(desired.CompartmentID),
			Limit:         common.Int(50),
			Page:          page,
		})
		if err != nil {
			return ocievents.Rule{}, false, fmt.Errorf("list OCI Events rules in compartment %s: %w", desired.CompartmentID, err)
		}
		for _, summary := range response.Items {
			if summary.LifecycleState == ocievents.RuleLifecycleStateDeleted || summary.LifecycleState == ocievents.RuleLifecycleStateDeleting {
				continue
			}
			if !ruleSummaryMatchesTrigger(summary, desired) {
				continue
			}
			ruleID := stringValue(summary.Id)
			if ruleID == "" {
				continue
			}
			full, err := o.client.GetRule(ctx, ocievents.GetRuleRequest{RuleId: common.String(ruleID)})
			if err != nil {
				return ocievents.Rule{}, false, fmt.Errorf("get OCI Events rule %s: %w", ruleID, err)
			}
			return full.Rule, true, nil
		}
		if response.OpcNextPage == nil || *response.OpcNextPage == "" {
			break
		}
		page = response.OpcNextPage
	}

	return ocievents.Rule{}, false, nil
}

func (o *OCI) createRule(ctx context.Context, desired DesiredRule) (ocievents.Rule, error) {
	log.FromContext(ctx).V(1).Info("creating OCI Events rule",
		"compartmentId", desired.CompartmentID,
		"displayName", desired.DisplayName,
		"functionId", desired.FunctionID,
		"actionType", string(ocievents.ActionDetailsActionTypeFaas),
		"condition", desired.ConditionJSON,
	)
	response, err := o.client.CreateRule(ctx, ocievents.CreateRuleRequest{
		CreateRuleDetails: ocievents.CreateRuleDetails{
			DisplayName:   common.String(desired.DisplayName),
			IsEnabled:     common.Bool(desired.IsEnabled),
			Condition:     common.String(desired.ConditionJSON),
			CompartmentId: common.String(desired.CompartmentID),
			Description:   common.String(desired.Description),
			Actions:       actionDetails(desired),
			FreeformTags:  managedTags(desired),
		},
	})
	if err != nil {
		return ocievents.Rule{}, err
	}
	return response.Rule, nil
}

func (o *OCI) updateRule(ctx context.Context, desired DesiredRule, ruleID string) (ocievents.Rule, error) {
	response, err := o.client.UpdateRule(ctx, ocievents.UpdateRuleRequest{
		RuleId: common.String(ruleID),
		UpdateRuleDetails: ocievents.UpdateRuleDetails{
			DisplayName:  common.String(desired.DisplayName),
			Description:  common.String(desired.Description),
			IsEnabled:    common.Bool(desired.IsEnabled),
			Condition:    common.String(desired.ConditionJSON),
			Actions:      actionDetails(desired),
			FreeformTags: managedTags(desired),
		},
	})
	if err != nil {
		return ocievents.Rule{}, err
	}
	return response.Rule, nil
}

func actionDetails(desired DesiredRule) *ocievents.ActionDetailsList {
	return &ocievents.ActionDetailsList{Actions: []ocievents.ActionDetails{
		ocievents.CreateFaaSActionDetails{
			IsEnabled:   common.Bool(desired.IsEnabled),
			Description: common.String("Invoke OCI Function " + desired.FunctionID),
			FunctionId:  common.String(desired.FunctionID),
		},
	}}
}

func ruleNeedsUpdate(rule ocievents.Rule, desired DesiredRule) bool {
	if stringValue(rule.DisplayName) != desired.DisplayName {
		return true
	}
	if stringValue(rule.Description) != desired.Description {
		return true
	}
	if boolValue(rule.IsEnabled) != desired.IsEnabled {
		return true
	}
	if !sameConditionJSON(stringValue(rule.Condition), desired.ConditionJSON) {
		return true
	}
	if !reflect.DeepEqual(rule.FreeformTags, managedTags(desired)) {
		return true
	}
	return ruleFunctionID(rule) != desired.FunctionID || ruleActionEnabled(rule) != desired.IsEnabled
}

func ruleFunctionID(rule ocievents.Rule) string {
	if rule.Actions == nil {
		return ""
	}
	for _, action := range rule.Actions.Actions {
		if faas, ok := action.(ocievents.FaaSAction); ok {
			return stringValue(faas.FunctionId)
		}
	}
	return ""
}

func ruleActionEnabled(rule ocievents.Rule) bool {
	if rule.Actions == nil {
		return false
	}
	for _, action := range rule.Actions.Actions {
		if _, ok := action.(ocievents.FaaSAction); ok {
			return boolValue(action.GetIsEnabled())
		}
	}
	return false
}

func ruleReady(rule ocievents.Rule) bool {
	switch rule.LifecycleState {
	case ocievents.RuleLifecycleStateActive, ocievents.RuleLifecycleStateInactive:
		return true
	default:
		return false
	}
}

func ruleStateMessage(rule ocievents.Rule, fallback string) string {
	if message := strings.TrimSpace(stringValue(rule.LifecycleMessage)); message != "" {
		return message
	}
	switch rule.LifecycleState {
	case ocievents.RuleLifecycleStateCreating, ocievents.RuleLifecycleStateUpdating:
		return fmt.Sprintf("OCI Events rule %q is %s.", stringValue(rule.DisplayName), rule.LifecycleState)
	case ocievents.RuleLifecycleStateFailed:
		return fmt.Sprintf("OCI Events rule %q is FAILED.", stringValue(rule.DisplayName))
	default:
		return fallback
	}
}

func ruleSummaryMatchesTrigger(summary ocievents.RuleSummary, desired DesiredRule) bool {
	tags := summary.FreeformTags
	return tags[triggerUIDTag] == desired.UID &&
		tags[triggerNameTag] == desired.TriggerName &&
		tags[triggerNamespaceTag] == desired.Namespace
}

func managedTags(desired DesiredRule) map[string]string {
	return map[string]string{
		triggerNameTag:      desired.TriggerName,
		triggerNamespaceTag: desired.Namespace,
		triggerUIDTag:       desired.UID,
	}
}

func validateDesiredRule(desired DesiredRule) error {
	switch {
	case strings.TrimSpace(desired.CompartmentID) == "":
		return fmt.Errorf("FunctionEventTrigger requires spec.compartmentId")
	case strings.TrimSpace(desired.DisplayName) == "":
		return fmt.Errorf("FunctionEventTrigger requires spec.displayName")
	case strings.TrimSpace(desired.ConditionJSON) == "":
		return fmt.Errorf("FunctionEventTrigger requires spec.condition")
	case strings.TrimSpace(desired.FunctionID) == "":
		return fmt.Errorf("FunctionEventTrigger requires referenced Function status.functionId")
	case strings.TrimSpace(desired.TriggerName) == "":
		return fmt.Errorf("FunctionEventTrigger metadata.name is required")
	case strings.TrimSpace(desired.Namespace) == "":
		return fmt.Errorf("FunctionEventTrigger metadata.namespace is required")
	case strings.TrimSpace(desired.UID) == "":
		return fmt.Errorf("FunctionEventTrigger metadata.uid is required")
	}
	return nil
}

func sameConditionJSON(a, b string) bool {
	normalizedA, errA := normalizeJSON(a)
	normalizedB, errB := normalizeJSON(b)
	if errA == nil && errB == nil {
		return normalizedA == normalizedB
	}
	return strings.TrimSpace(a) == strings.TrimSpace(b)
}

func normalizeJSON(value string) (string, error) {
	var decoded interface{}
	if err := json.Unmarshal([]byte(value), &decoded); err != nil {
		return "", err
	}
	encoded, err := json.Marshal(decoded)
	if err != nil {
		return "", err
	}
	return string(encoded), nil
}

func isNotFound(err error) bool {
	serviceErr, ok := common.IsServiceError(err)
	return ok && serviceErr.GetHTTPStatusCode() == 404
}

func configProviderForAuthMode(options OCIOptions) (common.ConfigurationProvider, error) {
	return operatorauth.ConfigProvider(operatorauth.Options{
		AuthMode:                        options.AuthMode,
		Region:                          options.Region,
		ConfigProvider:                  options.ConfigProvider,
		WorkloadIdentityProviderFactory: options.WorkloadIdentityProviderFactory,
		ConfigFileProviderFactory:       options.ConfigFileProviderFactory,
	})
}

func normalizeOCIAuthMode(value string) (string, error) {
	return operatorauth.NormalizeOCIAuthMode(value)
}

func ociConfigProviderFromEnvironment() common.ConfigurationProvider {
	return operatorauth.ConfigFileProviderFromEnvironment()
}

func regionFromOCID(ocid string) string {
	parts := strings.Split(ocid, ".")
	if len(parts) >= 4 && strings.Contains(parts[3], "-") {
		return parts[3]
	}
	return ""
}

func stringValue(value *string) string {
	if value == nil {
		return ""
	}
	return strings.TrimSpace(*value)
}

func boolValue(value *bool) bool {
	return value != nil && *value
}
