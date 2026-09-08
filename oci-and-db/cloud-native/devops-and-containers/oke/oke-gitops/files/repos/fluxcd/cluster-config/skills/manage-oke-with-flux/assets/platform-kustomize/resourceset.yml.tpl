apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: __APP__
  namespace: flux-system
spec:
  inputs:
    - name: __APP__
      namespace: __NAMESPACE__
      resourcesPath: ./platform/applications/__APP__/resources
  resources:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: << inputs.namespace >>
    - apiVersion: kustomize.toolkit.fluxcd.io/v1
      kind: Kustomization
      metadata:
        name: << inputs.name >>
        namespace: flux-system
      spec:
        interval: 5m
        sourceRef:
          kind: GitRepository
          name: flux-system
        path: << inputs.resourcesPath >>
        targetNamespace: << inputs.namespace >>
        prune: true
        wait: true
        timeout: 3m
