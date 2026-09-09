name: __APP__
namespace: __NAMESPACE__
helm:
  repository: __HELM_REPOSITORY__
  chart: __CHART__
  version: __VERSION__
  releaseName: __RELEASE__
  valueFiles:
    - values/00-base.yml
    - values/90-user.yml
resourcesPath: platform/applications/__APP__/resources
