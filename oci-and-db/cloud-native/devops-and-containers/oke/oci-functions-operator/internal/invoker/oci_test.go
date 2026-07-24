// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package invoker

import (
	"context"
	"errors"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"

	operatorauth "github.com/oracle/oci-functions-operator/internal/ociauth"
	"github.com/oracle/oci-go-sdk/v65/common"
	ocifunctions "github.com/oracle/oci-go-sdk/v65/functions"
)

func TestNormalizeInvokeEndpoint(t *testing.T) {
	tests := []struct {
		name      string
		value     string
		want      string
		wantError string
	}{
		{
			name:      "missing",
			wantError: "target invoke endpoint is required",
		},
		{
			name:      "missing scheme",
			value:     "functions.us-ashburn-1.oci.oraclecloud.com",
			wantError: "must start with https:// or http://",
		},
		{
			name:      "missing host",
			value:     "https://",
			wantError: "endpoint must include a host",
		},
		{
			name:      "path rejected",
			value:     "https://functions.us-ashburn-1.oci.oraclecloud.com/20181201",
			wantError: "must not include a path",
		},
		{
			name:  "trims trailing slash",
			value: " https://functions.us-ashburn-1.oci.oraclecloud.com/ ",
			want:  "https://functions.us-ashburn-1.oci.oraclecloud.com",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := normalizeInvokeEndpoint(tt.value)
			if tt.wantError != "" {
				if err == nil {
					t.Fatalf("normalizeInvokeEndpoint returned nil error, want %q", tt.wantError)
				}
				if !strings.Contains(err.Error(), tt.wantError) {
					t.Fatalf("error = %q, want containing %q", err, tt.wantError)
				}
				return
			}
			if err != nil {
				t.Fatalf("normalizeInvokeEndpoint returned error: %v", err)
			}
			if got != tt.want {
				t.Fatalf("endpoint = %q, want %q", got, tt.want)
			}
		})
	}
}

