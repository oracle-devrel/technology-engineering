// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package ociauth

import (
	"errors"
	"os"
	"strings"
	"testing"

	"github.com/oracle/oci-go-sdk/v65/common"
	sdkAuth "github.com/oracle/oci-go-sdk/v65/common/auth"
)

func TestWorkloadModeDoesNotRequireResourcePrincipalRegion(t *testing.T) {
	unsetEnv(t, sdkAuth.ResourcePrincipalRegionEnvVar)

	expectedProvider := common.NewRawConfigurationProvider("tenancy", "user", "me-jeddah-1", "fingerprint", "private-key", nil)
	called := false
	provider, err := ConfigProvider(Options{
		AuthMode: OCIAuthModeWorkload,
		Region:   "me-jeddah-1",
		WorkloadIdentityProviderFactory: func(options WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			called = true
			if options.Region != "me-jeddah-1" {
				t.Fatalf("workload region = %q, want me-jeddah-1", options.Region)
			}
			if _, ok := os.LookupEnv(sdkAuth.ResourcePrincipalRegionEnvVar); ok {
				t.Fatalf("%s was required in the public workload auth environment", sdkAuth.ResourcePrincipalRegionEnvVar)
			}
			return expectedProvider, nil
		},
	})
	if err != nil {
		t.Fatalf("ConfigProvider returned error: %v", err)
	}
	if provider != expectedProvider {
		t.Fatalf("provider = %#v, want injected workload provider", provider)
	}
	if !called {
		t.Fatalf("workload provider factory was not called")
	}
}

func TestWorkloadModeReportsMissingOCIRegionWithoutResourcePrincipalMessage(t *testing.T) {
	unsetEnv(t, EnvOCIRegion)
	unsetEnv(t, sdkAuth.ResourcePrincipalRegionEnvVar)

	_, err := ConfigProvider(Options{AuthMode: OCIAuthModeWorkload})
	if err == nil {
		t.Fatalf("ConfigProvider returned nil error, want missing region error")
	}
	if !strings.Contains(err.Error(), EnvOCIRegion) {
		t.Fatalf("error = %q, want %s guidance", err, EnvOCIRegion)
	}
	if strings.Contains(err.Error(), "OCI_RESOURCE_PRINCIPAL") {
		t.Fatalf("error = %q, should not expose Resource Principal env vars for workload auth", err)
	}
}

func TestDefaultWorkloadProviderBridgesOCIRegionToSDKProvider(t *testing.T) {
	unsetEnv(t, sdkAuth.ResourcePrincipalVersionEnvVar)
	unsetEnv(t, sdkAuth.ResourcePrincipalRegionEnvVar)

	expectedProvider := common.NewRawConfigurationProvider("tenancy", "user", "me-jeddah-1", "fingerprint", "private-key", nil)
	called := false
	provider, err := workloadIdentityConfigProvider(WorkloadIdentityOptions{Region: "me-jeddah-1"}, func() (common.ConfigurationProvider, error) {
		called = true
		if got := os.Getenv(sdkAuth.ResourcePrincipalVersionEnvVar); got != sdkAuth.ResourcePrincipalVersion2_2 {
			t.Fatalf("%s = %q, want %q during SDK provider construction", sdkAuth.ResourcePrincipalVersionEnvVar, got, sdkAuth.ResourcePrincipalVersion2_2)
		}
		if got := os.Getenv(sdkAuth.ResourcePrincipalRegionEnvVar); got != "me-jeddah-1" {
			t.Fatalf("%s = %q, want me-jeddah-1 during SDK provider construction", sdkAuth.ResourcePrincipalRegionEnvVar, got)
		}
		return expectedProvider, nil
	})
	if err != nil {
		t.Fatalf("workloadIdentityConfigProvider returned error: %v", err)
	}
	if provider != expectedProvider {
		t.Fatalf("provider = %#v, want injected SDK provider", provider)
	}
	if !called {
		t.Fatalf("SDK OKE Workload Identity provider was not called")
	}
	if _, ok := os.LookupEnv(sdkAuth.ResourcePrincipalVersionEnvVar); ok {
		t.Fatalf("%s was not restored after SDK provider construction", sdkAuth.ResourcePrincipalVersionEnvVar)
	}
	if _, ok := os.LookupEnv(sdkAuth.ResourcePrincipalRegionEnvVar); ok {
		t.Fatalf("%s was not restored after SDK provider construction", sdkAuth.ResourcePrincipalRegionEnvVar)
	}
}

func TestConfigModeUsesConfigProvider(t *testing.T) {
	expectedProvider := common.NewRawConfigurationProvider("tenancy", "user", "us-ashburn-1", "fingerprint", "private-key", nil)
	configCalled := false

	provider, err := ConfigProvider(Options{
		AuthMode: OCIAuthModeConfig,
		ConfigFileProviderFactory: func() common.ConfigurationProvider {
			configCalled = true
			return expectedProvider
		},
		WorkloadIdentityProviderFactory: func(WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			t.Fatalf("workload provider factory was called for config auth mode")
			return nil, nil
		},
	})
	if err != nil {
		t.Fatalf("ConfigProvider returned error: %v", err)
	}
	if provider != expectedProvider {
		t.Fatalf("provider = %#v, want config provider", provider)
	}
	if !configCalled {
		t.Fatalf("config provider factory was not called")
	}
}

func TestInvalidAuthModeFailsClearly(t *testing.T) {
	_, err := ConfigProvider(Options{
		AuthMode: "bogus",
		WorkloadIdentityProviderFactory: func(WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			t.Fatalf("workload provider factory was called for invalid auth mode")
			return nil, nil
		},
		ConfigFileProviderFactory: func() common.ConfigurationProvider {
			t.Fatalf("config provider factory was called for invalid auth mode")
			return nil
		},
	})
	if err == nil {
		t.Fatalf("ConfigProvider returned nil error, want invalid auth mode error")
	}
	if !strings.Contains(err.Error(), "unsupported "+EnvOCIAuthMode) {
		t.Fatalf("error = %q, want unsupported auth mode message", err)
	}
}

func TestWorkloadProviderFactoryErrorIsWrapped(t *testing.T) {
	expectedErr := errors.New("not running in OKE")

	_, err := ConfigProvider(Options{
		AuthMode: OCIAuthModeWorkload,
		Region:   "me-jeddah-1",
		WorkloadIdentityProviderFactory: func(WorkloadIdentityOptions) (common.ConfigurationProvider, error) {
			return nil, expectedErr
		},
	})
	if err == nil {
		t.Fatalf("ConfigProvider returned nil error, want workload provider error")
	}
	if !errors.Is(err, expectedErr) {
		t.Fatalf("error = %v, want wrapped %v", err, expectedErr)
	}
	if !strings.Contains(err.Error(), "configure OCI Workload Identity auth provider") {
		t.Fatalf("error = %q, want workload identity context", err)
	}
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
