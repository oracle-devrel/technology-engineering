{{- define "frontend.labels" -}}
app.kubernetes.io/name: {{ .Values.global.application | quote }}
app.kubernetes.io/component: {{ .Values.global.component | quote }}
app.kubernetes.io/instance: {{ .Values.global.instance | quote }}
app.kubernetes.io/environment: {{ .Values.global.environment | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
{{- end }}
