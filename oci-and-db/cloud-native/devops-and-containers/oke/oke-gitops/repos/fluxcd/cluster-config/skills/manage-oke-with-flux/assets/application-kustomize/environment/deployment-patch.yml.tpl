apiVersion: apps/v1
kind: Deployment
metadata:
  name: __COMPONENT__
spec:
  template:
    spec:
      containers:
        - name: __COMPONENT__
          env:
            - name: APP_ENVIRONMENT
              value: __ENVIRONMENT__
