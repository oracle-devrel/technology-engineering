apiVersion: v2
name: __APP__
description: Umbrella chart for __APP__
type: application
version: 0.1.0
dependencies:
  - name: __COMPONENT__
    version: 0.1.0
    repository: file://charts/__COMPONENT__
    condition: __COMPONENT__.enabled
