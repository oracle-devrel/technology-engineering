// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package ociauth

import (
	"fmt"
	"os"
	"strings"
	"sync"

	"github.com/oracle/oci-go-sdk/v65/common"
	sdkAuth "github.com/oracle/oci-go-sdk/v65/common/auth"
)

const (
	// EnvOCIAuthMode selects the OCI SDK auth provider used in OCI mode.
	EnvOCIAuthMode = "OCI_AUTH_MODE"
	// EnvOCIConfigProfile optionally selects a profile from the OCI config file.
	EnvOCIConfigProfile = "OCI_CONFIG_PROFILE"
	// EnvOCIConfigFile optionally selects a non-default OCI config file path.
	EnvOCIConfigFile = "OCI_CONFIG_FILE"
	// EnvOCIRegion optionally supplies the OKE Workload Identity region.
	EnvOCIRegion = "OCI_REGION"

	// OCIAuthModeWorkload uses the OKE Workload Identity auth provider.
	OCIAuthModeWorkload = "workload"
	// OCIAuthModeConfig uses a local OCI config file/profile.
	OCIAuthModeConfig = "config"
)

// WorkloadIdentityProviderFactory creates an OKE Workload Identity configuration provider.
type WorkloadIdentityProviderFactory func(WorkloadIdentityOptions) (common.ConfigurationProvider, error)

// ConfigFileProviderFactory creates a local OCI config file/profile provider.
type ConfigFileProviderFactory func() common.ConfigurationProvider

type sdkOKEProviderFactory func() (common.ConfigurationProvider, error)

// WorkloadIdentityOptions configures the OKE Workload Identity provider.
type WorkloadIdentityOptions struct {
	Region string
}

// Options configures OCI SDK auth provider construction.
type Options struct {
	AuthMode                        string
	Region                          string
	ConfigProvider                  common.ConfigurationProvider
	WorkloadIdentityProviderFactory WorkloadIdentityProviderFactory
	ConfigFileProviderFactory       ConfigFileProviderFactory
}

var sdkWorkloadIdentityEnvMu sync.Mutex

// ConfigProviderFromEnvironment constructs an OCI SDK auth provider from OCI environment variables.
func ConfigProviderFromEnvironment() (common.ConfigurationProvider, error) {
	return ConfigProvider(Options{
		AuthMode: getenv(EnvOCIAuthMode),
		Region:   getenv(EnvOCIRegion),
	})
}

// ConfigProvider constructs the selected OCI SDK auth provider.
func ConfigProvider(options Options) (common.ConfigurationProvider, error) {
	if options.ConfigProvider != nil {
		return options.ConfigProvider, nil
	}

	authMode, err := NormalizeOCIAuthMode(options.AuthMode)
	if err != nil {
		return nil, err
	}

	switch authMode {
	case OCIAuthModeWorkload:
		providerFactory := options.WorkloadIdentityProviderFactory
		if providerFactory == nil {
			providerFactory = WorkloadIdentityConfigProviderFromEnvironment
		}
		configProvider, err := providerFactory(WorkloadIdentityOptions{
			Region: firstNonEmpty(options.Region, getenv(EnvOCIRegion)),
		})
		if err != nil {
			return nil, fmt.Errorf("configure OCI Workload Identity auth provider: %w", err)
		}
		return configProvider, nil
	case OCIAuthModeConfig:
		providerFactory := options.ConfigFileProviderFactory
		if providerFactory == nil {
			providerFactory = ConfigFileProviderFromEnvironment
		}
		return providerFactory(), nil
	default:
		return nil, fmt.Errorf("unsupported %s %q; supported values are %q and %q", EnvOCIAuthMode, options.AuthMode, OCIAuthModeWorkload, OCIAuthModeConfig)
	}
}

// NormalizeOCIAuthMode normalizes and validates an OCI auth mode.
func NormalizeOCIAuthMode(value string) (string, error) {
	authMode := strings.ToLower(strings.TrimSpace(value))
	if authMode == "" {
		return OCIAuthModeWorkload, nil
	}
	switch authMode {
	case OCIAuthModeWorkload, OCIAuthModeConfig:
		return authMode, nil
	default:
		return "", fmt.Errorf("unsupported %s %q; supported values are %q and %q", EnvOCIAuthMode, value, OCIAuthModeWorkload, OCIAuthModeConfig)
	}
}

// WorkloadIdentityConfigProviderFromEnvironment constructs the SDK OKE Workload Identity provider.
func WorkloadIdentityConfigProviderFromEnvironment(options WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
	return workloadIdentityConfigProvider(options, func() (common.ConfigurationProvider, error) {
		return sdkAuth.OkeWorkloadIdentityConfigurationProvider()
	})
}

func workloadIdentityConfigProvider(options WorkloadIdentityOptions, providerFactory sdkOKEProviderFactory) (common.ConfigurationProvider, error) {
	region := strings.TrimSpace(options.Region)
	if region == "" {
		return nil, fmt.Errorf("%s is required for OCI Workload Identity auth; set %s to the OKE cluster or workload region", EnvOCIRegion, EnvOCIRegion)
	}

	// The OCI Go SDK's OKE Workload Identity helper currently reads the region
	// and version from Resource Principal env var names even though this is not
	// the OKE deployment contract exposed by the operator. Bridge OCI_REGION to
	// those SDK internals only while constructing the provider.
	return withTemporarySDKWorkloadIdentityEnv(map[string]string{
		sdkAuth.ResourcePrincipalVersionEnvVar: sdkAuth.ResourcePrincipalVersion2_2,
		sdkAuth.ResourcePrincipalRegionEnvVar:  region,
	}, providerFactory)
}

func withTemporarySDKWorkloadIdentityEnv(values map[string]string, providerFactory sdkOKEProviderFactory) (common.ConfigurationProvider, error) {
	sdkWorkloadIdentityEnvMu.Lock()
	defer sdkWorkloadIdentityEnvMu.Unlock()

	original := make(map[string]*string, len(values))
	for key, value := range values {
		if current, ok := os.LookupEnv(key); ok {
			copied := current
			original[key] = &copied
		} else {
			original[key] = nil
		}
		if err := os.Setenv(key, value); err != nil {
			return nil, fmt.Errorf("set SDK Workload Identity environment %s: %w", key, err)
		}
	}

	configProvider, err := providerFactory()
	restoreErr := restoreEnv(original)
	if err != nil {
		return nil, err
	}
	if restoreErr != nil {
		return nil, restoreErr
	}
	return configProvider, nil
}

func restoreEnv(original map[string]*string) error {
	for key, value := range original {
		if value == nil {
			if err := os.Unsetenv(key); err != nil {
				return fmt.Errorf("restore SDK Workload Identity environment %s: %w", key, err)
			}
			continue
		}
		if err := os.Setenv(key, *value); err != nil {
			return fmt.Errorf("restore SDK Workload Identity environment %s: %w", key, err)
		}
	}
	return nil
}

// ConfigFileProviderFromEnvironment constructs a local OCI config file/profile provider.
func ConfigFileProviderFromEnvironment() common.ConfigurationProvider {
	profile := strings.TrimSpace(getenv(EnvOCIConfigProfile))
	if profile != "" {
		return common.CustomProfileConfigProvider(getenv(EnvOCIConfigFile), profile)
	}
	return common.DefaultConfigProvider()
}

func getenv(key string) string {
	return strings.TrimSpace(strings.Trim(os.Getenv(key), "\x00"))
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if trimmed := strings.TrimSpace(value); trimmed != "" {
			return trimmed
		}
	}
	return ""
}
