// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package lifecycle

import (
	"context"
	"errors"
	"reflect"
	"strings"
	"testing"

	"github.com/oracle/oci-go-sdk/v65/common"
	ocifunctions "github.com/oracle/oci-go-sdk/v65/functions"
	ocilogging "github.com/oracle/oci-go-sdk/v65/logging"
)

func TestEnsureFunctionCreatesApplicationAndFunctionInJeddah(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{}

	manager, err := NewOCI(OCIOptions{
		ConfigProvider: common.NewRawConfigurationProvider("tenancy", "user", "me-jeddah-1", "fingerprint", "private-key", nil),
		ClientFactory: func(common.ConfigurationProvider) (functionsManagementClient, error) {
			return fakeClient, nil
		},
		LoggingClientFactory: func(common.ConfigurationProvider) (loggingManagementClient, error) {
			return fakeClient, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}

	desired := DesiredFunction{
		Region:                  "me-jeddah-1",
		CompartmentID:           "ocid1.compartment.oc1..exampleuniqueid",
		ApplicationName:         "demo-app",
		SubnetIDs:               []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		ApplicationNSGIDs:       []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.exampleuniqueid"},
		ManageApplicationNSGIDs: true,
		DisplayName:             "hello",
		Image:                   "me-jeddah-1.ocir.io/example/functions/hello:latest",
		MemoryInMBs:             256,
		TimeoutInSeconds:        60,
		Config:                  map[string]string{"GREETING": "hello"},
		FreeformTags:            map[string]string{"managed-by": "oci-functions-operator"},
	}

	state, err := manager.EnsureFunction(ctx, desired)
	if err != nil {
		t.Fatalf("EnsureFunction returned error: %v", err)
	}
	if fakeClient.region != "me-jeddah-1" {
		t.Fatalf("region = %q, want me-jeddah-1", fakeClient.region)
	}
	if !state.Ready {
		t.Fatalf("state.Ready = false, want true")
	}
	if state.ApplicationID != fakeApplicationID || state.FunctionID != fakeFunctionID || state.InvokeEndpoint != fakeInvokeEndpoint {
		t.Fatalf("state = %#v, want created application/function IDs and endpoint", state)
	}
	if fakeClient.createdApplication.CompartmentId == nil || *fakeClient.createdApplication.CompartmentId != desired.CompartmentID {
		t.Fatalf("created application compartment = %#v, want %q", fakeClient.createdApplication.CompartmentId, desired.CompartmentID)
	}
	if !reflect.DeepEqual(fakeClient.createdApplication.SubnetIds, desired.SubnetIDs) {
		t.Fatalf("created application subnets = %#v, want %#v", fakeClient.createdApplication.SubnetIds, desired.SubnetIDs)
	}
	if !reflect.DeepEqual(fakeClient.createdApplication.NetworkSecurityGroupIds, desired.ApplicationNSGIDs) {
		t.Fatalf("created application NSGs = %#v, want %#v", fakeClient.createdApplication.NetworkSecurityGroupIds, desired.ApplicationNSGIDs)
	}
	if !hasLifecycleEvent(state.Events, EventTypeNormal, "ApplicationCreatedWithNSGs") {
		t.Fatalf("events = %#v, want ApplicationCreatedWithNSGs normal event", state.Events)
	}
	if fakeClient.createdFunction.ApplicationId == nil || *fakeClient.createdFunction.ApplicationId != fakeApplicationID {
		t.Fatalf("created function application ID = %#v, want %q", fakeClient.createdFunction.ApplicationId, fakeApplicationID)
	}
	if fakeClient.createdFunction.MemoryInMBs == nil || *fakeClient.createdFunction.MemoryInMBs != desired.MemoryInMBs {
		t.Fatalf("created function memory = %#v, want %d", fakeClient.createdFunction.MemoryInMBs, desired.MemoryInMBs)
	}
	if fakeClient.createdFunction.TimeoutInSeconds == nil || *fakeClient.createdFunction.TimeoutInSeconds != desired.TimeoutInSeconds {
		t.Fatalf("created function timeout = %#v, want %d", fakeClient.createdFunction.TimeoutInSeconds, desired.TimeoutInSeconds)
	}
	if !reflect.DeepEqual(fakeClient.createdFunction.Config, desired.Config) {
		t.Fatalf("created function config = %#v, want %#v", fakeClient.createdFunction.Config, desired.Config)
	}
}

func TestEnsureFunctionUpdatesApplicationNSGsWhenChanged(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		applications: []ocifunctions.ApplicationSummary{{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		}},
		application: ocifunctions.Application{
			Id:                      common.String(fakeApplicationID),
			DisplayName:             common.String("demo-app"),
			LifecycleState:          ocifunctions.ApplicationLifecycleStateActive,
			SubnetIds:               []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
			NetworkSecurityGroupIds: []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.old"},
		},
	}

	manager, err := NewOCI(OCIOptions{
		ConfigProvider: common.NewRawConfigurationProvider("tenancy", "user", "me-jeddah-1", "fingerprint", "private-key", nil),
		ClientFactory: func(common.ConfigurationProvider) (functionsManagementClient, error) {
			return fakeClient, nil
		},
		LoggingClientFactory: func(common.ConfigurationProvider) (loggingManagementClient, error) {
			return fakeClient, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}

	desired := validDesiredFunction()
	desired.ApplicationNSGIDs = []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.new"}
	desired.ManageApplicationNSGIDs = true

	state, err := manager.EnsureFunction(ctx, desired)
	if err != nil {
		t.Fatalf("EnsureFunction returned error: %v", err)
	}
	if !reflect.DeepEqual(fakeClient.updatedApplication.NetworkSecurityGroupIds, desired.ApplicationNSGIDs) {
		t.Fatalf("updated application NSGs = %#v, want %#v", fakeClient.updatedApplication.NetworkSecurityGroupIds, desired.ApplicationNSGIDs)
	}
	if fakeClient.updatedApplicationID != fakeApplicationID {
		t.Fatalf("updated application ID = %q, want %q", fakeClient.updatedApplicationID, fakeApplicationID)
	}
	if !hasLifecycleEvent(state.Events, EventTypeNormal, "ApplicationNSGsUpdated") {
		t.Fatalf("events = %#v, want ApplicationNSGsUpdated normal event", state.Events)
	}
}

func TestEnsureFunctionReturnsApplicationNSGUpdateFailure(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		applications: []ocifunctions.ApplicationSummary{{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		}},
		application: ocifunctions.Application{
			Id:                      common.String(fakeApplicationID),
			DisplayName:             common.String("demo-app"),
			LifecycleState:          ocifunctions.ApplicationLifecycleStateActive,
			SubnetIds:               []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
			NetworkSecurityGroupIds: []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.old"},
		},
		updateApplicationErr: errors.New("not authorized to update NSGs"),
	}

	manager, err := NewOCI(OCIOptions{
		ConfigProvider: common.NewRawConfigurationProvider("tenancy", "user", "me-jeddah-1", "fingerprint", "private-key", nil),
		ClientFactory: func(common.ConfigurationProvider) (functionsManagementClient, error) {
			return fakeClient, nil
		},
		LoggingClientFactory: func(common.ConfigurationProvider) (loggingManagementClient, error) {
			return fakeClient, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}

	desired := validDesiredFunction()
	desired.ApplicationNSGIDs = []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.new"}
	desired.ManageApplicationNSGIDs = true

	state, err := manager.EnsureFunction(ctx, desired)
	if err == nil {
		t.Fatalf("EnsureFunction returned nil error, want NSG update failure")
	}
	if !strings.Contains(err.Error(), "update OCI Functions application") || !strings.Contains(err.Error(), "NSG configuration") {
		t.Fatalf("error = %q, want NSG update context", err)
	}
	if state.ApplicationID != fakeApplicationID {
		t.Fatalf("state application ID = %q, want %q", state.ApplicationID, fakeApplicationID)
	}
	if !hasLifecycleEvent(state.Events, EventTypeWarning, "ApplicationNSGUpdateFailed") {
		t.Fatalf("events = %#v, want ApplicationNSGUpdateFailed warning event", state.Events)
	}
}

func TestEnsureApplicationCreatesManagedApplication(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.EnsureApplication(ctx, DesiredApplication{
		Mode:                    ApplicationModeManaged,
		Region:                  "me-jeddah-1",
		CompartmentID:           "ocid1.compartment.oc1..exampleuniqueid",
		DisplayName:             "demo-app",
		SubnetIDs:               []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		ApplicationNSGIDs:       []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.exampleuniqueid"},
		ManageApplicationNSGIDs: true,
		Config:                  map[string]string{"APP_LEVEL": "true"},
		Logging: &ApplicationLogging{InvocationLogs: &ApplicationInvocationLogs{
			Enabled:    true,
			LogGroupID: "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid",
			LineFormat: "JSON",
		}},
		ManageApplicationLogging: true,
	})
	if err != nil {
		t.Fatalf("EnsureApplication returned error: %v", err)
	}
	if fakeClient.region != "me-jeddah-1" {
		t.Fatalf("region = %q, want me-jeddah-1", fakeClient.region)
	}
	if state.ApplicationID != fakeApplicationID || !state.Ready {
		t.Fatalf("state = %#v, want ready app ID", state)
	}
	if fakeClient.createdApplication.DisplayName == nil || *fakeClient.createdApplication.DisplayName != "demo-app" {
		t.Fatalf("created displayName = %#v, want demo-app", fakeClient.createdApplication.DisplayName)
	}
	if !reflect.DeepEqual(fakeClient.createdApplication.Config, map[string]string{"APP_LEVEL": "true"}) {
		t.Fatalf("created config = %#v, want app config", fakeClient.createdApplication.Config)
	}
	if fakeClient.createdApplication.Logging == nil || fakeClient.createdApplication.Logging.LineFormat != ocifunctions.ApplicationLoggingConfigLineFormatJson {
		t.Fatalf("created logging = %#v, want JSON invocation logging", fakeClient.createdApplication.Logging)
	}
	if !hasLifecycleEvent(state.Events, EventTypeNormal, "ApplicationCreatedWithInvocationLogs") {
		t.Fatalf("events = %#v, want ApplicationCreatedWithInvocationLogs normal event", state.Events)
	}
	if len(fakeClient.listLogsRequests) != 1 {
		t.Fatalf("ListLogs called %d times, want 1", len(fakeClient.listLogsRequests))
	}
	listLogsRequest := fakeClient.listLogsRequests[0]
	if stringValue(listLogsRequest.LogGroupId) != "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid" {
		t.Fatalf("ListLogs log group ID = %q, want desired log group", stringValue(listLogsRequest.LogGroupId))
	}
	if listLogsRequest.SourceService != nil || listLogsRequest.SourceResource != nil {
		t.Fatalf("ListLogs source filters = service %#v resource %#v, want nil filters", listLogsRequest.SourceService, listLogsRequest.SourceResource)
	}
	if fakeClient.createdLogGroupID != "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid" {
		t.Fatalf("created log group ID = %q, want log group from desired logging", fakeClient.createdLogGroupID)
	}
	if fakeClient.createdLog.LogType != ocilogging.CreateLogDetailsLogTypeService {
		t.Fatalf("created log type = %q, want SERVICE", fakeClient.createdLog.LogType)
	}
	source, ok := fakeClient.createdLog.Configuration.Source.(ocilogging.OciService)
	if !ok {
		t.Fatalf("created log source = %#v, want OciService", fakeClient.createdLog.Configuration.Source)
	}
	if stringValue(source.Service) != defaultInvocationLogService ||
		stringValue(source.Resource) != fakeApplicationID ||
		stringValue(source.Category) != defaultInvocationLogCategory {
		t.Fatalf("created log source = %#v, want functions/%s/%s", source, fakeApplicationID, defaultInvocationLogCategory)
	}
}

func TestEnsureApplicationUpdatesMutableFields(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		applications: []ocifunctions.ApplicationSummary{{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		}},
		application: ocifunctions.Application{
			Id:                      common.String(fakeApplicationID),
			DisplayName:             common.String("demo-app"),
			LifecycleState:          ocifunctions.ApplicationLifecycleStateActive,
			SubnetIds:               []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
			NetworkSecurityGroupIds: []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.old"},
			Config:                  map[string]string{"OLD": "true"},
			Logging:                 &ocifunctions.ApplicationLoggingConfig{LineFormat: ocifunctions.ApplicationLoggingConfigLineFormatPlainText},
		},
		logs: []ocilogging.LogSummary{{
			Id:             common.String("ocid1.log.oc1.me-jeddah-1.exampleuniqueid"),
			LogGroupId:     common.String("ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid"),
			DisplayName:    common.String("old-functions-log"),
			LogType:        ocilogging.LogSummaryLogTypeService,
			LifecycleState: ocilogging.LogLifecycleStateActive,
			IsEnabled:      common.Bool(false),
			Configuration: &ocilogging.Configuration{
				Source: ocilogging.OciService{
					Service:  common.String(defaultInvocationLogService),
					Resource: common.String(fakeApplicationID),
					Category: common.String(defaultInvocationLogCategory),
				},
			},
		}},
	}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.EnsureApplication(ctx, DesiredApplication{
		Mode:                           ApplicationModeManaged,
		Region:                         "me-jeddah-1",
		CompartmentID:                  "ocid1.compartment.oc1..exampleuniqueid",
		DisplayName:                    "demo-app",
		SubnetIDs:                      []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		ApplicationNSGIDs:              []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.new"},
		ManageApplicationNSGIDs:        true,
		Config:                         map[string]string{"NEW": "true"},
		ManageApplicationConfiguration: true,
		Logging: &ApplicationLogging{InvocationLogs: &ApplicationInvocationLogs{
			Enabled:        true,
			LogGroupID:     "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid",
			LogDisplayName: "demo-app-invocation",
			LineFormat:     "JSON",
		}},
		ManageApplicationLogging: true,
	})
	if err != nil {
		t.Fatalf("EnsureApplication returned error: %v", err)
	}
	if state.ApplicationID != fakeApplicationID {
		t.Fatalf("state application ID = %q, want %q", state.ApplicationID, fakeApplicationID)
	}
	if !reflect.DeepEqual(fakeClient.updatedApplication.NetworkSecurityGroupIds, []string{"ocid1.networksecuritygroup.oc1.me-jeddah-1.new"}) {
		t.Fatalf("updated NSGs = %#v, want new NSG", fakeClient.updatedApplication.NetworkSecurityGroupIds)
	}
	if !reflect.DeepEqual(fakeClient.updatedApplication.Config, map[string]string{"NEW": "true"}) {
		t.Fatalf("updated config = %#v, want new config", fakeClient.updatedApplication.Config)
	}
	if fakeClient.updatedApplication.Logging == nil || fakeClient.updatedApplication.Logging.LineFormat != ocifunctions.ApplicationLoggingConfigLineFormatJson {
		t.Fatalf("updated logging = %#v, want JSON invocation logging", fakeClient.updatedApplication.Logging)
	}
	if !hasLifecycleEvent(state.Events, EventTypeNormal, "ApplicationInvocationLogsUpdated") {
		t.Fatalf("events = %#v, want ApplicationInvocationLogsUpdated", state.Events)
	}
	if fakeClient.updatedLogID != "ocid1.log.oc1.me-jeddah-1.exampleuniqueid" {
		t.Fatalf("updated log ID = %q, want existing service log", fakeClient.updatedLogID)
	}
	if fakeClient.updatedLog.IsEnabled == nil || !*fakeClient.updatedLog.IsEnabled {
		t.Fatalf("updated log enabled = %#v, want true", fakeClient.updatedLog.IsEnabled)
	}
	if fakeClient.updatedLog.DisplayName == nil || *fakeClient.updatedLog.DisplayName != "demo-app-invocation" {
		t.Fatalf("updated log displayName = %#v, want demo-app-invocation", fakeClient.updatedLog.DisplayName)
	}
}

func TestEnsureApplicationAdoptsInactiveInvocationLog(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		applications: []ocifunctions.ApplicationSummary{{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		}},
		application: ocifunctions.Application{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
			SubnetIds:      []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
			Logging:        &ocifunctions.ApplicationLoggingConfig{LineFormat: ocifunctions.ApplicationLoggingConfigLineFormatJson},
		},
		logs: []ocilogging.LogSummary{{
			Id:             common.String("ocid1.log.oc1.me-jeddah-1.inactive"),
			LogGroupId:     common.String("ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid"),
			DisplayName:    common.String("old-functions-log"),
			LogType:        ocilogging.LogSummaryLogTypeService,
			LifecycleState: ocilogging.LogLifecycleStateInactive,
			IsEnabled:      common.Bool(false),
			Configuration: &ocilogging.Configuration{
				Source: ocilogging.OciService{
					Service:  common.String(defaultInvocationLogService),
					Resource: common.String(fakeApplicationID),
					Category: common.String(defaultInvocationLogCategory),
				},
			},
		}},
		createLogErr: fakeServiceError{status: 409, code: "Conflict", message: "logDisplayName already exists"},
	}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.EnsureApplication(ctx, DesiredApplication{
		Mode:          ApplicationModeManaged,
		Region:        "me-jeddah-1",
		CompartmentID: "ocid1.compartment.oc1..exampleuniqueid",
		DisplayName:   "demo-app",
		SubnetIDs:     []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		Logging: &ApplicationLogging{InvocationLogs: &ApplicationInvocationLogs{
			Enabled:        true,
			LogGroupID:     "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid",
			LogDisplayName: "demo-app-invocation",
			LineFormat:     "JSON",
		}},
		ManageApplicationLogging: true,
	})
	if err != nil {
		t.Fatalf("EnsureApplication returned error: %v", err)
	}
	if !state.Ready {
		t.Fatalf("state.Ready = false, want true")
	}
	if len(fakeClient.listLogsRequests) != 1 {
		t.Fatalf("ListLogs called %d times, want 1", len(fakeClient.listLogsRequests))
	}
	if fakeClient.listLogsRequests[0].LifecycleState != "" {
		t.Fatalf("ListLogs lifecycle filter = %q, want all lifecycle states", fakeClient.listLogsRequests[0].LifecycleState)
	}
	if fakeClient.createdLogGroupID != "" {
		t.Fatalf("createdLogGroupID = %q, want no create for existing inactive source log", fakeClient.createdLogGroupID)
	}
	if fakeClient.updatedLogID != "ocid1.log.oc1.me-jeddah-1.inactive" {
		t.Fatalf("updatedLogID = %q, want existing inactive service log", fakeClient.updatedLogID)
	}
	if fakeClient.updatedLog.DisplayName == nil || *fakeClient.updatedLog.DisplayName != "demo-app-invocation" {
		t.Fatalf("updated displayName = %#v, want demo-app-invocation", fakeClient.updatedLog.DisplayName)
	}
	if fakeClient.updatedLog.IsEnabled == nil || !*fakeClient.updatedLog.IsEnabled {
		t.Fatalf("updated isEnabled = %#v, want true", fakeClient.updatedLog.IsEnabled)
	}
}

func TestEnsureApplicationWaitsForCreatingInvocationLog(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		applications: []ocifunctions.ApplicationSummary{{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		}},
		application: ocifunctions.Application{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
			SubnetIds:      []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
			Logging:        &ocifunctions.ApplicationLoggingConfig{LineFormat: ocifunctions.ApplicationLoggingConfigLineFormatJson},
		},
		logs: []ocilogging.LogSummary{{
			Id:             common.String("ocid1.log.oc1.me-jeddah-1.creating"),
			LogGroupId:     common.String("ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid"),
			DisplayName:    common.String("demo-app-invocation"),
			LogType:        ocilogging.LogSummaryLogTypeService,
			LifecycleState: ocilogging.LogLifecycleStateCreating,
			IsEnabled:      common.Bool(true),
			Configuration: &ocilogging.Configuration{
				Source: ocilogging.OciService{
					Service:  common.String(defaultInvocationLogService),
					Resource: common.String(fakeApplicationID),
					Category: common.String(defaultInvocationLogCategory),
				},
			},
		}},
	}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.EnsureApplication(ctx, DesiredApplication{
		Mode:          ApplicationModeManaged,
		Region:        "me-jeddah-1",
		CompartmentID: "ocid1.compartment.oc1..exampleuniqueid",
		DisplayName:   "demo-app",
		SubnetIDs:     []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		Logging: &ApplicationLogging{InvocationLogs: &ApplicationInvocationLogs{
			Enabled:        true,
			LogGroupID:     "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid",
			LogDisplayName: "demo-app-invocation",
			LineFormat:     "JSON",
		}},
		ManageApplicationLogging: true,
	})
	if err != nil {
		t.Fatalf("EnsureApplication returned error: %v", err)
	}
	if state.Ready {
		t.Fatalf("state.Ready = true, want pending while invocation log is creating")
	}
	if !strings.Contains(state.Message, "CREATING") || !strings.Contains(state.Message, "ocid1.log.oc1.me-jeddah-1.creating") {
		t.Fatalf("state.Message = %q, want creating log guidance", state.Message)
	}
	if fakeClient.createdLogGroupID != "" {
		t.Fatalf("createdLogGroupID = %q, want no create for existing creating source log", fakeClient.createdLogGroupID)
	}
	if fakeClient.updatedLogID != "" {
		t.Fatalf("updatedLogID = %q, want no update while source log is creating", fakeClient.updatedLogID)
	}
}

func TestEnsureApplicationReportsInvocationLogDisplayNameConflict(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		applications: []ocifunctions.ApplicationSummary{{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		}},
		application: ocifunctions.Application{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
			SubnetIds:      []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
			Logging:        &ocifunctions.ApplicationLoggingConfig{LineFormat: ocifunctions.ApplicationLoggingConfigLineFormatJson},
		},
		logs: []ocilogging.LogSummary{{
			Id:             common.String("ocid1.log.oc1.me-jeddah-1.other"),
			LogGroupId:     common.String("ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid"),
			DisplayName:    common.String("demo-app-invocation"),
			LogType:        ocilogging.LogSummaryLogTypeService,
			LifecycleState: ocilogging.LogLifecycleStateActive,
			IsEnabled:      common.Bool(true),
			Configuration: &ocilogging.Configuration{
				Source: ocilogging.OciService{
					Service:  common.String(defaultInvocationLogService),
					Resource: common.String("ocid1.fnapp.oc1.me-jeddah-1.other"),
					Category: common.String(defaultInvocationLogCategory),
				},
			},
		}},
		createLogErr: fakeServiceError{status: 409, code: "Conflict", message: "logDisplayName already exists"},
	}
	manager := newTestOCIManager(t, fakeClient)

	_, err := manager.EnsureApplication(ctx, DesiredApplication{
		Mode:          ApplicationModeManaged,
		Region:        "me-jeddah-1",
		CompartmentID: "ocid1.compartment.oc1..exampleuniqueid",
		DisplayName:   "demo-app",
		SubnetIDs:     []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		Logging: &ApplicationLogging{InvocationLogs: &ApplicationInvocationLogs{
			Enabled:        true,
			LogGroupID:     "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid",
			LogDisplayName: "demo-app-invocation",
			LineFormat:     "JSON",
		}},
		ManageApplicationLogging: true,
	})
	if err == nil || !strings.Contains(err.Error(), "displayName") || !strings.Contains(err.Error(), "ocid1.log.oc1.me-jeddah-1.other") {
		t.Fatalf("EnsureApplication error = %v, want displayName conflict with existing log OCID", err)
	}
	if fakeClient.createdLogGroupID != "" {
		t.Fatalf("createdLogGroupID = %q, want no create when displayName is already owned", fakeClient.createdLogGroupID)
	}
	if fakeClient.updatedLogID != "" {
		t.Fatalf("updatedLogID = %q, want no update for different-source displayName conflict", fakeClient.updatedLogID)
	}
}

