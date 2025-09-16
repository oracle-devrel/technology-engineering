from graphviz import Digraph

# Create a directed graph
dot = Digraph()

# Define the nodes
dot.node('A', 'Upload Expense Claim PDF')
dot.node('B', 'Extract Data from PDF (LLM)')
dot.node('C', 'Policy Check\n(conformance to rules)')
dot.node('D', 'Category Check\n(mislabeling detection)')
dot.node('E', 'Declared Amount Check\n(vs backend/API)')
dot.node('F', 'Display Results\n(Green/Red Status)')

# Define the edges
dot.edge('A', 'B')
dot.edge('B', 'C')
dot.edge('C', 'D')
dot.edge('D', 'E')
dot.edge('E', 'F')

# Render to file
dot.format = 'png'
dot.render('expense_validation_flow', view=False)

print("✅ Flowchart generated: 'expense_validation_flow.png'")
