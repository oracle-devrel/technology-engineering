apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: __APP__
nameSuffix: -__ENVIRONMENT__

resources:
  - ../../base

images:
  - name: __IMAGE_REPOSITORY__
    newTag: __IMAGE_TAG__

labels:
  - includeSelectors: true
    pairs:
      app.kubernetes.io/instance: __APP__-__ENVIRONMENT__
      app.kubernetes.io/environment: __ENVIRONMENT__

patches:
  - path: deployment-patch.yml
