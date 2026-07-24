apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ default (ternary (printf "%s-%s" .Values.component.name .Values.environment) .Values.component.name (and (ne .Values.environment "") (ne .Values.environment "prod"))) .Values.serviceAccount.name }}
  labels:
    app.kubernetes.io/name: {{ .Values.application.name }}
    app.kubernetes.io/component: {{ .Values.component.name }}
    app.kubernetes.io/instance: {{ .Release.Name }}
    {{- if .Values.environment }}
    env: {{ .Values.environment }}
    {{- end }}
automountServiceAccountToken: {{ .Values.serviceAccount.automountToken }}
{{- with .Values.serviceAccount.imagePullSecrets }}
imagePullSecrets:
{{- range . }}
  - name: {{ .name }}
{{- end }}
{{- end }}
