// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package eventtrigger

import (
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"

	operatorauth "github.com/oracle/oci-functions-operator/internal/ociauth"
	"github.com/oracle/oci-go-sdk/v65/common"
	sdkAuth "github.com/oracle/oci-go-sdk/v65/common/auth"
	ocievents "github.com/oracle/oci-go-sdk/v65/events"
)

func TestNewOCIWorkloadModeUsesSharedAuthProviderAndRegion(t *testing.T) {
	unsetEnv(t, sdkAuth.ResourcePrincipalVersionEnvVar)
	unsetEnv(t, sdkAuth.ResourcePrincipalRegionEnvVar)

	expectedProvider := common.NewRawConfigurationProvider("tenancy", "user", "me-jeddah-1", "fingerprint", "private-key", nil)
	fakeClient := &fakeEventsClient{}
	workloadCalled := false
	clientCalled := false

	manager, err := NewOCI(OCIOptions{
		AuthMode: operatorauth.OCIAuthModeWorkload,
		Region:   "me-jeddah-1",
		WorkloadIdentityProviderFactory: func(options operatorauth.WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			workloadCalled = true
			if options.Region != "me-jeddah-1" {
				t.Fatalf("workload region = %q, want me-jeddah-1", options.Region)
			}
			if _, ok := os.LookupEnv(sdkAuth.ResourcePrincipalRegionEnvVar); ok {
				t.Fatalf("%s should not be required for Events workload auth", sdkAuth.ResourcePrincipalRegionEnvVar)
			}
			return expectedProvider, nil
		},
		ClientFactory: func(provider common.ConfigurationProvider) (eventsClient, error) {
			clientCalled = true
			if provider != expectedProvider {
				t.Fatalf("config provider = %#v, want shared workload provider", provider)
			}
			return fakeClient, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}
	if manager == nil {
		t.Fatalf("NewOCI returned nil manager")
	}
	if !workloadCalled {
		t.Fatalf("workload provider factory was not called")
	}
	if !clientCalled {
		t.Fatalf("client factory was not called")
	}
	if fakeClient.region != "me-jeddah-1" {
		t.Fatalf("Events client region = %q, want me-jeddah-1", fakeClient.region)
	}
}

func TestNewOCIConfigModeUsesConfigProvider(t *testing.T) {
	expectedProvider := common.NewRawConfigurationProvider("tenancy", "user", "us-ashburn-1", "fingerprint", "private-key", nil)
	fakeClient := &fakeEventsClient{}
	configCalled := false

	_, err := NewOCI(OCIOptions{
		AuthMode: operatorauth.OCIAuthModeConfig,
		ConfigFileProviderFactory: func() common.ConfigurationProvider {
			configCalled = true
			return expectedProvider
		},
		WorkloadIdentityProviderFactory: func(operatorauth.WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			t.Fatalf("workload provider factory was called for config mode")
			return nil, nil
		},
		ClientFactory: func(provider common.ConfigurationProvider) (eventsClient, error) {
			if provider != expectedProvider {
				t.Fatalf("config provider = %#v, want config provider", provider)
			}
			return fakeClient, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}
	if !configCalled {
		t.Fatalf("config provider factory was not called")
	}
	if fakeClient.region != "us-ashburn-1" {
		t.Fatalf("Events client region = %q, want provider region us-ashburn-1", fakeClient.region)
	}
}

func TestEnsureRuleCreateRuleRequestUsesFaaSFunctionAction(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeEventsClient{}
	manager := &OCI{client: fakeClient}
	desired := validDesiredRule()

	state, err := manager.EnsureRule(ctx, desired)
	if err != nil {
		t.Fatalf("EnsureRule returned error: %v", err)
	}
	if !state.Ready {
		t.Fatalf("state.Ready = false, want true")
	}
	if fakeClient.createCalls != 1 {
		t.Fatalf("createCalls = %d, want 1", fakeClient.createCalls)
	}
	details := fakeClient.createdRule.CreateRuleDetails
	if stringValue(details.CompartmentId) != desired.CompartmentID {
		t.Fatalf("compartmentId = %q, want %q", stringValue(details.CompartmentId), desired.CompartmentID)
	}
	if stringValue(details.DisplayName) != desired.DisplayName {
		t.Fatalf("displayName = %q, want %q", stringValue(details.DisplayName), desired.DisplayName)
	}
	if stringValue(details.Condition) != desired.ConditionJSON {
		t.Fatalf("condition = %q, want %q", stringValue(details.Condition), desired.ConditionJSON)
	}
	if details.Actions == nil || len(details.Actions.Actions) != 1 {
		t.Fatalf("actions = %#v, want one FAAS action", details.Actions)
	}
	faas, ok := details.Actions.Actions[0].(ocievents.CreateFaaSActionDetails)
	if !ok {
		t.Fatalf("action = %T, want CreateFaaSActionDetails", details.Actions.Actions[0])
	}
	if stringValue(faas.FunctionId) != desired.FunctionID {
		t.Fatalf("functionId = %q, want %q", stringValue(faas.FunctionId), desired.FunctionID)
	}
	encodedAction, err := json.Marshal(details.Actions.Actions[0])
	if err != nil {
		t.Fatalf("marshal action: %v", err)
	}
	if !strings.Contains(string(encodedAction), `"actionType":"FAAS"`) {
		t.Fatalf("encoded action = %s, want FAAS actionType", encodedAction)
	}
}

func validDesiredRule() DesiredRule {
	return DesiredRule{
		CompartmentID: "ocid1.compartment.oc1..exampleuniqueid",
		DisplayName:   "object-created-trigger",
		Description:   "Invoke managed-hello when objects are created",
		IsEnabled:     true,
		ConditionJSON: `{"eventType":"com.oraclecloud.objectstorage.createobject","data":{"additionalDetails":{"bucketName":"my-bucket"}}}`,
		FunctionID:    "ocid1.fnfunc.oc1.me-jeddah-1.exampleuniqueid",
		TriggerName:   "object-created-trigger",
		Namespace:     "default",
		UID:           "uid-object-created-trigger",
	}
}

type fakeEventsClient struct {
	region      string
	createCalls int
	createdRule ocievents.CreateRuleRequest
}

func (f *fakeEventsClient) SetRegion(region string) {
	f.region = region
}

func (f *fakeEventsClient) ListRules(context.Context, ocievents.ListRulesRequest) (ocievents.ListRulesResponse, error) {
	return ocievents.ListRulesResponse{}, nil
}

func (f *fakeEventsClient) CreateRule(_ context.Context, request ocievents.CreateRuleRequest) (ocievents.CreateRuleResponse, error) {
	f.createCalls++
	f.createdRule = request
	return ocievents.CreateRuleResponse{
		Rule: ocievents.Rule{
			Id:             common.String("ocid1.eventrule.oc1.me-jeddah-1.exampleuniqueid"),
			DisplayName:    request.CreateRuleDetails.DisplayName,
			LifecycleState: ocievents.RuleLifecycleStateActive,
			Condition:      request.CreateRuleDetails.Condition,
		},
	}, nil
}

func (f *fakeEventsClient) GetRule(context.Context, ocievents.GetRuleRequest) (ocievents.GetRuleResponse, error) {
	return ocievents.GetRuleResponse{}, nil
}

func (f *fakeEventsClient) UpdateRule(context.Context, ocievents.UpdateRuleRequest) (ocievents.UpdateRuleResponse, error) {
	return ocievents.UpdateRuleResponse{}, nil
}

func (f *fakeEventsClient) DeleteRule(context.Context, ocievents.DeleteRuleRequest) (ocievents.DeleteRuleResponse, error) {
	return ocievents.DeleteRuleResponse{}, nil
}

func unsetEnv(t *testing.T, key string) {
	t.Helper()
	previous, existed := os.LookupEnv(key)
	if err := os.Unsetenv(key); err != nil {
		t.Fatalf("unset %s: %v", key, err)
	}
	t.Cleanup(func() {
		if existed {
			_ = os.Setenv(key, previous)
			return
		}
		_ = os.Unsetenv(key)
	})
}
