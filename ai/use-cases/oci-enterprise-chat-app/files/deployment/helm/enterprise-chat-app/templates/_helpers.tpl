{{/*
Full image path for a component.
Usage: {{ include "enterprise-chat-app.image" (dict "registry" .Values.registry "image" .Values.backend.image) }}
*/}}
{{- define "enterprise-chat-app.image" -}}
{{ .registry.server }}/{{ .registry.repository }}/{{ .image.name }}:{{ .image.tag }}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "enterprise-chat-app.labels" -}}
app.kubernetes.io/part-of: enterprise-chat-app
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{/*
CORS origins — includes the ingress controller external IP if available
*/}}
{{- define "enterprise-chat-app.corsOrigins" -}}
http://frontend-service.{{ .Values.namespace }}.svc.cluster.local
{{- end -}}
