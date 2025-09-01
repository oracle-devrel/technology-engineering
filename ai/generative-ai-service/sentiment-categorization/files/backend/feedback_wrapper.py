from backend.feedback_agent import FeedbackAgent


class FeedbackAgentWrapper:
    def __init__(self):
        self.agent = FeedbackAgent()
        self.run_graph = self.agent.run_step_by_step()

    def get_nodes_edges(self):
        graph_data = self.agent.get_graph()
        nodes = list(graph_data.nodes.keys())
        edges = [(edge.source, edge.target) for edge in graph_data.edges]
        return nodes, edges

    def run_step_by_step(self):
        try:
            action_output = next(self.run_graph)
            current_node = list(action_output.keys())[0]
        except StopIteration:
            action_output = {}
            current_node = "FINALIZED"
        return current_node, action_output

    def get_graph(self):
        return self.agent.get_graph()
