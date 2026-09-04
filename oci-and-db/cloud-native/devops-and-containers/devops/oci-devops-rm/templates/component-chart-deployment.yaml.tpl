apiVersion: apps/v1
kind: Deployment
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
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ .Values.application.name }}
      app.kubernetes.io/component: {{ .Values.component.name }}
      app.kubernetes.io/instance: {{ .Release.Name }}
      {{- if .Values.environment }}
      env: {{ .Values.environment }}
      {{- end }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ .Values.application.name }}
        app.kubernetes.io/component: {{ .Values.component.name }}
        app.kubernetes.io/instance: {{ .Release.Name }}
        {{- if .Values.environment }}
        env: {{ .Values.environment }}
        {{- end }}
    spec:
      serviceAccountName: {{ default (ternary (printf "%s-%s" .Values.component.name .Values.environment) .Values.component.name (and (ne .Values.environment "") (ne .Values.environment "prod"))) .Values.serviceAccount.name }}
      automountServiceAccountToken: false
      containers:
        - name: app
          {{- $imageTag := .Values.image.tag }}
          {{- if eq .Values.environment "prod" }}
          {{- $imageTag = regexReplaceAll "-rc\\.[0-9]+$" .Values.image.tag "" }}
          {{- end }}
          image: "{{ .Values.image.repository }}:{{ $imageTag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          command: ["/usr/bin/sleep", "31536000"]
          ports:
            - name: http
              containerPort: 8080
          resources:
            requests:
              cpu: {{ .Values.resources.requests.cpu | quote }}
              memory: {{ .Values.resources.requests.memory | quote }}
            limits:
              memory: {{ .Values.resources.limits.memory | quote }}