func TestEnsureApplicationReportsInvocationLogRenameConflict(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		applications: []ocifunctions.ApplicationSummary{{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		}},
		application: ocifunctions.Application{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
			SubnetIds:      []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
			Logging:        &ocifunctions.ApplicationLoggingConfig{LineFormat: ocifunctions.ApplicationLoggingConfigLineFormatJson},
		},
		logs: []ocilogging.LogSummary{
			{
				Id:             common.String("ocid1.log.oc1.me-jeddah-1.source"),
				LogGroupId:     common.String("ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid"),
				DisplayName:    common.String("old-functions-log"),
				LogType:        ocilogging.LogSummaryLogTypeService,
				LifecycleState: ocilogging.LogLifecycleStateActive,
				IsEnabled:      common.Bool(true),
				Configuration: &ocilogging.Configuration{
					Source: ocilogging.OciService{
						Service:  common.String(defaultInvocationLogService),
						Resource: common.String(fakeApplicationID),
						Category: common.String(defaultInvocationLogCategory),
					},
				},
			},
			{
				Id:             common.String("ocid1.log.oc1.me-jeddah-1.custom"),
				LogGroupId:     common.String("ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid"),
				DisplayName:    common.String("demo-app-invocation"),
				LogType:        ocilogging.LogSummaryLogTypeCustom,
				LifecycleState: ocilogging.LogLifecycleStateActive,
				IsEnabled:      common.Bool(true),
			},
		},
		updateLogErr: fakeServiceError{status: 409, code: "Conflict", message: "logDisplayName already exists"},
	}
	manager := newTestOCIManager(t, fakeClient)

	_, err := manager.EnsureApplication(ctx, DesiredApplication{
		Mode:          ApplicationModeManaged,
		Region:        "me-jeddah-1",
		CompartmentID: "ocid1.compartment.oc1..exampleuniqueid",
		DisplayName:   "demo-app",
		SubnetIDs:     []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		Logging: &ApplicationLogging{InvocationLogs: &ApplicationInvocationLogs{
			Enabled:        true,
			LogGroupID:     "ocid1.loggroup.oc1.me-jeddah-1.exampleuniqueid",
			LogDisplayName: "demo-app-invocation",
			LineFormat:     "JSON",
		}},
		ManageApplicationLogging: true,
	})
	if err == nil || !strings.Contains(err.Error(), "displayName") || !strings.Contains(err.Error(), "ocid1.log.oc1.me-jeddah-1.custom") {
		t.Fatalf("EnsureApplication error = %v, want rename displayName conflict with custom log OCID", err)
	}
	if fakeClient.updatedLogID != "" {
		t.Fatalf("updatedLogID = %q, want no update when displayName is already owned", fakeClient.updatedLogID)
	}
	if fakeClient.createdLogGroupID != "" {
		t.Fatalf("createdLogGroupID = %q, want no create for existing source log", fakeClient.createdLogGroupID)
	}
}

