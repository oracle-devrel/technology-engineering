// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package lifecycle

import (
	"context"
	"fmt"
	"reflect"
	"strings"

	operatorauth "github.com/oracle/oci-functions-operator/internal/ociauth"
	"github.com/oracle/oci-go-sdk/v65/common"
	ocifunctions "github.com/oracle/oci-go-sdk/v65/functions"
)

const (
	// EnvOCIAuthMode selects the OCI SDK auth provider used in OCI lifecycle mode.
	EnvOCIAuthMode = operatorauth.EnvOCIAuthMode
	// EnvOCIConfigProfile optionally selects a profile from the OCI config file.
	EnvOCIConfigProfile = operatorauth.EnvOCIConfigProfile
	// EnvOCIConfigFile optionally selects a non-default OCI config file path.
	EnvOCIConfigFile = operatorauth.EnvOCIConfigFile
	// EnvOCIRegion optionally supplies the OKE Workload Identity region.
	EnvOCIRegion = operatorauth.EnvOCIRegion

	// OCIAuthModeWorkload uses the OKE Workload Identity auth provider.
	OCIAuthModeWorkload = operatorauth.OCIAuthModeWorkload
	// OCIAuthModeConfig uses a local OCI config file/profile.
	OCIAuthModeConfig = operatorauth.OCIAuthModeConfig
)

type functionsManagementClient interface {
	SetRegion(region string)
	ListApplications(context.Context, ocifunctions.ListApplicationsRequest) (ocifunctions.ListApplicationsResponse, error)
	CreateApplication(context.Context, ocifunctions.CreateApplicationRequest) (ocifunctions.CreateApplicationResponse, error)
	GetApplication(context.Context, ocifunctions.GetApplicationRequest) (ocifunctions.GetApplicationResponse, error)
	UpdateApplication(context.Context, ocifunctions.UpdateApplicationRequest) (ocifunctions.UpdateApplicationResponse, error)
	ListFunctions(context.Context, ocifunctions.ListFunctionsRequest) (ocifunctions.ListFunctionsResponse, error)
	CreateFunction(context.Context, ocifunctions.CreateFunctionRequest) (ocifunctions.CreateFunctionResponse, error)
	GetFunction(context.Context, ocifunctions.GetFunctionRequest) (ocifunctions.GetFunctionResponse, error)
	UpdateFunction(context.Context, ocifunctions.UpdateFunctionRequest) (ocifunctions.UpdateFunctionResponse, error)
}

type managementClientFactory func(common.ConfigurationProvider) (functionsManagementClient, error)
type workloadIdentityProviderFactory = operatorauth.WorkloadIdentityProviderFactory
type configFileProviderFactory = operatorauth.ConfigFileProviderFactory

// OCIOptions configures an OCI lifecycle manager.
type OCIOptions struct {
	AuthMode                        string
	Region                          string
	ConfigProvider                  common.ConfigurationProvider
	WorkloadIdentityProviderFactory workloadIdentityProviderFactory
	ConfigFileProviderFactory       configFileProviderFactory
	ClientFactory                   managementClientFactory
}

// OCI manages OCI Functions lifecycle through the OCI Go SDK.
type OCI struct {
	client functionsManagementClient
}

// NewOCIFromEnvironment constructs an OCI lifecycle manager from OCI-related environment variables.
func NewOCIFromEnvironment() (*OCI, error) {
	configProvider, err := operatorauth.ConfigProviderFromEnvironment()
	if err != nil {
		return nil, err
	}
	return NewOCI(OCIOptions{ConfigProvider: configProvider})
}

// NewOCI constructs an OCI lifecycle manager.
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
		clientFactory = newFunctionsManagementClient
	}

	client, err := clientFactory(configProvider)
	if err != nil {
		return nil, fmt.Errorf("configure OCI Functions management client: %w", err)
	}

	return &OCI{client: client}, nil
}

func newFunctionsManagementClient(configProvider common.ConfigurationProvider) (functionsManagementClient, error) {
	client, err := ocifunctions.NewFunctionsManagementClientWithConfigurationProvider(configProvider)
	if err != nil {
		return nil, err
	}
	return &client, nil
}

