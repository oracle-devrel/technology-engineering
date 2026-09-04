apiVersion: v1
kind: Service
metadata:
  name: {{ default (ternary (printf "%s-%s" .Values.component.name .Values.environment) .Values.component.name (and (ne .Values.environment "") (ne .Values.environment "prod"))) .Values.nameOverride }}
  labels:
    app.kubernetes.io/name: {{ .Values.application.name }}
    app.kubernetes.io/component: {{ .Values.component.name }}
    app.kubernetes.io/instance: {{ .Release.Name }}
    {{- if .Values.environment }}
    env: {{ .Values.environment }}
    {{- end }}
spec:
  selector:
    app.kubernetes.io/name: {{ .Values.application.name }}
    app.kubernetes.io/component: {{ .Values.component.name }}
    app.kubernetes.io/instance: {{ .Release.Name }}
    {{- if .Values.environment }}
    env: {{ .Values.environment }}
    {{- end }}
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
