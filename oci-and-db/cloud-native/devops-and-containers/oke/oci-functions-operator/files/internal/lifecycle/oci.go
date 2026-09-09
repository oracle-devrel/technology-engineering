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
	ocilogging "github.com/oracle/oci-go-sdk/v65/logging"
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

	defaultInvocationLogService  = "functions"
	defaultInvocationLogCategory = "invoke"
)

type functionsManagementClient interface {
	SetRegion(region string)
	ListApplications(context.Context, ocifunctions.ListApplicationsRequest) (ocifunctions.ListApplicationsResponse, error)
	CreateApplication(context.Context, ocifunctions.CreateApplicationRequest) (ocifunctions.CreateApplicationResponse, error)
	GetApplication(context.Context, ocifunctions.GetApplicationRequest) (ocifunctions.GetApplicationResponse, error)
	UpdateApplication(context.Context, ocifunctions.UpdateApplicationRequest) (ocifunctions.UpdateApplicationResponse, error)
	DeleteApplication(context.Context, ocifunctions.DeleteApplicationRequest) (ocifunctions.DeleteApplicationResponse, error)
	ListFunctions(context.Context, ocifunctions.ListFunctionsRequest) (ocifunctions.ListFunctionsResponse, error)
	CreateFunction(context.Context, ocifunctions.CreateFunctionRequest) (ocifunctions.CreateFunctionResponse, error)
	GetFunction(context.Context, ocifunctions.GetFunctionRequest) (ocifunctions.GetFunctionResponse, error)
	UpdateFunction(context.Context, ocifunctions.UpdateFunctionRequest) (ocifunctions.UpdateFunctionResponse, error)
	DeleteFunction(context.Context, ocifunctions.DeleteFunctionRequest) (ocifunctions.DeleteFunctionResponse, error)
}

type loggingManagementClient interface {
	SetRegion(region string)
	ListLogs(context.Context, ocilogging.ListLogsRequest) (ocilogging.ListLogsResponse, error)
	CreateLog(context.Context, ocilogging.CreateLogRequest) (ocilogging.CreateLogResponse, error)
	UpdateLog(context.Context, ocilogging.UpdateLogRequest) (ocilogging.UpdateLogResponse, error)
}

type managementClientFactory func(common.ConfigurationProvider) (functionsManagementClient, error)
type loggingManagementClientFactory func(common.ConfigurationProvider) (loggingManagementClient, error)
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
	LoggingClientFactory            loggingManagementClientFactory
}

// OCI manages OCI Functions lifecycle through the OCI Go SDK.
type OCI struct {
	client        functionsManagementClient
	loggingClient loggingManagementClient
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

	loggingClientFactory := options.LoggingClientFactory
	if loggingClientFactory == nil {
		loggingClientFactory = newLoggingManagementClient
	}
	loggingClient, err := loggingClientFactory(configProvider)
	if err != nil {
		return nil, fmt.Errorf("configure OCI Logging management client: %w", err)
	}

	return &OCI{client: client, loggingClient: loggingClient}, nil
}

func newFunctionsManagementClient(configProvider common.ConfigurationProvider) (functionsManagementClient, error) {
	client, err := ocifunctions.NewFunctionsManagementClientWithConfigurationProvider(configProvider)
	if err != nil {
		return nil, err
	}
	return &client, nil
}