// EnsureFunction ensures the OCI application and function exist and match the desired function config.
func (o *OCI) EnsureFunction(ctx context.Context, desired DesiredFunction) (FunctionState, error) {
	if o == nil || o.client == nil {
		return FunctionState{}, fmt.Errorf("oci lifecycle manager is not configured")
	}
	if err := validateDesiredFunction(desired); err != nil {
		return FunctionState{}, err
	}

	o.client.SetRegion(desired.Region)

	application, events, err := o.ensureApplication(ctx, desired)
	if err != nil {
		return FunctionState{ApplicationID: stringValue(application.Id), Events: events}, err
	}

	state := FunctionState{ApplicationID: stringValue(application.Id), Events: events}
	if application.LifecycleState != "" && application.LifecycleState != ocifunctions.ApplicationLifecycleStateActive {
		state.Message = fmt.Sprintf("OCI application %q is %s.", desired.ApplicationName, application.LifecycleState)
		return state, nil
	}

	function, err := o.ensureFunction(ctx, desired, state.ApplicationID)
	if err != nil {
		return state, err
	}

	state.FunctionID = stringValue(function.Id)
	state.InvokeEndpoint = strings.TrimSpace(stringValue(function.InvokeEndpoint))
	if function.LifecycleState != "" && function.LifecycleState != ocifunctions.FunctionLifecycleStateActive {
		state.Message = fmt.Sprintf("OCI function %q is %s.", desired.DisplayName, function.LifecycleState)
		return state, nil
	}
	if state.FunctionID == "" || state.InvokeEndpoint == "" {
		state.Message = "OCI function exists but invoke endpoint is not available yet."
		return state, nil
	}

	state.Ready = true
	state.Message = "Managed OCI Function is ready."
	return state, nil
}

func (o *OCI) ensureApplication(ctx context.Context, desired DesiredFunction) (ocifunctions.Application, []Event, error) {
	response, err := o.client.ListApplications(ctx, ocifunctions.ListApplicationsRequest{
		CompartmentId: common.String(desired.CompartmentID),
		DisplayName:   common.String(desired.ApplicationName),
		Limit:         common.Int(50),
	})
	if err != nil {
		return ocifunctions.Application{}, nil, fmt.Errorf("list OCI Functions applications: %w", err)
	}
	for _, item := range response.Items {
		if stringValue(item.DisplayName) != desired.ApplicationName {
			continue
		}
		if item.LifecycleState == ocifunctions.ApplicationLifecycleStateDeleted || item.LifecycleState == ocifunctions.ApplicationLifecycleStateDeleting {
			continue
		}
		application, err := o.getApplication(ctx, stringValue(item.Id))
		if err != nil {
			return ocifunctions.Application{}, nil, err
		}
		return o.ensureApplicationNSGs(ctx, desired, application)
	}

	created, err := o.client.CreateApplication(ctx, ocifunctions.CreateApplicationRequest{
		CreateApplicationDetails: ocifunctions.CreateApplicationDetails{
			CompartmentId:           common.String(desired.CompartmentID),
			DisplayName:             common.String(desired.ApplicationName),
			SubnetIds:               copyStringSlice(desired.SubnetIDs),
			NetworkSecurityGroupIds: copyStringSlice(desired.ApplicationNSGIDs),
			FreeformTags:            copyStringMap(desired.FreeformTags),
		},
	})
	if err != nil {
		return ocifunctions.Application{}, nil, fmt.Errorf("create OCI Functions application %q: %w", desired.ApplicationName, err)
	}

	events := []Event{}
	if len(desired.ApplicationNSGIDs) > 0 {
		events = append(events, Event{
			Type:    EventTypeNormal,
			Reason:  "ApplicationCreatedWithNSGs",
			Message: fmt.Sprintf("Created OCI Functions application %q with NSGs %s.", desired.ApplicationName, formatStringList(desired.ApplicationNSGIDs)),
		})
	}
	return created.Application, events, nil
}

