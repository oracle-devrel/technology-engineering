{{- if .Values.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "__COMPONENT__.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ .Values.global.application }}
    app.kubernetes.io/component: {{ .Values.global.component }}
    app.kubernetes.io/instance: {{ .Values.global.instance }}
    app.kubernetes.io/environment: {{ .Values.global.environment }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/instance: {{ .Values.global.instance }}
      app.kubernetes.io/component: {{ .Values.global.component }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ .Values.global.application }}
        app.kubernetes.io/component: {{ .Values.global.component }}
        app.kubernetes.io/instance: {{ .Values.global.instance }}
        app.kubernetes.io/environment: {{ .Values.global.environment }}
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: __COMPONENT__
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: [ALL]
{{- end }}
