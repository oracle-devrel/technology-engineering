{{/*
Expand the name of the chart.
*/}}
{{- define "protein-design-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "protein-design-chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "protein-design-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "protein-design-chart.labels" -}}
helm.sh/chart: {{ include "protein-design-chart.chart" . }}
{{ include "protein-design-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "protein-design-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "protein-design-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}


{{/*
Create secret to access docker registry
*/}}
{{- define "imagePullSecret" -}}
{{- $registry := .Values.imagePullSecret.registry -}}
{{- $secretName := .Values.imagePullSecret.secretName -}}
{{- $secretKey := .Values.imagePullSecret.secretKey -}}
{{- $secretNamespace := .Release.Namespace -}}

{{- $secret := lookup "v1" "Secret" $secretNamespace $secretName -}}
{{- if $secret -}}
  {{- $password := index $secret.data $secretKey | b64dec -}}
  {{- $auth := printf "%s:%s" .Values.imagePullSecret.username $password | b64enc -}}
  {{- printf "{\"auths\":{\"%s\":{\"auth\":\"%s\"}}}" $registry $auth | b64enc -}}
{{- else -}}
  {{- fail (printf "Secret %s not found in namespace %s" $secretName $secretNamespace) -}}
{{- end -}}
{{- end -}}

