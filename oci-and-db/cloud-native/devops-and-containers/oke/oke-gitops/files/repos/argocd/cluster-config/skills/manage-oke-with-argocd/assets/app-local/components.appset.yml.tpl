apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: __APP__-components
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "0"
spec:
  goTemplate: true
  goTemplateOptions: [missingkey=error]
  generators:
    - list:
        elements:
          - component: __COMPONENT__
            environment: __ENVIRONMENT__
            resourcesPath: applications/__APP__/kustomize/components/__COMPONENT__/environments/__ENVIRONMENT__
  template:
    metadata:
      name: '__APP__-{{ .component }}-{{ .environment }}'
      namespace: argocd
      finalizers: [resources-finalizer.argocd.argoproj.io]
    spec:
      project: applications
      source:
        repoURL: __APPS_CONFIG_REPO_URL__
        targetRevision: HEAD
        path: '{{ .resourcesPath }}'
      destination:
        server: https://kubernetes.default.svc
        namespace: __APP__
      syncPolicy:
        syncOptions: [ServerSideApply=true, ApplyOutOfSyncOnly=true, SkipDryRunOnMissingResource=true, FailOnSharedResource=true, PruneLast=true]
        automated: {prune: true, selfHeal: true}