func TestEnsureApplicationRequiresLogGroupForInvocationLogs(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{}
	manager := newTestOCIManager(t, fakeClient)

	_, err := manager.EnsureApplication(ctx, DesiredApplication{
		Mode:          ApplicationModeManaged,
		Region:        "me-jeddah-1",
		CompartmentID: "ocid1.compartment.oc1..exampleuniqueid",
		DisplayName:   "demo-app",
		SubnetIDs:     []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		Logging: &ApplicationLogging{InvocationLogs: &ApplicationInvocationLogs{
			Enabled:    true,
			LineFormat: "JSON",
		}},
		ManageApplicationLogging: true,
	})
	if err == nil || !strings.Contains(err.Error(), "logGroupId is required") {
		t.Fatalf("EnsureApplication error = %v, want missing logGroupId error", err)
	}
}

func TestDeleteApplicationDeletesOnlyWhenEmpty(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.DeleteApplication(ctx, ApplicationDeleteTarget{
		Region:        "me-jeddah-1",
		ApplicationID: fakeApplicationID,
	})
	if err != nil {
		t.Fatalf("DeleteApplication returned error: %v", err)
	}
	if fakeClient.deletedApplicationID != fakeApplicationID {
		t.Fatalf("deletedApplicationID = %q, want %q", fakeClient.deletedApplicationID, fakeApplicationID)
	}
	if !state.Deleted {
		t.Fatalf("state.Deleted = false, want true")
	}
}

