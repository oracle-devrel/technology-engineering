environment: "${environment}"
application:
  name: "${application_chart_name}"
component:
  name: "${component_name}"
image:
  repository: "$${image_repository}"
  tag: "$${${image_tag_parameter}}"
