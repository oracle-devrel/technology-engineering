// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package v1alpha1

import (
	"os"
	"strings"
	"testing"

	apiextensionsv1 "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1"
	"sigs.k8s.io/yaml"
)

func TestFunctionEventTriggerSampleSchemaDoesNotRequireOCIFields(t *testing.T) {
	crdBytes, err := os.ReadFile("../../config/crd/bases/functions.oci.oracle.com_functioneventtriggers.yaml")
	if err != nil {
		t.Fatalf("read generated FunctionEventTrigger CRD: %v", err)
	}
	var crd apiextensionsv1.CustomResourceDefinition
	if err := yaml.Unmarshal(crdBytes, &crd); err != nil {
		t.Fatalf("unmarshal generated FunctionEventTrigger CRD: %v", err)
	}

	specSchema := crd.Spec.Versions[0].Schema.OpenAPIV3Schema.Properties["spec"]
	required := map[string]bool{}
	for _, field := range specSchema.Required {
		required[field] = true
	}
	if !required["condition"] || !required["functionRef"] {
		t.Fatalf("spec required fields = %#v, want condition and functionRef", specSchema.Required)
	}
	for _, field := range []string{"compartmentId", "displayName"} {
		if required[field] {
			t.Fatalf("spec required fields = %#v, must not require %s for functionevent.* triggers", specSchema.Required, field)
		}
	}
	if len(specSchema.XValidations) != 0 {
		t.Fatalf("spec x-kubernetes-validations = %#v, want none so CRD CEL cost stays low", specSchema.XValidations)
	}

	sampleBytes, err := os.ReadFile("../../config/samples/functions_v1alpha1_functioneventtrigger_order_created.yaml")
	if err != nil {
		t.Fatalf("read FunctionEventTrigger sample: %v", err)
	}
	var sample map[string]interface{}
	if err := yaml.Unmarshal(sampleBytes, &sample); err != nil {
		t.Fatalf("unmarshal FunctionEventTrigger sample: %v", err)
	}
	spec, ok := sample["spec"].(map[string]interface{})
	if !ok {
		t.Fatalf("sample spec = %#v, want object", sample["spec"])
	}
	if _, ok := spec["compartmentId"]; ok {
		t.Fatalf("sample must not set spec.compartmentId for FunctionEvent-only trigger")
	}
	if _, ok := spec["displayName"]; ok {
		t.Fatalf("sample must not set spec.displayName for FunctionEvent-only trigger")
	}
	condition, ok := spec["condition"].(map[string]interface{})
	if !ok {
		t.Fatalf("sample condition = %#v, want object", spec["condition"])
	}
	eventTypes, ok := condition["eventType"].([]interface{})
	if !ok || len(eventTypes) == 0 {
		t.Fatalf("sample condition.eventType = %#v, want non-empty list", condition["eventType"])
	}
	for _, value := range eventTypes {
		eventType, ok := value.(string)
		if !ok || !strings.HasPrefix(eventType, "functionevent.") {
			t.Fatalf("sample condition.eventType item = %#v, want %q prefix", value, "functionevent.")
		}
	}
}