func TestDeleteApplicationBlocksWhenFunctionsRemain(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		functions: []ocifunctions.FunctionSummary{{
			Id:             common.String(fakeFunctionID),
			DisplayName:    common.String("hello"),
			LifecycleState: ocifunctions.FunctionLifecycleStateActive,
		}},
	}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.DeleteApplication(ctx, ApplicationDeleteTarget{
		Region:        "me-jeddah-1",
		ApplicationID: fakeApplicationID,
	})
	if err != nil {
		t.Fatalf("DeleteApplication returned error: %v", err)
	}
	if fakeClient.deletedApplicationID != "" {
		t.Fatalf("deletedApplicationID = %q, want empty when functions remain", fakeClient.deletedApplicationID)
	}
	if !state.Blocked || state.Deleted {
		t.Fatalf("state = %#v, want blocked and not deleted", state)
	}
	if !hasLifecycleEvent(state.Events, EventTypeWarning, "ApplicationDeleteBlocked") {
		t.Fatalf("events = %#v, want ApplicationDeleteBlocked", state.Events)
	}
}

func TestDeleteManagedFunctionDeletesFunctionByID(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.DeleteManagedFunction(ctx, ManagedFunctionDeleteTarget{
		Region:     "me-jeddah-1",
		FunctionID: fakeFunctionID,
	})
	if err != nil {
		t.Fatalf("DeleteManagedFunction returned error: %v", err)
	}
	if fakeClient.region != "me-jeddah-1" {
		t.Fatalf("region = %q, want me-jeddah-1", fakeClient.region)
	}
	if fakeClient.deletedFunctionID != fakeFunctionID {
		t.Fatalf("deletedFunctionID = %q, want %q", fakeClient.deletedFunctionID, fakeFunctionID)
	}
	if !state.Deleted || state.FunctionID != fakeFunctionID {
		t.Fatalf("state = %#v, want deleted function ID", state)
	}
	if !hasLifecycleEvent(state.Events, EventTypeNormal, "ManagedFunctionDeleted") {
		t.Fatalf("events = %#v, want ManagedFunctionDeleted", state.Events)
	}
}

