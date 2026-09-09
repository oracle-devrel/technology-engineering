apiVersion: v1
kind: Service
metadata:
  name: __COMPONENT__
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: __APP__
    app.kubernetes.io/component: __COMPONENT__
  ports:
    - name: http
      port: 80
      targetPort: http