func (o *OCI) getApplication(ctx context.Context, applicationID string) (ocifunctions.Application, error) {
	if applicationID == "" {
		return ocifunctions.Application{}, fmt.Errorf("OCI application lookup returned an empty application OCID")
	}
	response, err := o.client.GetApplication(ctx, ocifunctions.GetApplicationRequest{ApplicationId: common.String(applicationID)})
	if err != nil {
		return ocifunctions.Application{}, fmt.Errorf("get OCI Functions application %s: %w", applicationID, err)
	}
	return response.Application, nil
}

func (o *OCI) ensureApplicationNSGs(ctx context.Context, desired DesiredFunction, application ocifunctions.Application) (ocifunctions.Application, []Event, error) {
	if !desired.ManageApplicationNSGIDs {
		return application, nil, nil
	}
	if sameStringSet(application.NetworkSecurityGroupIds, desired.ApplicationNSGIDs) {
		return application, nil, nil
	}

	applicationID := stringValue(application.Id)
	updated, err := o.client.UpdateApplication(ctx, ocifunctions.UpdateApplicationRequest{
		ApplicationId: common.String(applicationID),
		UpdateApplicationDetails: ocifunctions.UpdateApplicationDetails{
			NetworkSecurityGroupIds: copyStringSlice(desired.ApplicationNSGIDs),
		},
	})
	if err != nil {
		event := Event{
			Type:    EventTypeWarning,
			Reason:  "ApplicationNSGUpdateFailed",
			Message: fmt.Sprintf("Failed to update OCI Functions application %q NSG configuration to %s: %v", desired.ApplicationName, formatStringList(desired.ApplicationNSGIDs), err),
		}
		return application, []Event{event}, fmt.Errorf("update OCI Functions application %s NSG configuration: %w", applicationID, err)
	}

	event := Event{
		Type:    EventTypeNormal,
		Reason:  "ApplicationNSGsUpdated",
		Message: fmt.Sprintf("Updated OCI Functions application %q NSG configuration to %s.", desired.ApplicationName, formatStringList(desired.ApplicationNSGIDs)),
	}
	return updated.Application, []Event{event}, nil
}

func (o *OCI) ensureFunction(ctx context.Context, desired DesiredFunction, applicationID string) (ocifunctions.Function, error) {
	response, err := o.client.ListFunctions(ctx, ocifunctions.ListFunctionsRequest{
		ApplicationId: common.String(applicationID),
		DisplayName:   common.String(desired.DisplayName),
		Limit:         common.Int(50),
	})
	if err != nil {
		return ocifunctions.Function{}, fmt.Errorf("list OCI Functions in application %s: %w", applicationID, err)
	}
	for _, item := range response.Items {
		if stringValue(item.DisplayName) != desired.DisplayName {
			continue
		}
		if item.LifecycleState == ocifunctions.FunctionLifecycleStateDeleted || item.LifecycleState == ocifunctions.FunctionLifecycleStateDeleting {
			continue
		}
		function, err := o.getFunction(ctx, stringValue(item.Id))
		if err != nil {
			return ocifunctions.Function{}, err
		}
		if functionNeedsUpdate(function, desired) {
			updated, err := o.client.UpdateFunction(ctx, ocifunctions.UpdateFunctionRequest{
				FunctionId: common.String(stringValue(function.Id)),
				UpdateFunctionDetails: ocifunctions.UpdateFunctionDetails{
					Image:            common.String(desired.Image),
					MemoryInMBs:      common.Int64(desired.MemoryInMBs),
					TimeoutInSeconds: common.Int(desired.TimeoutInSeconds),
					Config:           copyStringMap(desired.Config),
					FreeformTags:     copyStringMap(desired.FreeformTags),
				},
			})
			if err != nil {
				return ocifunctions.Function{}, fmt.Errorf("update OCI Function %s: %w", stringValue(function.Id), err)
			}
			return updated.Function, nil
		}
		return function, nil
	}

	created, err := o.client.CreateFunction(ctx, ocifunctions.CreateFunctionRequest{
		CreateFunctionDetails: ocifunctions.CreateFunctionDetails{
			ApplicationId:    common.String(applicationID),
			DisplayName:      common.String(desired.DisplayName),
			Image:            common.String(desired.Image),
			MemoryInMBs:      common.Int64(desired.MemoryInMBs),
			TimeoutInSeconds: common.Int(desired.TimeoutInSeconds),
			Config:           copyStringMap(desired.Config),
			FreeformTags:     copyStringMap(desired.FreeformTags),
		},
	})
	if err != nil {
		return ocifunctions.Function{}, fmt.Errorf("create OCI Function %q: %w", desired.DisplayName, err)
	}
	return created.Function, nil
}