func TestDeleteManagedFunctionResolvesFunctionWhenStatusFunctionIDMissing(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		applications: []ocifunctions.ApplicationSummary{{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		}},
		functions: []ocifunctions.FunctionSummary{{
			Id:             common.String(fakeFunctionID),
			DisplayName:    common.String("hello"),
			LifecycleState: ocifunctions.FunctionLifecycleStateActive,
		}},
	}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.DeleteManagedFunction(ctx, ManagedFunctionDeleteTarget{
		Region:          "me-jeddah-1",
		CompartmentID:   "ocid1.compartment.oc1..exampleuniqueid",
		ApplicationName: "demo-app",
		DisplayName:     "hello",
	})
	if err != nil {
		t.Fatalf("DeleteManagedFunction returned error: %v", err)
	}
	if fakeClient.deletedFunctionID != fakeFunctionID {
		t.Fatalf("deletedFunctionID = %q, want resolved %q", fakeClient.deletedFunctionID, fakeFunctionID)
	}
	if state.ApplicationID != fakeApplicationID || state.FunctionID != fakeFunctionID {
		t.Fatalf("state = %#v, want resolved application/function IDs", state)
	}
}

func TestDeleteManagedFunctionResolvesFunctionByApplicationID(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{
		functions: []ocifunctions.FunctionSummary{{
			Id:             common.String(fakeFunctionID),
			DisplayName:    common.String("hello"),
			LifecycleState: ocifunctions.FunctionLifecycleStateActive,
		}},
	}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.DeleteManagedFunction(ctx, ManagedFunctionDeleteTarget{
		ApplicationID: fakeApplicationID,
		DisplayName:   "hello",
	})
	if err != nil {
		t.Fatalf("DeleteManagedFunction returned error: %v", err)
	}
	if fakeClient.region != "me-jeddah-1" {
		t.Fatalf("region = %q, want region from application OCID", fakeClient.region)
	}
	if fakeClient.deletedFunctionID != fakeFunctionID {
		t.Fatalf("deletedFunctionID = %q, want resolved %q", fakeClient.deletedFunctionID, fakeFunctionID)
	}
	if state.ApplicationID != fakeApplicationID || state.FunctionID != fakeFunctionID {
		t.Fatalf("state = %#v, want resolved application/function IDs", state)
	}
}

