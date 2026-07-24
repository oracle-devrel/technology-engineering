LOCALBIN ?= $(shell pwd)/bin
CONTROLLER_GEN ?= $(LOCALBIN)/controller-gen
CONTROLLER_TOOLS_VERSION ?= v0.21.0
GENERATED_CRD_DIR ?= config/crd/bases
CHART_CRD_DIR ?= charts/oci-functions-operator/crds

.PHONY: all
all: generate manifests test

.PHONY: generate
generate: controller-gen
	$(CONTROLLER_GEN) object:headerFile="hack/boilerplate.go.txt" paths="./..."

.PHONY: manifests
manifests: controller-gen
	$(CONTROLLER_GEN) rbac:roleName=manager-role crd paths="./..." output:crd:artifacts:config=config/crd/bases output:rbac:artifacts:config=config/rbac

.PHONY: test
test:
	go test ./...

.PHONY: helm-chart
helm-chart: manifests
	mkdir -p $(CHART_CRD_DIR)
	cp $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functionapplications.yaml $(CHART_CRD_DIR)/functionapplications.functions.oci.oracle.com.yaml
	cp $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functions.yaml $(CHART_CRD_DIR)/functions.functions.oci.oracle.com.yaml
	cp $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functionjobs.yaml $(CHART_CRD_DIR)/functionjobs.functions.oci.oracle.com.yaml
	cp $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functionevents.yaml $(CHART_CRD_DIR)/functionevents.functions.oci.oracle.com.yaml
	cp $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functioneventtriggers.yaml $(CHART_CRD_DIR)/functioneventtriggers.functions.oci.oracle.com.yaml
	$(MAKE) helm-crds-check

.PHONY: helm-crds-check
helm-crds-check:
	test -f $(CHART_CRD_DIR)/functionapplications.functions.oci.oracle.com.yaml
	test -f $(CHART_CRD_DIR)/functions.functions.oci.oracle.com.yaml
	test -f $(CHART_CRD_DIR)/functionjobs.functions.oci.oracle.com.yaml
	test -f $(CHART_CRD_DIR)/functioneventtriggers.functions.oci.oracle.com.yaml
	test -f $(CHART_CRD_DIR)/functionevents.functions.oci.oracle.com.yaml
	cmp -s $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functionapplications.yaml $(CHART_CRD_DIR)/functionapplications.functions.oci.oracle.com.yaml
	cmp -s $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functions.yaml $(CHART_CRD_DIR)/functions.functions.oci.oracle.com.yaml
	cmp -s $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functionjobs.yaml $(CHART_CRD_DIR)/functionjobs.functions.oci.oracle.com.yaml
	cmp -s $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functioneventtriggers.yaml $(CHART_CRD_DIR)/functioneventtriggers.functions.oci.oracle.com.yaml
	cmp -s $(GENERATED_CRD_DIR)/functions.oci.oracle.com_functionevents.yaml $(CHART_CRD_DIR)/functionevents.functions.oci.oracle.com.yaml

.PHONY: helm-template
helm-template: helm-chart
	helm template oci-functions-operator charts/oci-functions-operator \
		--namespace oci-functions-operator-system

.PHONY: fmt
fmt:
	go fmt ./...

.PHONY: vet
vet:
	go vet ./...

.PHONY: controller-gen
controller-gen: $(CONTROLLER_GEN)

$(CONTROLLER_GEN):
	mkdir -p $(LOCALBIN)
	GOBIN=$(LOCALBIN) go install sigs.k8s.io/controller-tools/cmd/controller-gen@$(CONTROLLER_TOOLS_VERSION)