func (o *OCI) getFunction(ctx context.Context, functionID string) (ocifunctions.Function, error) {
	if functionID == "" {
		return ocifunctions.Function{}, fmt.Errorf("OCI function lookup returned an empty function OCID")
	}
	response, err := o.client.GetFunction(ctx, ocifunctions.GetFunctionRequest{FunctionId: common.String(functionID)})
	if err != nil {
		return ocifunctions.Function{}, fmt.Errorf("get OCI Function %s: %w", functionID, err)
	}
	return response.Function, nil
}

func functionNeedsUpdate(function ocifunctions.Function, desired DesiredFunction) bool {
	if stringValue(function.Image) != desired.Image {
		return true
	}
	if int64Value(function.MemoryInMBs) != desired.MemoryInMBs {
		return true
	}
	if intValue(function.TimeoutInSeconds) != desired.TimeoutInSeconds {
		return true
	}
	return !reflect.DeepEqual(nilToEmptyMap(function.Config), nilToEmptyMap(desired.Config))
}

func validateDesiredFunction(desired DesiredFunction) error {
	switch {
	case strings.TrimSpace(desired.Region) == "":
		return fmt.Errorf("managed Function requires spec.config.region")
	case strings.TrimSpace(desired.CompartmentID) == "":
		return fmt.Errorf("managed Function requires spec.config.compartmentId")
	case strings.TrimSpace(desired.ApplicationName) == "":
		return fmt.Errorf("managed Function requires spec.config.applicationName")
	case len(desired.SubnetIDs) == 0:
		return fmt.Errorf("managed Function requires spec.config.subnetIds")
	case desired.ManageApplicationNSGIDs && hasEmptyString(desired.ApplicationNSGIDs):
		return fmt.Errorf("managed Function requires spec.config.nsgIds entries to be non-empty")
	case strings.TrimSpace(desired.DisplayName) == "":
		return fmt.Errorf("managed Function requires spec.config.displayName")
	case strings.TrimSpace(desired.Image) == "":
		return fmt.Errorf("managed Function requires spec.config.image")
	case desired.MemoryInMBs <= 0:
		return fmt.Errorf("managed Function requires spec.config.memoryInMBs")
	case desired.TimeoutInSeconds <= 0:
		return fmt.Errorf("managed Function requires spec.config.timeoutInSeconds")
	}
	return nil
}

func hasEmptyString(values []string) bool {
	for _, value := range values {
		if strings.TrimSpace(value) == "" {
			return true
		}
	}
	return false
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

func stringValue(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}

func int64Value(value *int64) int64 {
	if value == nil {
		return 0
	}
	return *value
}

func intValue(value *int) int {
	if value == nil {
		return 0
	}
	return *value
}

func copyStringMap(values map[string]string) map[string]string {
	if len(values) == 0 {
		return nil
	}
	copied := make(map[string]string, len(values))
	for key, value := range values {
		copied[key] = value
	}
	return copied
}

func copyStringSlice(values []string) []string {
	if values == nil {
		return nil
	}
	return append([]string(nil), values...)
}

func nilToEmptyMap(values map[string]string) map[string]string {
	if values == nil {
		return map[string]string{}
	}
	return values
}

func sameStringSet(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	seen := make(map[string]int, len(a))
	for _, value := range a {
		seen[value]++
	}
	for _, value := range b {
		if seen[value] == 0 {
			return false
		}
		seen[value]--
	}
	return true
}

func formatStringList(values []string) string {
	if len(values) == 0 {
		return "[]"
	}
	return "[" + strings.Join(values, ", ") + "]"
}
