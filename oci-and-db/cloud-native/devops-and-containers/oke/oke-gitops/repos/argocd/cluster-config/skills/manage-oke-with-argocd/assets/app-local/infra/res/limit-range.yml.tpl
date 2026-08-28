apiVersion: v1
kind: LimitRange
metadata:
  name: __APP__-defaults
spec:
  limits:
    - type: Container
      defaultRequest: {cpu: 25m, memory: 64Mi}
      default: {cpu: 250m, memory: 256Mi}
