apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: __APP__-infrastructure
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-10"
  finalizers: [resources-finalizer.argocd.argoproj.io]
spec:
  project: platform
  source:
    repoURL: __CLUSTER_CONFIG_REPO_URL__
    targetRevision: HEAD
    path: platform/applications/__APP__/infrastructure/resources
  destination:
    server: https://kubernetes.default.svc
    namespace: __APP__
  syncPolicy:
    syncOptions: [CreateNamespace=true, ServerSideApply=true, ApplyOutOfSyncOnly=true, FailOnSharedResource=true, PruneLast=true]
    automated: {prune: true, selfHeal: true}