func newLoggingManagementClient(configProvider common.ConfigurationProvider) (loggingManagementClient, error) {
	client, err := ocilogging.NewLoggingManagementClientWithConfigurationProvider(configProvider)
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

	application, events, err := o.ensureApplication(ctx, desiredApplicationFromFunction(desired))
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

// EnsureFunctionInApplication ensures an OCI Function exists in an already resolved OCI Functions application.
func (o *OCI) EnsureFunctionInApplication(ctx context.Context, desired DesiredFunctionInApplication) (FunctionState, error) {
	if o == nil || o.client == nil {
		return FunctionState{}, fmt.Errorf("oci lifecycle manager is not configured")
	}
	if err := validateDesiredFunctionInApplication(desired); err != nil {
		return FunctionState{}, err
	}

	o.client.SetRegion(desired.Region)

	function, err := o.ensureFunction(ctx, DesiredFunction{
		DisplayName:      desired.DisplayName,
		Image:            desired.Image,
		MemoryInMBs:      desired.MemoryInMBs,
		TimeoutInSeconds: desired.TimeoutInSeconds,
		Config:           desired.Config,
		FreeformTags:     desired.FreeformTags,
	}, desired.ApplicationID)
	if err != nil {
		return FunctionState{ApplicationID: desired.ApplicationID}, err
	}

	state := FunctionState{
		ApplicationID:  desired.ApplicationID,
		FunctionID:     stringValue(function.Id),
		InvokeEndpoint: strings.TrimSpace(stringValue(function.InvokeEndpoint)),
	}
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

// EnsureApplication ensures or resolves an OCI Functions application.
func (o *OCI) EnsureApplication(ctx context.Context, desired DesiredApplication) (ApplicationState, error) {
	if o == nil || o.client == nil {
		return ApplicationState{}, fmt.Errorf("oci lifecycle manager is not configured")
	}
	if err := validateDesiredApplication(desired); err != nil {
		return ApplicationState{}, err
	}

	region := effectiveApplicationRegion(desired.Region, desired.ExistingApplicationID)
	o.client.SetRegion(region)

	application, events, err := o.ensureApplication(ctx, desired)
	if err != nil {
		return ApplicationState{
			ApplicationID: stringValue(application.Id),
			DisplayName:   stringValue(application.DisplayName),
			Region:        region,
			Events:        events,
		}, err
	}
	if applicationInvocationLoggingEnabled(desired.Logging) {
		logEvents, err := o.ensureApplicationInvocationLog(ctx, desired, stringValue(application.Id), region)
		events = append(events, logEvents...)
		if err != nil {
			state := ApplicationState{
				ApplicationID: stringValue(application.Id),
				DisplayName:   stringValue(application.DisplayName),
				Region:        region,
				Events:        events,
			}
			if message, ok := pendingApplicationLogMessage(err); ok {
				state.Message = message
				return state, nil
			}
			return state, err
		}
	}

	state := ApplicationState{
		ApplicationID: stringValue(application.Id),
		DisplayName:   stringValue(application.DisplayName),
		Region:        region,
		Events:        events,
	}
	switch application.LifecycleState {
	case "", ocifunctions.ApplicationLifecycleStateActive:
		state.Ready = state.ApplicationID != ""
		state.Message = "OCI Functions application is ready."
	case ocifunctions.ApplicationLifecycleStateFailed:
		state.Message = fmt.Sprintf("OCI Functions application %q is FAILED.", state.DisplayName)
	default:
		state.Message = fmt.Sprintf("OCI Functions application %q is %s.", state.DisplayName, application.LifecycleState)
	}
	if state.ApplicationID == "" {
		state.Message = "OCI Functions application exists but OCID is not available yet."
	}
	return state, nil
}

// DeleteManagedFunction deletes a managed OCI Function and intentionally retains the OCI application.
func (o *OCI) DeleteManagedFunction(ctx context.Context, target ManagedFunctionDeleteTarget) (FunctionDeletionState, error) {
	if o == nil || o.client == nil {
		return FunctionDeletionState{}, fmt.Errorf("oci lifecycle manager is not configured")
	}
	region := effectiveFunctionRegion(target.Region, target.FunctionID)
	if strings.TrimSpace(region) == "" {
		region = effectiveApplicationRegion("", target.ApplicationID)
	}
	if strings.TrimSpace(region) == "" {
		return FunctionDeletionState{}, fmt.Errorf("managed Function deletion requires spec.config.region or status.functionId with a region")
	}

	o.client.SetRegion(region)

	functionID := strings.TrimSpace(target.FunctionID)
	state := FunctionDeletionState{FunctionID: functionID}
	if functionID == "" {
		resolved, err := o.resolveFunctionForDelete(ctx, target)
		if err != nil {
			return state, err
		}
		state.ApplicationID = resolved.ApplicationID
		state.FunctionID = resolved.FunctionID
		functionID = resolved.FunctionID
		if functionID == "" {
			state.Message = "Managed OCI Function was not found; nothing to delete. OCI Functions application retained."
			state.Events = []Event{{
				Type:    EventTypeNormal,
				Reason:  "ManagedFunctionAlreadyDeleted",
				Message: state.Message,
			}}
			return state, nil
		}
	}

	if err := o.deleteFunctionByID(ctx, functionID); err != nil {
		return state, err
	}

	state.Deleted = true
	state.Message = fmt.Sprintf("Deleted managed OCI Function %s. OCI Functions application retained.", functionID)
	state.Events = []Event{{
		Type:    EventTypeNormal,
		Reason:  "ManagedFunctionDeleted",
		Message: state.Message,
	}}
	return state, nil
}

// DeleteApplication deletes an OCI Functions application only when it has no active functions.
func (o *OCI) DeleteApplication(ctx context.Context, target ApplicationDeleteTarget) (ApplicationDeletionState, error) {
	if o == nil || o.client == nil {
		return ApplicationDeletionState{}, fmt.Errorf("oci lifecycle manager is not configured")
	}
	region := effectiveApplicationRegion(target.Region, target.ApplicationID)
	if strings.TrimSpace(region) == "" {
		return ApplicationDeletionState{}, fmt.Errorf("FunctionApplication deletion requires spec.region or status.applicationId with a region")
	}
	applicationID := strings.TrimSpace(target.ApplicationID)
	if applicationID == "" {
		return ApplicationDeletionState{}, fmt.Errorf("FunctionApplication deletion requires status.applicationId")
	}

	o.client.SetRegion(region)

	functions, err := o.client.ListFunctions(ctx, ocifunctions.ListFunctionsRequest{
		ApplicationId: common.String(applicationID),
		Limit:         common.Int(50),
	})
	if err != nil {
		return ApplicationDeletionState{ApplicationID: applicationID}, fmt.Errorf("list OCI Functions before deleting application %s: %w", applicationID, err)
	}
	activeFunctions := 0
	if stringValue(functions.OpcNextPage) != "" {
		activeFunctions++
	}
	for _, function := range functions.Items {
		if function.LifecycleState == ocifunctions.FunctionLifecycleStateDeleted || function.LifecycleState == ocifunctions.FunctionLifecycleStateDeleting {
			continue
		}
		activeFunctions++
	}
	if activeFunctions > 0 {
		message := fmt.Sprintf("Retained OCI Functions application %s because %d function(s) remain in it.", applicationID, activeFunctions)
		return ApplicationDeletionState{
			ApplicationID: applicationID,
			Blocked:       true,
			Message:       message,
			Events: []Event{{
				Type:    EventTypeWarning,
				Reason:  "ApplicationDeleteBlocked",
				Message: message,
			}},
		}, nil
	}

	_, err = o.client.DeleteApplication(ctx, ocifunctions.DeleteApplicationRequest{ApplicationId: common.String(applicationID)})
	if err != nil {
		if isOCIServiceNotFound(err) {
			message := "OCI Functions application was not found; nothing to delete."
			return ApplicationDeletionState{
				ApplicationID: applicationID,
				Deleted:       true,
				Message:       message,
				Events: []Event{{
					Type:    EventTypeNormal,
					Reason:  "ApplicationAlreadyDeleted",
					Message: message,
				}},
			}, nil
		}
		return ApplicationDeletionState{ApplicationID: applicationID}, fmt.Errorf("delete OCI Functions application %s: %w", applicationID, err)
	}

	message := fmt.Sprintf("Deleted OCI Functions application %s.", applicationID)
	return ApplicationDeletionState{
		ApplicationID: applicationID,
		Deleted:       true,
		Message:       message,
		Events: []Event{{
			Type:    EventTypeNormal,
			Reason:  "ApplicationDeleted",
			Message: message,
		}},
	}, nil
}

func (o *OCI) deleteFunctionByID(ctx context.Context, functionID string) error {
	if strings.TrimSpace(functionID) == "" {
		return fmt.Errorf("managed Function deletion requires an OCI Function OCID")
	}
	_, err := o.client.DeleteFunction(ctx, ocifunctions.DeleteFunctionRequest{FunctionId: common.String(functionID)})
	if err != nil {
		if isOCIServiceNotFound(err) {
			return nil
		}
		return fmt.Errorf("delete OCI Function %s: %w", functionID, err)
	}
	return nil
}

func (o *OCI) resolveFunctionForDelete(ctx context.Context, target ManagedFunctionDeleteTarget) (FunctionDeletionState, error) {
	state := FunctionDeletionState{}
	switch {
	case strings.TrimSpace(target.ApplicationID) != "":
		state.ApplicationID = strings.TrimSpace(target.ApplicationID)
	case strings.TrimSpace(target.CompartmentID) == "":
		return state, fmt.Errorf("managed Function deletion requires spec.config.compartmentId when status.functionId is empty")
	case strings.TrimSpace(target.ApplicationName) == "":
		return state, fmt.Errorf("managed Function deletion requires spec.config.applicationName when status.functionId is empty")
	}
	if strings.TrimSpace(target.DisplayName) == "" {
		return state, fmt.Errorf("managed Function deletion requires spec.config.displayName when status.functionId is empty")
	}

	if state.ApplicationID == "" {
		applications, err := o.client.ListApplications(ctx, ocifunctions.ListApplicationsRequest{
			CompartmentId: common.String(strings.TrimSpace(target.CompartmentID)),
			DisplayName:   common.String(strings.TrimSpace(target.ApplicationName)),
			Limit:         common.Int(50),
		})
		if err != nil {
			return state, fmt.Errorf("list OCI Functions applications for managed Function deletion: %w", err)
		}

		applicationIDs := []string{}
		for _, application := range applications.Items {
			if stringValue(application.DisplayName) != strings.TrimSpace(target.ApplicationName) {
				continue
			}
			if application.LifecycleState == ocifunctions.ApplicationLifecycleStateDeleted || application.LifecycleState == ocifunctions.ApplicationLifecycleStateDeleting {
				continue
			}
			applicationID := strings.TrimSpace(stringValue(application.Id))
			if applicationID != "" {
				applicationIDs = append(applicationIDs, applicationID)
			}
		}
		switch len(applicationIDs) {
		case 0:
			return state, nil
		case 1:
			state.ApplicationID = applicationIDs[0]
		default:
			return state, fmt.Errorf("managed Function deletion cannot safely resolve application %q: multiple matching applications found", strings.TrimSpace(target.ApplicationName))
		}
	}

	functions, err := o.client.ListFunctions(ctx, ocifunctions.ListFunctionsRequest{
		ApplicationId: common.String(state.ApplicationID),
		DisplayName:   common.String(strings.TrimSpace(target.DisplayName)),
		Limit:         common.Int(50),
	})
	if err != nil {
		return state, fmt.Errorf("list OCI Functions for managed Function deletion in application %s: %w", state.ApplicationID, err)
	}

	functionIDs := []string{}
	for _, function := range functions.Items {
		if stringValue(function.DisplayName) != strings.TrimSpace(target.DisplayName) {
			continue
		}
		if function.LifecycleState == ocifunctions.FunctionLifecycleStateDeleted || function.LifecycleState == ocifunctions.FunctionLifecycleStateDeleting {
			continue
		}
		functionID := strings.TrimSpace(stringValue(function.Id))
		if functionID != "" {
			functionIDs = append(functionIDs, functionID)
		}
	}
	switch len(functionIDs) {
	case 0:
		return state, nil
	case 1:
		state.FunctionID = functionIDs[0]
		return state, nil
	default:
		return state, fmt.Errorf("managed Function deletion cannot safely resolve function %q in application %q: multiple matching functions found", strings.TrimSpace(target.DisplayName), strings.TrimSpace(target.ApplicationName))
	}
}

func (o *OCI) ensureApplication(ctx context.Context, desired DesiredApplication) (ocifunctions.Application, []Event, error) {
	if strings.TrimSpace(desired.ExistingApplicationID) != "" {
		application, err := o.getApplication(ctx, strings.TrimSpace(desired.ExistingApplicationID))
		if err != nil {
			return ocifunctions.Application{}, nil, err
		}
		if desired.Mode == ApplicationModeExisting {
			return application, nil, nil
		}
		return o.ensureApplicationMutableFields(ctx, desired, application)
	}

	response, err := o.client.ListApplications(ctx, ocifunctions.ListApplicationsRequest{
		CompartmentId: common.String(desired.CompartmentID),
		DisplayName:   common.String(desired.DisplayName),
		Limit:         common.Int(50),
	})
	if err != nil {
		return ocifunctions.Application{}, nil, fmt.Errorf("list OCI Functions applications: %w", err)
	}
	for _, item := range response.Items {
		if stringValue(item.DisplayName) != desired.DisplayName {
			continue
		}
		if item.LifecycleState == ocifunctions.ApplicationLifecycleStateDeleted || item.LifecycleState == ocifunctions.ApplicationLifecycleStateDeleting {
			continue
		}
		application, err := o.getApplication(ctx, stringValue(item.Id))
		if err != nil {
			return ocifunctions.Application{}, nil, err
		}
		if desired.Mode == ApplicationModeExisting {
			return application, nil, nil
		}
		return o.ensureApplicationMutableFields(ctx, desired, application)
	}
	if desired.Mode == ApplicationModeExisting {
		return ocifunctions.Application{}, nil, fmt.Errorf("resolve OCI Functions application %q: not found", desired.DisplayName)
	}

	created, err := o.client.CreateApplication(ctx, ocifunctions.CreateApplicationRequest{
		CreateApplicationDetails: ocifunctions.CreateApplicationDetails{
			CompartmentId:           common.String(desired.CompartmentID),
			DisplayName:             common.String(desired.DisplayName),
			SubnetIds:               copyStringSlice(desired.SubnetIDs),
			NetworkSecurityGroupIds: copyStringSlice(desired.ApplicationNSGIDs),
			Config:                  copyStringMap(desired.Config),
			Logging:                 applicationLoggingConfig(desired.Logging),
			FreeformTags:            copyStringMap(desired.FreeformTags),
		},
	})
	if err != nil {
		return ocifunctions.Application{}, nil, fmt.Errorf("create OCI Functions application %q: %w", desired.DisplayName, err)
	}

	events := []Event{}
	if len(desired.ApplicationNSGIDs) > 0 {
		events = append(events, Event{
			Type:    EventTypeNormal,
			Reason:  "ApplicationCreatedWithNSGs",
			Message: fmt.Sprintf("Created OCI Functions application %q with NSGs %s.", desired.DisplayName, formatStringList(desired.ApplicationNSGIDs)),
		})
	}
	if applicationInvocationLoggingEnabled(desired.Logging) {
		events = append(events, Event{
			Type:    EventTypeNormal,
			Reason:  "ApplicationCreatedWithInvocationLogs",
			Message: fmt.Sprintf("Created OCI Functions application %q with invocation logs enabled using %s line format.", desired.DisplayName, effectiveInvocationLogLineFormat(desired.Logging)),
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

func (o *OCI) ensureApplicationMutableFields(ctx context.Context, desired DesiredApplication, application ocifunctions.Application) (ocifunctions.Application, []Event, error) {
	if strings.TrimSpace(desired.DisplayName) != "" && stringValue(application.DisplayName) != desired.DisplayName {
		return application, nil, fmt.Errorf("OCI Functions application displayName is %q and cannot be updated to %q by the OCI Functions API", stringValue(application.DisplayName), desired.DisplayName)
	}
	if len(desired.SubnetIDs) > 0 && !sameStringSet(application.SubnetIds, desired.SubnetIDs) {
		return application, nil, fmt.Errorf("OCI Functions application %q subnetIds differ and cannot be updated by the OCI Functions API", desired.DisplayName)
	}
	needsUpdate := false
	nsgUpdated := false
	loggingUpdated := false
	updateDetails := ocifunctions.UpdateApplicationDetails{}
	if desired.ManageApplicationNSGIDs && !sameStringSet(application.NetworkSecurityGroupIds, desired.ApplicationNSGIDs) {
		updateDetails.NetworkSecurityGroupIds = copyStringSlice(desired.ApplicationNSGIDs)
		needsUpdate = true
		nsgUpdated = true
	}
	if desired.ManageApplicationConfiguration && !reflect.DeepEqual(nilToEmptyMap(application.Config), nilToEmptyMap(desired.Config)) {
		updateDetails.Config = copyStringMap(desired.Config)
		needsUpdate = true
	}
	if desired.ManageApplicationLogging && !sameApplicationLogging(application.Logging, desired.Logging) {
		if applicationInvocationLoggingEnabled(desired.Logging) {
			updateDetails.Logging = applicationLoggingConfig(desired.Logging)
			needsUpdate = true
			loggingUpdated = true
		}
	}
	if !needsUpdate {
		return application, nil, nil
	}

	applicationID := stringValue(application.Id)
	updated, err := o.client.UpdateApplication(ctx, ocifunctions.UpdateApplicationRequest{
		ApplicationId:            common.String(applicationID),
		UpdateApplicationDetails: updateDetails,
	})
	if err != nil {
		reason := "ApplicationUpdateFailed"
		message := fmt.Sprintf("Failed to update OCI Functions application %q configuration: %v", desired.DisplayName, err)
		errorMessage := fmt.Sprintf("update OCI Functions application %s configuration: %v", applicationID, err)
		if nsgUpdated {
			reason = "ApplicationNSGUpdateFailed"
			message = fmt.Sprintf("Failed to update OCI Functions application %q NSG configuration to %s: %v", desired.DisplayName, formatStringList(desired.ApplicationNSGIDs), err)
			errorMessage = fmt.Sprintf("update OCI Functions application %s NSG configuration: %v", applicationID, err)
		} else if loggingUpdated {
			reason = "ApplicationLoggingUpdateFailed"
			message = fmt.Sprintf("Failed to update OCI Functions application %q invocation log configuration: %v", desired.DisplayName, err)
			errorMessage = fmt.Sprintf("update OCI Functions application %s invocation log configuration: %v", applicationID, err)
		}
		event := Event{
			Type:    EventTypeWarning,
			Reason:  reason,
			Message: message,
		}
		return application, []Event{event}, fmt.Errorf("%s", errorMessage)
	}

	events := []Event{}
	if nsgUpdated {
		events = append(events, Event{
			Type:    EventTypeNormal,
			Reason:  "ApplicationNSGsUpdated",
			Message: fmt.Sprintf("Updated OCI Functions application %q NSG configuration to %s.", desired.DisplayName, formatStringList(desired.ApplicationNSGIDs)),
		})
	}
	if loggingUpdated {
		events = append(events, Event{
			Type:    EventTypeNormal,
			Reason:  "ApplicationInvocationLogsUpdated",
			Message: fmt.Sprintf("Updated OCI Functions application %q invocation logs to %s line format.", desired.DisplayName, effectiveInvocationLogLineFormat(desired.Logging)),
		})
	}
	return updated.Application, events, nil
}

func (o *OCI) ensureApplicationInvocationLog(ctx context.Context, desired DesiredApplication, applicationID, region string) ([]Event, error) {
	if o.loggingClient == nil {
		return nil, fmt.Errorf("OCI Logging management client is not configured")
	}
	logs := desired.Logging.InvocationLogs
	logGroupID := strings.TrimSpace(logs.LogGroupID)
	displayName := effectiveInvocationLogDisplayName(desired.DisplayName, logs)
	service := effectiveInvocationLogService(logs)
	category := effectiveInvocationLogCategory(logs)

	o.loggingClient.SetRegion(region)
	var matching []ocilogging.LogSummary
	var allLogs []ocilogging.LogSummary
	var page *string
	for {
		listResponse, err := o.loggingClient.ListLogs(ctx, ocilogging.ListLogsRequest{
			LogGroupId: common.String(logGroupID),
			Limit:      common.Int(100),
			Page:       page,
		})
		if err != nil {
			return nil, fmt.Errorf("list OCI Logging service logs in log group %s for Functions application %s: %w", logGroupID, applicationID, err)
		}
		for _, item := range listResponse.Items {
			allLogs = append(allLogs, item)
			if invocationLogSummaryMatches(item, logGroupID, applicationID, service, category) {
				matching = append(matching, item)
			}
		}
		if listResponse.OpcNextPage == nil || strings.TrimSpace(*listResponse.OpcNextPage) == "" {
			break
		}
		page = listResponse.OpcNextPage
	}
	if len(matching) > 1 {
		return nil, fmt.Errorf("multiple OCI Logging service logs found for Functions application %s in log group %s with service %q and category %q", applicationID, logGroupID, service, category)
	}
	if len(matching) == 0 {
		if conflict, ok := invocationLogDisplayNameConflict(allLogs, logGroupID, displayName, ""); ok {
			return nil, fmt.Errorf("OCI Logging service log displayName %q is already used in log group %s by log %s in lifecycle state %s with source %s", displayName, logGroupID, stringValue(conflict.Id), conflict.LifecycleState, invocationLogSourceDescription(conflict))
		}
		_, err := o.loggingClient.CreateLog(ctx, ocilogging.CreateLogRequest{
			LogGroupId: common.String(logGroupID),
			CreateLogDetails: ocilogging.CreateLogDetails{
				DisplayName: common.String(displayName),
				LogType:     ocilogging.CreateLogDetailsLogTypeService,
				IsEnabled:   common.Bool(logs.Enabled),
				Configuration: &ocilogging.Configuration{
					CompartmentId: common.String(strings.TrimSpace(desired.CompartmentID)),
					Source: ocilogging.OciService{
						Service:  common.String(service),
						Resource: common.String(applicationID),
						Category: common.String(category),
					},
				},
			},
		})
		if err != nil {
			if isOCIServiceConflict(err) {
				return nil, fmt.Errorf("create OCI Logging service log %q for Functions application %s in log group %s conflicted; a log with that displayName or service source may still exist or still be deleting: %w", displayName, applicationID, logGroupID, err)
			}
			return nil, fmt.Errorf("create OCI Logging service log for Functions application %s in log group %s: %w", applicationID, logGroupID, err)
		}
		return []Event{{
			Type:    EventTypeNormal,
			Reason:  "ApplicationInvocationLogCreated",
			Message: fmt.Sprintf("Created OCI Logging service log %q for Functions application %q in log group %s.", displayName, desired.DisplayName, logGroupID),
		}}, nil
	}

	log := matching[0]
	if !manageableInvocationLogState(log.LifecycleState) {
		message := fmt.Sprintf("OCI Logging service log %s for Functions application %s in log group %s is %s; wait for the log lifecycle to settle before reconciling invocation logs", stringValue(log.Id), applicationID, logGroupID, log.LifecycleState)
		if pendingInvocationLogState(log.LifecycleState) {
			return nil, pendingApplicationLogError{message: message}
		}
		return nil, fmt.Errorf("%s", message)
	}
	needsUpdate := false
	updateDetails := ocilogging.UpdateLogDetails{}
	if stringValue(log.DisplayName) != displayName {
		if conflict, ok := invocationLogDisplayNameConflict(allLogs, logGroupID, displayName, stringValue(log.Id)); ok {
			return nil, fmt.Errorf("OCI Logging service log displayName %q is already used in log group %s by log %s in lifecycle state %s with source %s", displayName, logGroupID, stringValue(conflict.Id), conflict.LifecycleState, invocationLogSourceDescription(conflict))
		}
		updateDetails.DisplayName = common.String(displayName)
		needsUpdate = true
	}
	if boolValue(log.IsEnabled) != logs.Enabled {
		updateDetails.IsEnabled = common.Bool(logs.Enabled)
		needsUpdate = true
	}
	if !needsUpdate {
		return nil, nil
	}
	_, err := o.loggingClient.UpdateLog(ctx, ocilogging.UpdateLogRequest{
		LogGroupId:       common.String(logGroupID),
		LogId:            common.String(stringValue(log.Id)),
		UpdateLogDetails: updateDetails,
	})
	if err != nil {
		return nil, fmt.Errorf("update OCI Logging service log %s for Functions application %s: %w", stringValue(log.Id), applicationID, err)
	}
	return []Event{{
		Type:    EventTypeNormal,
		Reason:  "ApplicationInvocationLogUpdated",
		Message: fmt.Sprintf("Updated OCI Logging service log %q for Functions application %q.", displayName, desired.DisplayName),
	}}, nil
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

func validateDesiredFunctionInApplication(desired DesiredFunctionInApplication) error {
	switch {
	case strings.TrimSpace(desired.Region) == "":
		return fmt.Errorf("managed Function with applicationRef requires referenced FunctionApplication status.region")
	case strings.TrimSpace(desired.ApplicationID) == "":
		return fmt.Errorf("managed Function with applicationRef requires referenced FunctionApplication status.applicationId")
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

func validateDesiredApplication(desired DesiredApplication) error {
	region := effectiveApplicationRegion(desired.Region, desired.ExistingApplicationID)
	switch {
	case strings.TrimSpace(region) == "":
		return fmt.Errorf("FunctionApplication requires spec.region unless spec.existingApplicationId contains a region")
	case desired.Mode == "":
		return fmt.Errorf("FunctionApplication requires mode")
	case desired.Mode != ApplicationModeManaged && desired.Mode != ApplicationModeExisting:
		return fmt.Errorf("FunctionApplication mode must be Managed or Existing")
	case strings.TrimSpace(desired.ExistingApplicationID) == "" && strings.TrimSpace(desired.CompartmentID) == "":
		return fmt.Errorf("FunctionApplication requires spec.compartmentId when spec.existingApplicationId is empty")
	case strings.TrimSpace(desired.ExistingApplicationID) == "" && strings.TrimSpace(desired.DisplayName) == "":
		return fmt.Errorf("FunctionApplication requires spec.displayName when spec.existingApplicationId is empty")
	case desired.Mode == ApplicationModeManaged && strings.TrimSpace(desired.ExistingApplicationID) == "" && len(desired.SubnetIDs) == 0:
		return fmt.Errorf("managed FunctionApplication requires spec.subnetIds")
	case desired.ManageApplicationNSGIDs && hasEmptyString(desired.ApplicationNSGIDs):
		return fmt.Errorf("FunctionApplication requires spec.nsgIds entries to be non-empty")
	case applicationInvocationLoggingEnabled(desired.Logging) && strings.TrimSpace(desired.Logging.InvocationLogs.LogGroupID) == "":
		return fmt.Errorf("FunctionApplication logging.invocationLogs.logGroupId is required when invocation logs are enabled")
	case applicationInvocationLoggingEnabled(desired.Logging) && strings.TrimSpace(effectiveInvocationLogService(desired.Logging.InvocationLogs)) == "":
		return fmt.Errorf("FunctionApplication logging.invocationLogs.service must be non-empty")
	case applicationInvocationLoggingEnabled(desired.Logging) && strings.TrimSpace(effectiveInvocationLogCategory(desired.Logging.InvocationLogs)) == "":
		return fmt.Errorf("FunctionApplication logging.invocationLogs.category must be non-empty")
	}
	return nil
}

func desiredApplicationFromFunction(desired DesiredFunction) DesiredApplication {
	return DesiredApplication{
		Mode:                           ApplicationModeManaged,
		Region:                         desired.Region,
		CompartmentID:                  desired.CompartmentID,
		DisplayName:                    desired.ApplicationName,
		SubnetIDs:                      desired.SubnetIDs,
		ApplicationNSGIDs:              desired.ApplicationNSGIDs,
		ManageApplicationNSGIDs:        desired.ManageApplicationNSGIDs,
		FreeformTags:                   copyStringMap(desired.FreeformTags),
		ManageApplicationConfiguration: false,
	}
}

func applicationLoggingConfig(logging *ApplicationLogging) *ocifunctions.ApplicationLoggingConfig {
	if !applicationInvocationLoggingEnabled(logging) {
		return nil
	}
	return &ocifunctions.ApplicationLoggingConfig{
		LineFormat: ocifunctions.ApplicationLoggingConfigLineFormatEnum(effectiveInvocationLogLineFormat(logging)),
	}
}

func applicationInvocationLoggingEnabled(logging *ApplicationLogging) bool {
	return logging != nil && logging.InvocationLogs != nil && logging.InvocationLogs.Enabled
}

func effectiveInvocationLogDisplayName(applicationDisplayName string, logs *ApplicationInvocationLogs) string {
	if logs != nil && strings.TrimSpace(logs.LogDisplayName) != "" {
		return strings.TrimSpace(logs.LogDisplayName)
	}
	if strings.TrimSpace(applicationDisplayName) == "" {
		return "function-application-invocation"
	}
	return strings.TrimSpace(applicationDisplayName) + "-invocation"
}

func effectiveInvocationLogService(logs *ApplicationInvocationLogs) string {
	if logs != nil && strings.TrimSpace(logs.Service) != "" {
		return strings.TrimSpace(logs.Service)
	}
	return defaultInvocationLogService
}

func effectiveInvocationLogCategory(logs *ApplicationInvocationLogs) string {
	if logs != nil && strings.TrimSpace(logs.Category) != "" {
		return strings.TrimSpace(logs.Category)
	}
	return defaultInvocationLogCategory
}

func effectiveInvocationLogLineFormat(logging *ApplicationLogging) string {
	if logging == nil || logging.InvocationLogs == nil || strings.TrimSpace(logging.InvocationLogs.LineFormat) == "" {
		return "JSON"
	}
	return strings.TrimSpace(logging.InvocationLogs.LineFormat)
}

func sameApplicationLogging(actual *ocifunctions.ApplicationLoggingConfig, desired *ApplicationLogging) bool {
	if !applicationInvocationLoggingEnabled(desired) {
		return true
	}
	if actual == nil {
		return false
	}
	return string(actual.LineFormat) == effectiveInvocationLogLineFormat(desired)
}

func invocationLogSummaryMatches(log ocilogging.LogSummary, logGroupID, applicationID, service, category string) bool {
	if stringValue(log.LogGroupId) != logGroupID || log.LogType != ocilogging.LogSummaryLogTypeService {
		return false
	}
	if log.Configuration == nil {
		return false
	}
	source, ok := log.Configuration.Source.(ocilogging.OciService)
	if !ok {
		return false
	}
	return stringValue(source.Service) == service &&
		stringValue(source.Resource) == applicationID &&
		stringValue(source.Category) == category
}

func invocationLogDisplayNameConflict(logs []ocilogging.LogSummary, logGroupID, displayName, allowedLogID string) (ocilogging.LogSummary, bool) {
	for _, log := range logs {
		if stringValue(log.LogGroupId) == logGroupID &&
			stringValue(log.DisplayName) == displayName &&
			stringValue(log.Id) != allowedLogID {
			return log, true
		}
	}
	return ocilogging.LogSummary{}, false
}

func manageableInvocationLogState(state ocilogging.LogLifecycleStateEnum) bool {
	return state == "" ||
		state == ocilogging.LogLifecycleStateActive ||
		state == ocilogging.LogLifecycleStateInactive
}

func pendingInvocationLogState(state ocilogging.LogLifecycleStateEnum) bool {
	return state == ocilogging.LogLifecycleStateCreating ||
		state == ocilogging.LogLifecycleStateUpdating ||
		state == ocilogging.LogLifecycleStateDeleting
}

func invocationLogSourceDescription(log ocilogging.LogSummary) string {
	if log.Configuration == nil {
		return "<unknown>"
	}
	source, ok := log.Configuration.Source.(ocilogging.OciService)
	if !ok {
		return fmt.Sprintf("%T", log.Configuration.Source)
	}
	return fmt.Sprintf("%s/%s/%s", stringValue(source.Service), stringValue(source.Resource), stringValue(source.Category))
}

func effectiveApplicationRegion(region, applicationID string) string {
	if strings.TrimSpace(region) != "" {
		return strings.TrimSpace(region)
	}
	parts := strings.Split(strings.TrimSpace(applicationID), ".")
	if len(parts) >= 5 && parts[0] == "ocid1" && parts[1] == "fnapp" {
		return parts[3]
	}
	return ""
}

func effectiveFunctionRegion(region, functionID string) string {
	if strings.TrimSpace(region) != "" {
		return strings.TrimSpace(region)
	}
	parts := strings.Split(strings.TrimSpace(functionID), ".")
	if len(parts) >= 5 && parts[0] == "ocid1" && parts[1] == "fnfunc" {
		return parts[3]
	}
	return ""
}

func isOCIServiceNotFound(err error) bool {
	serviceErr, ok := common.IsServiceError(err)
	return ok && serviceErr.GetHTTPStatusCode() == 404
}

func isOCIServiceConflict(err error) bool {
	serviceErr, ok := common.IsServiceError(err)
	return ok && serviceErr.GetHTTPStatusCode() == 409
}

type pendingApplicationLogError struct {
	message string
}

func (e pendingApplicationLogError) Error() string {
	return e.message
}

func pendingApplicationLogMessage(err error) (string, bool) {
	pendingErr, ok := err.(pendingApplicationLogError)
	if !ok {
		return "", false
	}
	return pendingErr.message, true
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

func boolValue(value *bool) bool {
	return value != nil && *value
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