func TestDeleteManagedFunctionTreatsNotFoundAsSuccessfulCleanup(t *testing.T) {
	ctx := context.Background()
	fakeClient := &fakeManagementClient{deleteFunctionErr: fakeServiceError{status: 404, code: "NotAuthorizedOrNotFound", message: "not found"}}
	manager := newTestOCIManager(t, fakeClient)

	state, err := manager.DeleteManagedFunction(ctx, ManagedFunctionDeleteTarget{
		Region:     "me-jeddah-1",
		FunctionID: fakeFunctionID,
	})
	if err != nil {
		t.Fatalf("DeleteManagedFunction returned error for not found: %v", err)
	}
	if fakeClient.deletedFunctionID != fakeFunctionID {
		t.Fatalf("deletedFunctionID = %q, want %q", fakeClient.deletedFunctionID, fakeFunctionID)
	}
	if !state.Deleted {
		t.Fatalf("state.Deleted = false, want true for idempotent not-found cleanup")
	}
}

const (
	fakeApplicationID  = "ocid1.fnapp.oc1.me-jeddah-1.exampleuniqueid"
	fakeFunctionID     = "ocid1.fnfunc.oc1.me-jeddah-1.exampleuniqueid"
	fakeInvokeEndpoint = "https://functions.me-jeddah-1.oci.oraclecloud.com"
)

