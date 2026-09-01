apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - resourceset.yml
configMapGenerator:
  - name: __APP__-values
    namespace: flux-system
    files:
      - 00-base.yaml=values/00-base.yml
      - 90-user.yaml=values/90-user.yml
generatorOptions:
  disableNameSuffixHash: true
