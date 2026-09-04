// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package invoker

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"

	operatorauth "github.com/oracle/oci-functions-operator/internal/ociauth"
	"github.com/oracle/oci-go-sdk/v65/common"
	ocifunctions "github.com/oracle/oci-go-sdk/v65/functions"
)

const (
	// EnvOCIAuthMode selects the OCI SDK auth provider used in OCI invoker mode.
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

const maxOCIErrorBodyBytes = 512

type functionsInvokeClient interface {
	InvokeFunction(ctx context.Context, request ocifunctions.InvokeFunctionRequest) (ocifunctions.InvokeFunctionResponse, error)
}

type functionsInvokeClientFactory func(common.ConfigurationProvider, string) (functionsInvokeClient, error)
type workloadIdentityProviderFactory = operatorauth.WorkloadIdentityProviderFactory
type configFileProviderFactory = operatorauth.ConfigFileProviderFactory

// OCIOptions configures an OCI-backed invoker.
type OCIOptions struct {
	AuthMode                        string
	Region                          string
	ConfigProvider                  common.ConfigurationProvider
	WorkloadIdentityProviderFactory workloadIdentityProviderFactory
	ConfigFileProviderFactory       configFileProviderFactory
	ClientFactory                   functionsInvokeClientFactory
}

// OCI invokes OCI Functions through the OCI Go SDK.
type OCI struct {
	configProvider common.ConfigurationProvider
	clientFactory  functionsInvokeClientFactory
}

// RequiresFunctionID reports that OCI mode requires a resolved OCI Function OCID.
func (o *OCI) RequiresFunctionID() bool {
	return true
}

// NewOCIFromEnvironment constructs an OCI invoker from OCI-related environment variables.
func NewOCIFromEnvironment() (*OCI, error) {
	return NewOCI(OCIOptions{
		AuthMode: os.Getenv(EnvOCIAuthMode),
		Region:   os.Getenv(EnvOCIRegion),
	})
}

// NewOCI constructs an OCI invoker.
func NewOCI(options OCIOptions) (*OCI, error) {
	configProvider := options.ConfigProvider
	var err error
	if configProvider == nil {
		configProvider, err = ociConfigProviderForAuthMode(options)
		if err != nil {
			return nil, err
		}
	}

	clientFactory := options.ClientFactory
	if clientFactory == nil {
		clientFactory = newFunctionsInvokeClient
	}

	return &OCI{
		configProvider: configProvider,
		clientFactory:  clientFactory,
	}, nil
}

func newFunctionsInvokeClient(configProvider common.ConfigurationProvider, endpoint string) (functionsInvokeClient, error) {
	return ocifunctions.NewFunctionsInvokeClientWithConfigurationProvider(configProvider, endpoint)
}

func ociConfigProviderForAuthMode(options OCIOptions) (common.ConfigurationProvider, error) {
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

func normalizeInvokeEndpoint(value string) (string, error) {
	endpoint := strings.TrimSpace(value)
	if endpoint == "" {
		return "", fmt.Errorf("target invoke endpoint is required in OCI mode")
	}

	parsed, err := url.Parse(endpoint)
	if err != nil {
		return "", fmt.Errorf("invalid target invoke endpoint %q: %w", endpoint, err)
	}
	if parsed.Scheme != "https" && parsed.Scheme != "http" {
		return "", fmt.Errorf("invalid target invoke endpoint %q: endpoint must start with https:// or http://", endpoint)
	}
	if parsed.Host == "" {
		return "", fmt.Errorf("invalid target invoke endpoint %q: endpoint must include a host", endpoint)
	}
	if parsed.Path != "" && parsed.Path != "/" {
		return "", fmt.Errorf("invalid target invoke endpoint %q: endpoint must not include a path; the OCI SDK adds the Functions API path", endpoint)
	}

	return strings.TrimRight(endpoint, "/"), nil
}

// Invoke invokes an OCI Function by OCID and per-function invoke endpoint.
func (o *OCI) Invoke(ctx context.Context, request Request) (Response, error) {
	functionID := strings.TrimSpace(request.Target.FunctionOCID)
	if functionID == "" {
		return Response{}, fmt.Errorf("oci invoker requires target function OCID")
	}
	if o == nil || o.configProvider == nil || o.clientFactory == nil {
		return Response{}, fmt.Errorf("oci invoker is not configured")
	}
	endpoint, err := normalizeInvokeEndpoint(request.Target.InvokeEndpoint)
	if err != nil {
		return Response{}, err
	}
	client, err := o.clientFactory(o.configProvider, endpoint)
	if err != nil {
		return Response{}, fmt.Errorf("configure OCI Functions invoke client for endpoint %s: %w", endpoint, err)
	}

	ociRequest := ocifunctions.InvokeFunctionRequest{
		FunctionId:   common.String(functionID),
		FnInvokeType: ocifunctions.InvokeFunctionFnInvokeTypeSync,
	}
	if request.Body != nil {
		ociRequest.InvokeFunctionBody = io.NopCloser(bytes.NewReader(request.Body))
	}

	ociResponse, err := client.InvokeFunction(ctx, ociRequest)
	response := responseFromOCI(ociResponse)
	if err != nil {
		if response.OCIRequestID == "" {
			response.OCIRequestID = ociRequestIDFromError(err)
		}
		if response.StatusCode == 0 {
			response.StatusCode = int32(statusCodeFromError(err))
		}
		return response, classifyOCIInvokeError(functionID, response, err)
	}

	if ociResponse.Content != nil {
		defer ociResponse.Content.Close()
		body, readErr := io.ReadAll(ociResponse.Content)
		if readErr != nil {
			return response, fmt.Errorf("read OCI Function %s response body: %w", functionID, readErr)
		}
		response.Body = body
	}
	if response.StatusCode != 0 && (response.StatusCode < http.StatusOK || response.StatusCode >= http.StatusMultipleChoices) {
		return response, non2xxOCIResponseError(functionID, response, response.Body)
	}

	return response, nil
}

func responseFromOCI(response ocifunctions.InvokeFunctionResponse) Response {
	result := Response{}
	if response.RawResponse != nil {
		result.StatusCode = int32(response.RawResponse.StatusCode)
		if callID := response.RawResponse.Header.Get("Fn-Call-Id"); callID != "" {
			result.InvocationID = callID
		}
		result.OCIRequestID = response.RawResponse.Header.Get("opc-request-id")
		if result.InvocationID == "" {
			result.InvocationID = result.OCIRequestID
		}
	}
	if response.OpcRequestId != nil {
		if result.OCIRequestID == "" {
			result.OCIRequestID = *response.OpcRequestId
		}
		if result.InvocationID == "" {
			result.InvocationID = *response.OpcRequestId
		}
	}
	if result.OCIRequestID == "" {
		result.OCIRequestID = result.InvocationID
	}
	return result
}

func classifyOCIInvokeError(functionID string, response Response, err error) error {
	details := ociErrorDetails(response)
	if errors.Is(err, context.DeadlineExceeded) || os.IsTimeout(err) || isNetTimeout(err) {
		return fmt.Errorf("oci timeout invoking function %s%s: %w", functionID, details, err)
	}
	if isEndpointError(err) {
		return fmt.Errorf("oci endpoint error invoking function %s%s: %w", functionID, details, err)
	}
	if serviceError, ok := common.IsServiceError(err); ok {
		statusCode := serviceError.GetHTTPStatusCode()
		if response.OCIRequestID == "" {
			response.OCIRequestID = serviceError.GetOpcRequestID()
		}
		if response.StatusCode == 0 {
			response.StatusCode = int32(statusCode)
		}
		serviceDetails := ociErrorDetails(response)
		if serviceError.GetCode() != "" {
			serviceDetails += fmt.Sprintf(" code=%s", serviceError.GetCode())
		}

		switch {
		case statusCode == http.StatusUnauthorized || statusCode == http.StatusForbidden:
			return fmt.Errorf("oci auth error invoking function %s%s: %s", functionID, serviceDetails, serviceError.GetMessage())
		case statusCode == http.StatusNotFound:
			return fmt.Errorf("oci function OCID error invoking function %s%s: %s", functionID, serviceDetails, serviceError.GetMessage())
		default:
			return fmt.Errorf("oci service error invoking function %s%s: %s", functionID, serviceDetails, serviceError.GetMessage())
		}
	}
	if response.StatusCode >= http.StatusBadRequest {
		return fmt.Errorf("%s: %w", non2xxOCIResponseError(functionID, response, response.Body).Error(), err)
	}
	return fmt.Errorf("oci invoke error invoking function %s%s: %w", functionID, details, err)
}

func non2xxOCIResponseError(functionID string, response Response, body []byte) error {
	return fmt.Errorf("oci non-2xx response invoking function %s%s body=%q", functionID, ociErrorDetails(response), truncateForStatus(body))
}

func ociErrorDetails(response Response) string {
	parts := []string{}
	if response.StatusCode != 0 {
		parts = append(parts, fmt.Sprintf("status=%d", response.StatusCode))
	}
	if response.OCIRequestID != "" {
		parts = append(parts, fmt.Sprintf("ociRequestId=%s", response.OCIRequestID))
	}
	if response.InvocationID != "" && response.InvocationID != response.OCIRequestID {
		parts = append(parts, fmt.Sprintf("invocationId=%s", response.InvocationID))
	}
	if len(parts) == 0 {
		return ""
	}
	return " " + strings.Join(parts, " ")
}

func truncateForStatus(body []byte) string {
	value := strings.TrimSpace(string(body))
	if len(value) <= maxOCIErrorBodyBytes {
		return value
	}
	return value[:maxOCIErrorBodyBytes] + "...(truncated)"
}

func ociRequestIDFromError(err error) string {
	if serviceError, ok := common.IsServiceError(err); ok {
		return serviceError.GetOpcRequestID()
	}
	return ""
}

func statusCodeFromError(err error) int {
	if serviceError, ok := common.IsServiceError(err); ok {
		return serviceError.GetHTTPStatusCode()
	}
	return 0
}

func isNetTimeout(err error) bool {
	var netErr net.Error
	return errors.As(err, &netErr) && netErr.Timeout()
}

func isEndpointError(err error) bool {
	var urlErr *url.Error
	if errors.As(err, &urlErr) {
		return true
	}
	var dnsErr *net.DNSError
	if errors.As(err, &dnsErr) {
		return true
	}
	var opErr *net.OpError
	return errors.As(err, &opErr)
}
