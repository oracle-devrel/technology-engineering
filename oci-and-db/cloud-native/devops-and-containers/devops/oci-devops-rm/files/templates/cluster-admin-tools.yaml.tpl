tools:
%{ for tool in tools ~}
  ${tool.name}:
    repository: ${jsonencode(tool.repository)}
    chart: ${jsonencode(tool.chart)}
    version: ${jsonencode(tool.version)}
%{ endfor ~}
