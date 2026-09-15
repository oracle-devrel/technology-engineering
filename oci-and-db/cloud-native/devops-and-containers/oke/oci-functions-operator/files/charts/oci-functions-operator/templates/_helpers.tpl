{{/*
Expand the chart name.
*/}}
{{- define "oci-functions-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "oci-functions-operator.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-controller-manager" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "oci-functions-operator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels.
*/}}
{{- define "oci-functions-operator.labels" -}}
helm.sh/chart: {{ include "oci-functions-operator.chart" . }}
{{ include "oci-functions-operator.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end -}}

{{/*
Selector labels.
*/}}
{{- define "oci-functions-operator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "oci-functions-operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: manager
{{- end -}}

{{/*
Service account name.
*/}}
{{- define "oci-functions-operator.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "oci-functions-operator.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "oci-functions-operator-controller-manager" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
