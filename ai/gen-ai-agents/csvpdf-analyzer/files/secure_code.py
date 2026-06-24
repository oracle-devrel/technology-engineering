"""
Secure code analyzer

analyze the generated code to identify unwanted, harmful code
"""

import ast
from utils import get_console_logger

# Define blocked imports and functions
BLOCKED_IMPORTS = {"os", "shutil", "subprocess", "pathlib", "pickle"}
BLOCKED_FUNCTIONS = {
    "open",
    "exec",
    "eval",
    "compile",
    "os.system",
    "os.remove",
    "os.rmdir",
    "shutil.rmtree",
    "subprocess.run",
    "subprocess.call",
    "pickle.load",
    "pickle.loads",
}

logger = get_console_logger()


def analyze_code(code_string):
    """
    analyze to detect harmful code
    """
    try:
        # Convert code into AST
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return f"❌ Syntax Error: {e}"

    warnings = []

    for node in ast.walk(tree):  # Walk through the AST
        # Check for banned imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in BLOCKED_IMPORTS:
                    warnings.append(f"🚨 Blocked Import: {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            if node.module in BLOCKED_IMPORTS:
                warnings.append(f"🚨 Blocked Import: {node.module}")

        # Check for banned function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_FUNCTIONS:
                warnings.append(f"🚨 Blocked Function Call: {node.func.id}()")
            elif isinstance(node.func, ast.Attribute):
                full_func_name = (
                    f"{node.func.value.id}.{node.func.attr}"
                    if isinstance(node.func.value, ast.Name)
                    else node.func.attr
                )
                if full_func_name in BLOCKED_FUNCTIONS:
                    warnings.append(f"🚨 Blocked Function Call: {full_func_name}()")

    return warnings if warnings else "✅ No security issues detected."
