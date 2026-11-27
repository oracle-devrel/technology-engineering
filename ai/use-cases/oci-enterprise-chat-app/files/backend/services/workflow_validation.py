"""Graph rules shared by persistence and execution."""

from collections import defaultdict, deque


def execution_order(nodes, edges):
    node_map = {node.id: node for node in nodes}
    if len(node_map) != len(nodes):
        raise ValueError("Node IDs must be unique")
    if len({edge.id for edge in edges}) != len(edges):
        raise ValueError("Edge IDs must be unique")
    if sum(node.type == "chat" for node in nodes) > 1:
        raise ValueError("Only one Chat block is allowed")
    allowed = {
        "input": {"agent", "data_source", "output"},
        "agent": {"agent", "data_source", "output", "chat"},
        "data_source": {"agent", "output"},
        "output": {"chat"},
        "chat": {"agent"},
    }
    degree = dict.fromkeys(node_map, 0)
    adjacent = defaultdict(list)
    connections = set()
    for edge in edges:
        if edge.source not in node_map or edge.target not in node_map:
            raise ValueError("Connection references a non-existent node")
        if edge.source == edge.target:
            raise ValueError("A node cannot connect to itself")
        pair = (edge.source, edge.target)
        if pair in connections:
            raise ValueError("Duplicate connection")
        connections.add(pair)
        if node_map[edge.target].type not in allowed[node_map[edge.source].type]:
            raise ValueError("Illegal connection between node types")
        degree[edge.target] += 1
        adjacent[edge.source].append(edge.target)
    queue = deque(key for key, count in degree.items() if count == 0)
    order = []
    while queue:
        key = queue.popleft()
        order.append(key)
        for target in adjacent[key]:
            degree[target] -= 1
            if degree[target] == 0:
                queue.append(target)
    if len(order) != len(nodes):
        raise ValueError("Workflow graph contains a cycle")
    return order