func TestNewOCIDoesNotRequireInvokeEndpointAtConstruction(t *testing.T) {
	_, err := NewOCI(OCIOptions{
		ConfigProvider: common.NewRawConfigurationProvider("tenancy", "user", "us-ashburn-1", "fingerprint", "private-key", nil),
		ClientFactory: func(common.ConfigurationProvider, string) (functionsInvokeClient, error) {
			t.Fatalf("client factory was called before invocation")
			return nil, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}
}

func TestNormalizeOCIAuthModeDefaultsToWorkload(t *testing.T) {
	authMode, err := normalizeOCIAuthMode("")
	if err != nil {
		t.Fatalf("normalizeOCIAuthMode returned error: %v", err)
	}
	if authMode != OCIAuthModeWorkload {
		t.Fatalf("auth mode = %q, want %q", authMode, OCIAuthModeWorkload)
	}
}

func TestNormalizeOCIAuthModeRejectsUnknownMode(t *testing.T) {
	_, err := normalizeOCIAuthMode("bogus")
	if err == nil {
		t.Fatalf("normalizeOCIAuthMode returned nil error, want unsupported mode error")
	}
	if !strings.Contains(err.Error(), "unsupported "+EnvOCIAuthMode) {
		t.Fatalf("error = %q, want unsupported auth mode message", err)
	}
}

func TestNewOCIDefaultsToWorkloadAuth(t *testing.T) {
	workloadProvider := common.NewRawConfigurationProvider("tenancy", "user", "us-ashburn-1", "fingerprint", "private-key", nil)
	configProvider := common.NewRawConfigurationProvider("config-tenancy", "config-user", "us-phoenix-1", "config-fingerprint", "private-key", nil)
	workloadCalled := false
	configCalled := false
	clientCalled := false

	ociInvoker, err := NewOCI(OCIOptions{
		WorkloadIdentityProviderFactory: func(_ operatorauth.WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			workloadCalled = true
			return workloadProvider, nil
		},
		ConfigFileProviderFactory: func() common.ConfigurationProvider {
			configCalled = true
			return configProvider
		},
		ClientFactory: func(configProvider common.ConfigurationProvider, endpoint string) (functionsInvokeClient, error) {
			clientCalled = true
			if configProvider != workloadProvider {
				t.Fatalf("config provider = %#v, want workload provider", configProvider)
			}
			if endpoint != "https://functions.us-ashburn-1.oci.oraclecloud.com" {
				t.Fatalf("endpoint = %q, want normalized endpoint", endpoint)
			}
			return &fakeFunctionsInvokeClient{}, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}
	if !workloadCalled {
		t.Fatalf("workload provider factory was not called")
	}
	if configCalled {
		t.Fatalf("config provider factory was called, want workload default")
	}
	if clientCalled {
		t.Fatalf("client factory was called before invocation")
	}

	_, err = ociInvoker.Invoke(context.Background(), Request{
		Target: Target{
			FunctionOCID:   "ocid1.fnfunc.oc1.iad.exampleuniqueid",
			InvokeEndpoint: "https://functions.us-ashburn-1.oci.oraclecloud.com",
		},
	})
	if err != nil {
		t.Fatalf("Invoke returned error: %v", err)
	}
	if !clientCalled {
		t.Fatalf("client factory was not called during invocation")
	}
}

func TestNewOCIWorkloadModeWrapsUnavailableProvider(t *testing.T) {
	expectedErr := errors.New("not running in OKE workload identity")

	_, err := NewOCI(OCIOptions{
		AuthMode: OCIAuthModeWorkload,
		WorkloadIdentityProviderFactory: func(_ operatorauth.WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			return nil, expectedErr
		},
		ClientFactory: func(common.ConfigurationProvider, string) (functionsInvokeClient, error) {
			t.Fatalf("client factory was called before workload auth provider succeeded")
			return nil, nil
		},
	})
	if err == nil {
		t.Fatalf("NewOCI returned nil error, want workload auth provider error")
	}
	if !errors.Is(err, expectedErr) {
		t.Fatalf("error = %v, want wrapped %v", err, expectedErr)
	}
	if !strings.Contains(err.Error(), "configure OCI Workload Identity auth provider") {
		t.Fatalf("error = %q, want workload identity context", err)
	}
}

func TestNewOCIFromEnvironmentWorkloadModeReportsMissingProviderEnvironment(t *testing.T) {
	t.Setenv(EnvOCIAuthMode, OCIAuthModeWorkload)
	unsetEnv(t, EnvOCIRegion)

	_, err := NewOCIFromEnvironment()
	if err == nil {
		t.Fatalf("NewOCIFromEnvironment returned nil error, want workload auth provider error")
	}
	if !strings.Contains(err.Error(), "configure OCI Workload Identity auth provider") {
		t.Fatalf("error = %q, want workload identity context", err)
	}
	if !strings.Contains(err.Error(), EnvOCIRegion) {
		t.Fatalf("error = %q, want missing %s detail", err, EnvOCIRegion)
	}
	if strings.Contains(err.Error(), "OCI_RESOURCE_PRINCIPAL") {
		t.Fatalf("error = %q, should not expose Resource Principal env vars for workload auth", err)
	}
}

func TestNewOCIConfigModeUsesConfigProvider(t *testing.T) {
	configProvider := common.NewRawConfigurationProvider("tenancy", "user", "us-ashburn-1", "fingerprint", "private-key", nil)
	configCalled := false
	clientCalled := false

	ociInvoker, err := NewOCI(OCIOptions{
		AuthMode: OCIAuthModeConfig,
		ConfigFileProviderFactory: func() common.ConfigurationProvider {
			configCalled = true
			return configProvider
		},
		WorkloadIdentityProviderFactory: func(_ operatorauth.WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			t.Fatalf("workload provider factory was called for config auth mode")
			return nil, nil
		},
		ClientFactory: func(got common.ConfigurationProvider, _ string) (functionsInvokeClient, error) {
			clientCalled = true
			if got != configProvider {
				t.Fatalf("config provider = %#v, want config file provider", got)
			}
			return &fakeFunctionsInvokeClient{}, nil
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}
	if !configCalled {
		t.Fatalf("config provider factory was not called")
	}
	_, err = ociInvoker.Invoke(context.Background(), Request{
		Target: Target{
			FunctionOCID:   "ocid1.fnfunc.oc1.iad.exampleuniqueid",
			InvokeEndpoint: "https://functions.us-ashburn-1.oci.oraclecloud.com",
		},
	})
	if err != nil {
		t.Fatalf("Invoke returned error: %v", err)
	}
	if !clientCalled {
		t.Fatalf("client factory was not called during invocation")
	}
}

func TestConfigProviderFromEnvironmentUsesConfigFileAndProfile(t *testing.T) {
	configPath := filepath.Join(t.TempDir(), "config")
	config := `
[DEFAULT]
user=ocid1.user.oc1..default
fingerprint=00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00
tenancy=ocid1.tenancy.oc1..default
region=us-phoenix-1
key_file=/does/not/matter

[LOCAL]
user=ocid1.user.oc1..local
fingerprint=11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11
tenancy=ocid1.tenancy.oc1..local
region=us-ashburn-1
key_file=/does/not/matter
`
	if err := os.WriteFile(configPath, []byte(config), 0600); err != nil {
		t.Fatalf("write OCI config fixture: %v", err)
	}
	t.Setenv(EnvOCIConfigFile, configPath)
	t.Setenv(EnvOCIConfigProfile, "LOCAL")

	configProvider := ociConfigProviderFromEnvironment()
	region, err := configProvider.Region()
	if err != nil {
		t.Fatalf("Region returned error: %v", err)
	}
	if region != "us-ashburn-1" {
		t.Fatalf("region = %q, want LOCAL profile region", region)
	}
	userOCID, err := configProvider.UserOCID()
	if err != nil {
		t.Fatalf("UserOCID returned error: %v", err)
	}
	if userOCID != "ocid1.user.oc1..local" {
		t.Fatalf("user OCID = %q, want LOCAL profile user", userOCID)
	}
}

func TestNewOCIRejectsInvalidAuthMode(t *testing.T) {
	_, err := NewOCI(OCIOptions{
		AuthMode: "bogus",
		ClientFactory: func(common.ConfigurationProvider, string) (functionsInvokeClient, error) {
			t.Fatalf("client factory was called for invalid auth mode")
			return nil, nil
		},
	})
	if err == nil {
		t.Fatalf("NewOCI returned nil error, want invalid auth mode error")
	}
	if !strings.Contains(err.Error(), "unsupported "+EnvOCIAuthMode) {
		t.Fatalf("error = %q, want unsupported auth mode message", err)
	}
}

func TestOCIInvokeWrapsClientConfigurationErrors(t *testing.T) {
	ociInvoker, err := NewOCI(OCIOptions{
		ConfigProvider: common.NewRawConfigurationProvider("", "", "", "", "", nil),
		ClientFactory: func(common.ConfigurationProvider, string) (functionsInvokeClient, error) {
			return nil, errors.New("bad config")
		},
	})
	if err != nil {
		t.Fatalf("NewOCI returned error: %v", err)
	}

	_, err = ociInvoker.Invoke(context.Background(), Request{
		Target: Target{
			FunctionOCID:   "ocid1.fnfunc.oc1.iad.exampleuniqueid",
			InvokeEndpoint: "https://functions.us-ashburn-1.oci.oraclecloud.com",
		},
	})
	if err == nil {
		t.Fatalf("Invoke returned nil error, want config provider error")
	}
	if !strings.Contains(err.Error(), "configure OCI Functions invoke client") {
		t.Fatalf("error = %q, want OCI client configuration context", err)
	}
}

func TestOCIInvokeClassifiesTimeout(t *testing.T) {
	fakeClient := &fakeFunctionsInvokeClient{err: context.DeadlineExceeded}
	ociInvoker := newTestOCIInvoker(fakeClient, nil)

	_, err := ociInvoker.Invoke(context.Background(), Request{
		Target: targetWithEndpoint(),
	})
	if err == nil {
		t.Fatalf("Invoke returned nil error, want timeout error")
	}
	if !strings.Contains(err.Error(), "oci timeout") {
		t.Fatalf("error = %q, want timeout classification", err)
	}
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("error = %v, want wrapped context deadline", err)
	}
}

func TestOCIInvokeRequiresFunctionOCID(t *testing.T) {
	ociInvoker := newTestOCIInvoker(&fakeFunctionsInvokeClient{}, nil)

	_, err := ociInvoker.Invoke(context.Background(), Request{})
	if err == nil {
		t.Fatalf("Invoke returned nil error, want missing function OCID error")
	}
	if !strings.Contains(err.Error(), "function OCID") {
		t.Fatalf("error = %q, want function OCID message", err)
	}
}

func TestOCIInvokeRequiresInvokeEndpoint(t *testing.T) {
	ociInvoker := newTestOCIInvoker(&fakeFunctionsInvokeClient{}, nil)

	_, err := ociInvoker.Invoke(context.Background(), Request{
		Target: Target{FunctionOCID: "ocid1.fnfunc.oc1.iad.exampleuniqueid"},
	})
	if err == nil {
		t.Fatalf("Invoke returned nil error, want missing invoke endpoint error")
	}
	if !strings.Contains(err.Error(), "invoke endpoint") {
		t.Fatalf("error = %q, want invoke endpoint message", err)
	}
}

func TestOCIInvokeMapsRequestAndResponse(t *testing.T) {
	var endpoint string
	fakeClient := &fakeFunctionsInvokeClient{
		response: ocifunctions.InvokeFunctionResponse{
			RawResponse: &http.Response{
				StatusCode: http.StatusAccepted,
				Header: http.Header{
					"Fn-Call-Id":     []string{"call-id"},
					"Opc-Request-Id": []string{"opc-request-id"},
				},
			},
			Content: io.NopCloser(strings.NewReader(`{"ok":true}`)),
		},
	}
	ociInvoker := newTestOCIInvoker(fakeClient, &endpoint)

	response, err := ociInvoker.Invoke(context.Background(), Request{
		Target: Target{
			FunctionOCID:   "ocid1.fnfunc.oc1.iad.exampleuniqueid",
			InvokeEndpoint: "https://functions.us-ashburn-1.oci.oraclecloud.com/",
		},
		Index: 3,
		Body:  []byte(`{"input":true}`),
	})
	if err != nil {
		t.Fatalf("Invoke returned error: %v", err)
	}

	if fakeClient.functionID == nil || *fakeClient.functionID != "ocid1.fnfunc.oc1.iad.exampleuniqueid" {
		t.Fatalf("function ID = %v, want request target OCID", fakeClient.functionID)
	}
	if string(fakeClient.body) != `{"input":true}` {
		t.Fatalf("request body = %s, want inline payload", fakeClient.body)
	}
	if fakeClient.invokeType != ocifunctions.InvokeFunctionFnInvokeTypeSync {
		t.Fatalf("invoke type = %q, want sync", fakeClient.invokeType)
	}
	if endpoint != "https://functions.us-ashburn-1.oci.oraclecloud.com" {
		t.Fatalf("endpoint = %q, want normalized request target endpoint", endpoint)
	}
	if response.InvocationID != "call-id" {
		t.Fatalf("invocation ID = %q, want Fn-Call-Id", response.InvocationID)
	}
	if response.OCIRequestID != "opc-request-id" {
		t.Fatalf("OCI request ID = %q, want opc-request-id", response.OCIRequestID)
	}
	if response.StatusCode != http.StatusAccepted {
		t.Fatalf("status code = %d, want %d", response.StatusCode, http.StatusAccepted)
	}
	if string(response.Body) != `{"ok":true}` {
		t.Fatalf("response body = %s, want function response body", response.Body)
	}
}

func TestOCIInvokeFallsBackToOpcRequestID(t *testing.T) {
	opcRequestID := "opc-request-id"
	fakeClient := &fakeFunctionsInvokeClient{
		response: ocifunctions.InvokeFunctionResponse{
			OpcRequestId: common.String(opcRequestID),
			RawResponse:  &http.Response{StatusCode: http.StatusOK},
		},
	}
	ociInvoker := newTestOCIInvoker(fakeClient, nil)

	response, err := ociInvoker.Invoke(context.Background(), Request{
		Target: targetWithEndpoint(),
	})
	if err != nil {
		t.Fatalf("Invoke returned error: %v", err)
	}
	if response.InvocationID != opcRequestID {
		t.Fatalf("invocation ID = %q, want opc request ID", response.InvocationID)
	}
	if response.OCIRequestID != opcRequestID {
		t.Fatalf("OCI request ID = %q, want opc request ID", response.OCIRequestID)
	}
}

func TestOCIInvokeFailsOnNon2xxResponse(t *testing.T) {
	largeBody := strings.Repeat("x", maxOCIErrorBodyBytes+100)
	fakeClient := &fakeFunctionsInvokeClient{
		response: ocifunctions.InvokeFunctionResponse{
			RawResponse: &http.Response{
				StatusCode: http.StatusBadGateway,
				Header: http.Header{
					"Opc-Request-Id": []string{"opc-request-id"},
				},
			},
			Content: io.NopCloser(strings.NewReader(largeBody)),
		},
	}
	ociInvoker := newTestOCIInvoker(fakeClient, nil)

	response, err := ociInvoker.Invoke(context.Background(), Request{
		Target: targetWithEndpoint(),
	})
	if err == nil {
		t.Fatalf("Invoke returned nil error, want non-2xx error")
	}
	if !strings.Contains(err.Error(), "oci non-2xx response") {
		t.Fatalf("error = %q, want non-2xx classification", err)
	}
	if !strings.Contains(err.Error(), "status=502") || !strings.Contains(err.Error(), "ociRequestId=opc-request-id") {
		t.Fatalf("error = %q, want status and request ID", err)
	}
	if !strings.Contains(err.Error(), "(truncated)") {
		t.Fatalf("error = %q, want truncated body marker", err)
	}
	if len(err.Error()) > maxOCIErrorBodyBytes+250 {
		t.Fatalf("error length = %d, want bounded non-2xx message", len(err.Error()))
	}
	if response.OCIRequestID != "opc-request-id" || response.StatusCode != http.StatusBadGateway {
		t.Fatalf("response metadata = %#v, want request ID and 502 status", response)
	}
}

func TestOCIInvokeReturnsResponseMetadataOnSDKError(t *testing.T) {
	expectedErr := errors.New("sdk failure")
	fakeClient := &fakeFunctionsInvokeClient{
		err: expectedErr,
		response: ocifunctions.InvokeFunctionResponse{
			RawResponse: &http.Response{
				StatusCode: http.StatusUnauthorized,
				Header:     http.Header{"Opc-Request-Id": []string{"opc-request-id"}},
			},
		},
	}
	ociInvoker := newTestOCIInvoker(fakeClient, nil)

	response, err := ociInvoker.Invoke(context.Background(), Request{
		Target: targetWithEndpoint(),
	})
	if err == nil {
		t.Fatalf("Invoke returned nil error, want SDK error")
	}
	if !errors.Is(err, expectedErr) {
		t.Fatalf("error = %v, want wrapped %v", err, expectedErr)
	}
	if response.OCIRequestID != "opc-request-id" || response.StatusCode != http.StatusUnauthorized {
		t.Fatalf("response metadata = %#v, want request ID and status from failed response", response)
	}
}

type fakeFunctionsInvokeClient struct {
	response   ocifunctions.InvokeFunctionResponse
	err        error
	functionID *string
	body       []byte
	invokeType ocifunctions.InvokeFunctionFnInvokeTypeEnum
}

func newTestOCIInvoker(fakeClient *fakeFunctionsInvokeClient, endpoint *string) *OCI {
	return &OCI{
		configProvider: common.NewRawConfigurationProvider("tenancy", "user", "us-ashburn-1", "fingerprint", "private-key", nil),
		clientFactory: func(_ common.ConfigurationProvider, gotEndpoint string) (functionsInvokeClient, error) {
			if endpoint != nil {
				*endpoint = gotEndpoint
			}
			return fakeClient, nil
		},
	}
}

func targetWithEndpoint() Target {
	return Target{
		FunctionOCID:   "ocid1.fnfunc.oc1.iad.exampleuniqueid",
		InvokeEndpoint: "https://functions.us-ashburn-1.oci.oraclecloud.com",
	}
}

func (f *fakeFunctionsInvokeClient) InvokeFunction(_ context.Context, request ocifunctions.InvokeFunctionRequest) (ocifunctions.InvokeFunctionResponse, error) {
	f.functionID = request.FunctionId
	f.invokeType = request.FnInvokeType
	if request.InvokeFunctionBody != nil {
		body, err := io.ReadAll(request.InvokeFunctionBody)
		if err != nil {
			return ocifunctions.InvokeFunctionResponse{}, err
		}
		f.body = body
	}
	return f.response, f.err
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
