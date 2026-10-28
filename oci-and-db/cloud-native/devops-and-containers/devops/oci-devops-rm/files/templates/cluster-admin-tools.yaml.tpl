clusters:
  noprod: ${jsonencode(noprod_cluster_name)}
  prod: ${jsonencode(prod_cluster_name)}
tools: ${length(tools) == 0 ? "{}" : ""}
%{ for tool in tools ~}
  ${tool.name}:
    repository: ${jsonencode(tool.repository)}
    chart: ${jsonencode(tool.chart)}
    version: ${jsonencode(tool.version)}
%{ endfor ~}
