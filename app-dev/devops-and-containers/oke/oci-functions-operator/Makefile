LOCALBIN ?= $(shell pwd)/bin
CONTROLLER_GEN ?= $(LOCALBIN)/controller-gen
CONTROLLER_TOOLS_VERSION ?= v0.21.0

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
	mkdir -p charts/oci-functions-operator/crds
	cp config/crd/bases/functions.oci.oracle.com_functions.yaml charts/oci-functions-operator/crds/functions.functions.oci.oracle.com.yaml
	cp config/crd/bases/functions.oci.oracle.com_functionjobs.yaml charts/oci-functions-operator/crds/functionjobs.functions.oci.oracle.com.yaml
	cp config/crd/bases/functions.oci.oracle.com_functionevents.yaml charts/oci-functions-operator/crds/functionevents.functions.oci.oracle.com.yaml
	cp config/crd/bases/functions.oci.oracle.com_functioneventtriggers.yaml charts/oci-functions-operator/crds/functioneventtriggers.functions.oci.oracle.com.yaml

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
