apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: __APP__
  namespace: flux-system
spec:
  dependsOn:
    - apiVersion: v1
      kind: ConfigMap
      name: __APP__-values
      namespace: flux-system
  inputs:
    - name: __APP__
      namespace: __NAMESPACE__
      chart: __CHART__
      version: __CHART_VERSION__
      repository: __HELM_REPOSITORY__
      valuesFrom:
        - kind: ConfigMap
          name: __APP__-values
          valuesKey: 00-base.yaml
        - kind: ConfigMap
          name: __APP__-values
          valuesKey: 90-user.yaml
  resources:
    - apiVersion: v1
      kind: Namespace
      metadata:
        name: << inputs.namespace >>
    - apiVersion: source.toolkit.fluxcd.io/v1
      kind: HelmRepository
      metadata:
        name: << inputs.name >>
        namespace: flux-system
      spec:
        interval: 30m
        url: << inputs.repository >>
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      metadata:
        name: << inputs.name >>
        namespace: flux-system
      spec:
        interval: 30m
        releaseName: << inputs.name >>
        targetNamespace: << inputs.namespace >>
        chart:
          spec:
            chart: << inputs.chart >>
            version: << inputs.version | quote >>
            sourceRef:
              kind: HelmRepository
              name: << inputs.name >>
        valuesFrom: << inputs.valuesFrom | toYaml | nindent 10 >>
