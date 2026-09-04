{{- define "__COMPONENT__.fullname" -}}
{{- printf "%s-%s" .Release.Name "__COMPONENT__" | trunc 63 | trimSuffix "-" -}}
{{- end -}}
