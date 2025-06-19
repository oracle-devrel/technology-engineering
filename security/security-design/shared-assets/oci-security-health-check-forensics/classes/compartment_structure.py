"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

commpartment_structure.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
class HCCompartmentStructure:
    def __init__(self, compartments):
        self.compartments = [comp.strip() for comp in compartments]

    def get_root_compartment(self):
        for comp in self.compartments:
            if "(root)" in comp:
                return comp
        return None

    def get_depth(self):
        root_depth = 1
        max_depth = max(len(comp.split('/')) for comp in self.compartments)
        return max_depth + root_depth

    def get_sub_compartments_root(self):
        return self.get_compartments_by_depth(1)

    def get_sub_compartments(self, target_compartment):
        sub_compartments = set() # make unique

        for compartment in self.compartments:
            if "(root)" in compartment:
                continue
        
            parts = compartment.split(" / ")
            if target_compartment in parts:
                index = parts.index(target_compartment)
                if index + 1 < len(parts):
                    sub_compartments.add(parts[index + 1])
        return list(sub_compartments)

    def get_compartments_by_depth(self, depth):
        root_compartment = self.get_root_compartment()
        compartments_at_depth = set()
    
        for compartment in self.compartments:
            if root_compartment in compartment:
                continue
            parts = compartment.split(" / ")
        
            if len(parts) >= depth:
                compartments_at_depth.add(parts[depth - 1])
    
        return sorted(compartments_at_depth)

    def get_comp_tree(self):
        tree = self.__build_tree(self.compartments)
        return self.__print_tree(tree)

    def __build_tree(self, paths):
        tree = {}
        root = self.get_root_compartment()
        tree[root] = {}

        for path in paths:
            if path == root:
                continue
            parts = path.split('/')
            current = tree[root]
            for part in parts:
                part = part.strip()
                if part not in current:
                    current[part] = {}
                current = current[part]
        return tree

    def __print_tree(self, tree, prefix=''):
        tree_str = ""
        for idx, (key, value) in enumerate(sorted(tree.items())):
            connector = "└── " if idx == len(tree) - 1 else "├── "
            tree_str += f"{prefix}{connector}{key}\n"
            if value:
                extension = "    " if idx == len(tree) - 1 else "│   "
                tree_str += self.__print_tree(value, prefix + extension)
        return tree_str

    def get_path_to(self, target_compartment):
        """
        Return a list of all full paths from the root compartment 
        down to compartments whose name == `target_compartment`.
    
        Each path keeps the root compartment name, including '(root)', intact.
        Example for 'acme-appdev-cmp':
            ["/iosociiam (root)/acme-top-cmp/acme-appdev-cmp"]
        """
        # 1) Build the tree from your existing compartments
        tree = self.__build_tree(self.compartments)

        # 2) Identify the root compartment key (e.g. "/ iosociiam (root)")
        root_key = self.get_root_compartment()
        if root_key not in tree:
            raise ValueError("Root compartment not found in the tree.")

        # Clean up leading/trailing spaces but **do not remove '(root)'**.
        # For instance, if root_key is "/ <root-comp> (root)",
        # `strip()` will remove extra leading/trailing whitespace but keep "(root)".
        # If it starts with '/', we'll remove only that one slash so that
        # the final path can start with a single slash.
        cleaned_root = root_key.strip()
        if cleaned_root.startswith("/"):
            cleaned_root = cleaned_root[1:].strip()

        # Store any matching full paths in a list
        results = []

        def dfs(subtree, path_so_far):
            """
            Depth-First Search through the compartment hierarchy.
            subtree: the nested dictionary for the current node
            path_so_far: list of compartment names from the root down to this node
            """
            for child_name, child_subtree in subtree.items():
                # Clean the child but DO NOT remove '(root)'
                child_clean = child_name.strip()
            
                new_path = path_so_far + [child_clean]
            
                # If this child matches target_compartment, record the full path
                if child_clean == target_compartment:
                    # Build final path. Example:
                    # path_so_far = ["iosociiam (root)", "acme-top-cmp"]
                    # child_clean = "acme-appdev-cmp"
                    # => "/iosociiam (root)/acme-top-cmp/acme-appdev-cmp"
                    full_path = " / " + " / ".join(new_path)
                    results.append(full_path)

                # Recur into the child node
                dfs(child_subtree, new_path)

        # 3) Start DFS from the root's subtree, using [cleaned_root] as the path
        dfs(tree[root_key], [cleaned_root])

        # 4) If no matches, raise an error
        if not results:
            raise ValueError(f"Compartment '{target_compartment}' not found.")

        return results


    """
        This is to handle the different subcommands from the CLI filter compartment command.
    """
    def handle_request(self, request, *args):
        if request == "get_root_compartment":
            return self.get_root_compartment()
        elif request == "get_max_depth":
            return self.get_depth()
        elif request == "get_sub_compartments_root":
            return self.get_sub_compartments_root()
        elif request == "get_tree_view":
            return self.get_comp_tree()
        elif request == "get_sub_compartments":
            if args:
                return self.get_sub_compartments(args[0])
            else:
                raise ValueError("Compartment name required for 'get_sub_compartments' request.")
        elif request == "get_compartments_at_depth":
            if args:
                return self.get_compartments_by_depth(int(args[0]))
            else:
                raise ValueError("Depth value required for 'get_compartments_at_depth' request.")
        else:
            raise ValueError("Invalid request.")
