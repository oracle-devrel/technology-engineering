enabled: false
replicaCount: 1
image:
  repository: __IMAGE_REPOSITORY__
  tag: __DEFAULT_TAG__
  pullPolicy: IfNotPresent
service:
  port: 80
  targetPort: 8080
resources:
  requests:
    cpu: 10m
    memory: 32Mi
  limits:
    cpu: 100m
    memory: 128Mi
