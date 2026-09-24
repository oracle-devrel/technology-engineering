replicaCount: 1
environment: ""
nameOverride: ""

application:
  name: ${application_name}

component:
  name: ${component_name}

image:
  repository: ghcr.io/oracle/oraclelinux
  tag: "9"
  pullPolicy: IfNotPresent

serviceAccount:
  name: ""
  automountToken: false
  imagePullSecrets:
    - name: ocirsecret

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    memory: 128Mi

service:
  port: 80
