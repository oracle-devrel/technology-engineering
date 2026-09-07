apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: fleet-__PROFILE__
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: fleet-config
  path: ./profiles/__PROFILE__
  prune: true
  wait: true
  timeout: 5m
