apiVersion: apps/v1
kind: Deployment
metadata:
  name: __COMPONENT__
  labels:
    app.kubernetes.io/name: __APP__
    app.kubernetes.io/part-of: __APP__
    app.kubernetes.io/component: __COMPONENT__
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: __APP__
      app.kubernetes.io/component: __COMPONENT__
  template:
    metadata:
      labels:
        app.kubernetes.io/name: __APP__
        app.kubernetes.io/part-of: __APP__
        app.kubernetes.io/component: __COMPONENT__
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: __COMPONENT__
          image: __IMAGE_REPOSITORY__:__DEFAULT_TAG__
          ports:
            - name: http
              containerPort: __CONTAINER_PORT__
          resources:
            requests:
              cpu: 10m
              memory: 32Mi
            limits:
              cpu: 100m
              memory: 128Mi
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: [ALL]
