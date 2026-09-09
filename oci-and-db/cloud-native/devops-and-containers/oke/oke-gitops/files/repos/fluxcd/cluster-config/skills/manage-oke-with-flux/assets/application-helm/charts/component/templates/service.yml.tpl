{{- if .Values.enabled }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "__COMPONENT__.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ .Values.global.application }}
    app.kubernetes.io/component: {{ .Values.global.component }}
    app.kubernetes.io/instance: {{ .Values.global.instance }}
    app.kubernetes.io/environment: {{ .Values.global.environment }}
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/instance: {{ .Values.global.instance }}
    app.kubernetes.io/component: {{ .Values.global.component }}
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
{{- end }}