type fakeManagementClient struct {
	region               string
	applications         []ocifunctions.ApplicationSummary
	application          ocifunctions.Application
	updateApplicationErr error
	createdApplication   ocifunctions.CreateApplicationDetails
	updatedApplication   ocifunctions.UpdateApplicationDetails
	updatedApplicationID string
	deletedApplicationID string
	deleteApplicationErr error
	logs                 []ocilogging.LogSummary
	listLogsRequests     []ocilogging.ListLogsRequest
	createdLogGroupID    string
	createdLog           ocilogging.CreateLogDetails
	updatedLogGroupID    string
	updatedLogID         string
	updatedLog           ocilogging.UpdateLogDetails
	listLogsErr          error
	createLogErr         error
	updateLogErr         error
	createdFunction      ocifunctions.CreateFunctionDetails
	functions            []ocifunctions.FunctionSummary
	deletedFunctionID    string
	deleteFunctionErr    error
}

func (f *fakeManagementClient) SetRegion(region string) {
	f.region = region
}

func (f *fakeManagementClient) ListApplications(context.Context, ocifunctions.ListApplicationsRequest) (ocifunctions.ListApplicationsResponse, error) {
	return ocifunctions.ListApplicationsResponse{Items: f.applications}, nil
}

func (f *fakeManagementClient) CreateApplication(_ context.Context, request ocifunctions.CreateApplicationRequest) (ocifunctions.CreateApplicationResponse, error) {
	f.createdApplication = request.CreateApplicationDetails
	return ocifunctions.CreateApplicationResponse{
		Application: ocifunctions.Application{
			Id:                      common.String(fakeApplicationID),
			DisplayName:             request.CreateApplicationDetails.DisplayName,
			LifecycleState:          ocifunctions.ApplicationLifecycleStateActive,
			NetworkSecurityGroupIds: request.CreateApplicationDetails.NetworkSecurityGroupIds,
		},
	}, nil
}

func (f *fakeManagementClient) GetApplication(context.Context, ocifunctions.GetApplicationRequest) (ocifunctions.GetApplicationResponse, error) {
	if f.application.Id != nil {
		return ocifunctions.GetApplicationResponse{Application: f.application}, nil
	}
	return ocifunctions.GetApplicationResponse{
		Application: ocifunctions.Application{
			Id:             common.String(fakeApplicationID),
			DisplayName:    common.String("demo-app"),
			LifecycleState: ocifunctions.ApplicationLifecycleStateActive,
		},
	}, nil
}

func (f *fakeManagementClient) UpdateApplication(_ context.Context, request ocifunctions.UpdateApplicationRequest) (ocifunctions.UpdateApplicationResponse, error) {
	f.updatedApplicationID = stringValue(request.ApplicationId)
	f.updatedApplication = request.UpdateApplicationDetails
	if f.updateApplicationErr != nil {
		return ocifunctions.UpdateApplicationResponse{}, f.updateApplicationErr
	}
	application := f.application
	if application.Id == nil {
		application.Id = common.String(fakeApplicationID)
	}
	application.NetworkSecurityGroupIds = request.UpdateApplicationDetails.NetworkSecurityGroupIds
	application.Config = request.UpdateApplicationDetails.Config
	application.Logging = request.UpdateApplicationDetails.Logging
	application.LifecycleState = ocifunctions.ApplicationLifecycleStateActive
	return ocifunctions.UpdateApplicationResponse{Application: application}, nil
}

func (f *fakeManagementClient) DeleteApplication(_ context.Context, request ocifunctions.DeleteApplicationRequest) (ocifunctions.DeleteApplicationResponse, error) {
	f.deletedApplicationID = stringValue(request.ApplicationId)
	if f.deleteApplicationErr != nil {
		return ocifunctions.DeleteApplicationResponse{}, f.deleteApplicationErr
	}
	return ocifunctions.DeleteApplicationResponse{}, nil
}

func (f *fakeManagementClient) ListLogs(_ context.Context, request ocilogging.ListLogsRequest) (ocilogging.ListLogsResponse, error) {
	f.listLogsRequests = append(f.listLogsRequests, request)
	if f.listLogsErr != nil {
		return ocilogging.ListLogsResponse{}, f.listLogsErr
	}
	items := make([]ocilogging.LogSummary, 0, len(f.logs))
	for _, log := range f.logs {
		if request.LogType != "" && string(log.LogType) != string(request.LogType) {
			continue
		}
		if request.LifecycleState != "" && string(log.LifecycleState) != string(request.LifecycleState) {
			continue
		}
		if request.DisplayName != nil && stringValue(log.DisplayName) != stringValue(request.DisplayName) {
			continue
		}
		if request.SourceService != nil && !logSourceServiceMatches(log, stringValue(request.SourceService)) {
			continue
		}
		if request.SourceResource != nil && !logSourceResourceMatches(log, stringValue(request.SourceResource)) {
			continue
		}
		items = append(items, log)
	}
	return ocilogging.ListLogsResponse{Items: items}, nil
}

func (f *fakeManagementClient) CreateLog(_ context.Context, request ocilogging.CreateLogRequest) (ocilogging.CreateLogResponse, error) {
	f.createdLogGroupID = stringValue(request.LogGroupId)
	f.createdLog = request.CreateLogDetails
	if f.createLogErr != nil {
		return ocilogging.CreateLogResponse{}, f.createLogErr
	}
	return ocilogging.CreateLogResponse{}, nil
}

func (f *fakeManagementClient) UpdateLog(_ context.Context, request ocilogging.UpdateLogRequest) (ocilogging.UpdateLogResponse, error) {
	f.updatedLogGroupID = stringValue(request.LogGroupId)
	f.updatedLogID = stringValue(request.LogId)
	f.updatedLog = request.UpdateLogDetails
	if f.updateLogErr != nil {
		return ocilogging.UpdateLogResponse{}, f.updateLogErr
	}
	return ocilogging.UpdateLogResponse{}, nil
}

func logSourceServiceMatches(log ocilogging.LogSummary, service string) bool {
	if log.Configuration == nil {
		return false
	}
	source, ok := log.Configuration.Source.(ocilogging.OciService)
	return ok && stringValue(source.Service) == service
}

func logSourceResourceMatches(log ocilogging.LogSummary, resource string) bool {
	if log.Configuration == nil {
		return false
	}
	source, ok := log.Configuration.Source.(ocilogging.OciService)
	return ok && stringValue(source.Resource) == resource
}

func (f *fakeManagementClient) ListFunctions(context.Context, ocifunctions.ListFunctionsRequest) (ocifunctions.ListFunctionsResponse, error) {
	return ocifunctions.ListFunctionsResponse{Items: f.functions}, nil
}

func (f *fakeManagementClient) CreateFunction(_ context.Context, request ocifunctions.CreateFunctionRequest) (ocifunctions.CreateFunctionResponse, error) {
	f.createdFunction = request.CreateFunctionDetails
	return ocifunctions.CreateFunctionResponse{
		Function: ocifunctions.Function{
			Id:             common.String(fakeFunctionID),
			DisplayName:    request.CreateFunctionDetails.DisplayName,
			InvokeEndpoint: common.String(fakeInvokeEndpoint),
			LifecycleState: ocifunctions.FunctionLifecycleStateActive,
		},
	}, nil
}

func (f *fakeManagementClient) GetFunction(context.Context, ocifunctions.GetFunctionRequest) (ocifunctions.GetFunctionResponse, error) {
	return ocifunctions.GetFunctionResponse{
		Function: ocifunctions.Function{
			Id:             common.String(fakeFunctionID),
			DisplayName:    common.String("hello"),
			InvokeEndpoint: common.String(fakeInvokeEndpoint),
			LifecycleState: ocifunctions.FunctionLifecycleStateActive,
		},
	}, nil
}

func (f *fakeManagementClient) UpdateFunction(context.Context, ocifunctions.UpdateFunctionRequest) (ocifunctions.UpdateFunctionResponse, error) {
	return ocifunctions.UpdateFunctionResponse{}, nil
}

func (f *fakeManagementClient) DeleteFunction(_ context.Context, request ocifunctions.DeleteFunctionRequest) (ocifunctions.DeleteFunctionResponse, error) {
	f.deletedFunctionID = stringValue(request.FunctionId)
	if f.deleteFunctionErr != nil {
		return ocifunctions.DeleteFunctionResponse{}, f.deleteFunctionErr
	}
	return ocifunctions.DeleteFunctionResponse{}, nil
}

func newTestOCIManager(t *testing.T, fakeClient *fakeManagementClient) *OCI {
	t.Helper()
	manager, err := NewOCI(OCIOptions{
		ConfigProvider: common.NewRawConfigurationProvider("tenancy", "user", "me-jeddah-1", "fingerprint", "private-key", nil),
		ClientFactory: func(common.ConfigurationProvider) (functionsManagementClient, error) {
			return fakeClient, nil
		},
		LoggingClientFactory: func(common.ConfigurationProvider) (loggingManagementClient, error) {
			return fakeClient, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}
	return manager
}

type fakeServiceError struct {
	status  int
	code    string
	message string
}

func (f fakeServiceError) Error() string {
	return f.message
}

func (f fakeServiceError) GetHTTPStatusCode() int {
	return f.status
}

func (f fakeServiceError) GetMessage() string {
	return f.message
}

func (f fakeServiceError) GetCode() string {
	return f.code
}

func (f fakeServiceError) GetOpcRequestID() string {
	return "opc-request-id"
}

func validDesiredFunction() DesiredFunction {
	return DesiredFunction{
		Region:           "me-jeddah-1",
		CompartmentID:    "ocid1.compartment.oc1..exampleuniqueid",
		ApplicationName:  "demo-app",
		SubnetIDs:        []string{"ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"},
		DisplayName:      "hello",
		Image:            "me-jeddah-1.ocir.io/example/functions/hello:latest",
		MemoryInMBs:      256,
		TimeoutInSeconds: 60,
		Config:           map[string]string{"GREETING": "hello"},
		FreeformTags:     map[string]string{"managed-by": "oci-functions-operator"},
	}
}

func hasLifecycleEvent(events []Event, eventType EventType, reason string) bool {
	for _, event := range events {
		if event.Type == eventType && event.Reason == reason {
			return true
		}
	}
	return false
}
