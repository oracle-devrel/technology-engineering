"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

json_file_analyzer_showoci.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import json
import argparse
from collections import OrderedDict, defaultdict

def get_type_name(value):
    """Returns a string representation of the value's type."""
    if isinstance(value, str):
        return "string"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "float"
    elif value is None:
        return "null"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        return type(value).__name__

def discover_json_structure_recursive(data, max_depth=5, current_depth=0):
    """
    Recursively discovers the structure of JSON data with depth limiting.
    """
    if isinstance(data, dict):
        if current_depth >= max_depth:
            return f"object (max depth {max_depth} reached - {len(data)} keys)"
        
        structure = OrderedDict()
        for key, value in data.items():
            structure[key] = discover_json_structure_recursive(value, max_depth, current_depth + 1)
        return structure
    elif isinstance(data, list):
        if not data:
            return "array (empty)"
        else:
            # Always try to show the structure of array elements
            first_element = data[0]
            
            # If it's an array of simple types, handle that
            if not isinstance(first_element, (dict, list)):
                element_type = get_type_name(first_element)
                # Check if all elements are the same simple type
                if all(get_type_name(item) == element_type for item in data[:min(5, len(data))]):
                    return f"array of {element_type}"
                else:
                    return "array of mixed simple types"
            
            # For complex types (objects/arrays), analyze structure
            element_structure = discover_json_structure_recursive(first_element, max_depth, current_depth + 1)
            
            # Check if other elements have similar structure (sample a few)
            sample_size = min(5, len(data))
            similar_structure = True
            
            if len(data) > 1:
                for i in range(1, sample_size):
                    other_structure = discover_json_structure_recursive(data[i], max_depth, current_depth + 1)
                    if not structures_are_similar(element_structure, other_structure):
                        similar_structure = False
                        break
            
            if similar_structure:
                return {
                    "_array_info": f"array of {len(data)} items",
                    "_element_structure": element_structure
                }
            else:
                return {
                    "_array_info": f"array of {len(data)} items (mixed structures)",
                    "_example_element": element_structure
                }
    else:
        return get_type_name(data)

def structures_are_similar(struct1, struct2):
    """Check if two structures are similar enough to be considered the same type."""
    if type(struct1) != type(struct2):
        return False
    
    if isinstance(struct1, dict) and isinstance(struct2, dict):
        # Consider similar if they have mostly the same keys
        keys1 = set(struct1.keys())
        keys2 = set(struct2.keys())
        common_keys = keys1 & keys2
        total_keys = keys1 | keys2
        
        # Similar if at least 70% of keys are common
        similarity = len(common_keys) / len(total_keys) if total_keys else 1
        return similarity >= 0.7
    
    return struct1 == struct2

def merge_structures(struct1, struct2):
    """
    Merge two structure representations, handling cases where the same field
    might have different types across different records of the same type.
    """
    if struct1 == struct2:
        return struct1
    
    if isinstance(struct1, dict) and isinstance(struct2, dict):
        merged = OrderedDict()
        all_keys = set(struct1.keys()) | set(struct2.keys())
        
        for key in all_keys:
            if key in struct1 and key in struct2:
                merged[key] = merge_structures(struct1[key], struct2[key])
            elif key in struct1:
                merged[key] = f"{struct1[key]} (optional)"
            else:
                merged[key] = f"{struct2[key]} (optional)"
        
        return merged
    else:
        # If structures are different and not both dicts, show both possibilities
        return f"{struct1} | {struct2}"

def analyze_json_by_type(data, max_depth=5):
    """
    Analyze JSON data grouped by 'type' field.
    
    Args:
        data: List of dictionaries, each containing 'type' and 'data' fields
        max_depth: Maximum depth for structure analysis
        
    Returns:
        Dictionary mapping type names to their data structures
    """
    if not isinstance(data, list):
        raise ValueError("Expected JSON data to be a list of objects")
    
    type_structures = {}
    type_counts = defaultdict(int)
    
    for item in data:
        if not isinstance(item, dict):
            print(f"Warning: Found non-dict item: {type(item)}")
            continue
            
        if 'type' not in item:
            print(f"Warning: Found item without 'type' field: {list(item.keys())}")
            continue
            
        if 'data' not in item:
            print(f"Warning: Found item without 'data' field for type '{item['type']}'")
            continue
        
        item_type = item['type']
        item_data = item['data']
        type_counts[item_type] += 1
        
        # Discover structure of this item's data
        current_structure = discover_json_structure_recursive(item_data, max_depth)
        
        # If we've seen this type before, merge structures
        if item_type in type_structures:
            type_structures[item_type] = merge_structures(
                type_structures[item_type], 
                current_structure
            )
        else:
            type_structures[item_type] = current_structure
    
    return type_structures, dict(type_counts)

def print_dict_structure(struct, indent=0, max_line_length=120):
    """Print dictionary structure with proper indentation and special handling for arrays."""
    spaces = " " * indent
    if isinstance(struct, dict):
        # Special handling for array structures
        if "_array_info" in struct:
            print(f"{spaces}{struct['_array_info']}")
            if "_element_structure" in struct:
                print(f"{spaces}Each element has structure:")
                print_dict_structure(struct["_element_structure"], indent + 2, max_line_length)
            elif "_example_element" in struct:
                print(f"{spaces}Example element structure:")
                print_dict_structure(struct["_example_element"], indent + 2, max_line_length)
            return
        
        # Normal object structure
        print(f"{spaces}{{")
        for i, (key, value) in enumerate(struct.items()):
            comma = "," if i < len(struct) - 1 else ""
            if isinstance(value, dict):
                if "_array_info" in value:
                    # Special compact display for arrays
                    print(f"{spaces}  \"{key}\": {value['_array_info']}")
                    if "_element_structure" in value:
                        print(f"{spaces}    Each element:")
                        print_dict_structure(value["_element_structure"], indent + 6, max_line_length)
                    elif "_example_element" in value:
                        print(f"{spaces}    Example element:")
                        print_dict_structure(value["_example_element"], indent + 6, max_line_length)
                    if comma:
                        print(f"{spaces}  ,")
                else:
                    print(f"{spaces}  \"{key}\": {{")
                    print_dict_structure(value, indent + 4, max_line_length)
                    print(f"{spaces}  }}{comma}")
            else:
                # Handle simple values and other types
                value_str = format_value_string(value, max_line_length - indent - len(key) - 6)
                print(f"{spaces}  \"{key}\": {value_str}{comma}")
        print(f"{spaces}}}")
    else:
        formatted_value = format_value_string(struct, max_line_length - indent)
        print(f"{spaces}{formatted_value}")

def format_value_string(value, max_length=80):
    """Format a value string with appropriate truncation and cleaning."""
    value_str = str(value)
    
    # Clean up common patterns
    value_str = value_str.replace("OrderedDict(", "").replace("})", "}")
    
    # For array descriptions, make them more readable
    if value_str.startswith("array of ") or value_str.startswith("array ("):
        # Keep array descriptions intact but clean them up
        if len(value_str) > max_length:
            # Find a good break point
            if "," in value_str and len(value_str) > max_length:
                parts = value_str.split(",")
                truncated = parts[0]
                if len(truncated) < max_length - 10:
                    truncated += ", ..."
                value_str = truncated
            else:
                value_str = value_str[:max_length-3] + "..."
    else:
        # For other long strings, truncate normally
        if len(value_str) > max_length:
            value_str = value_str[:max_length-3] + "..."
    
    return value_str

def print_type_analysis(type_structures, type_counts, filter_types=None):
    """Print the analysis results in a readable format."""
    print("=" * 80)
    print("JSON STRUCTURE ANALYSIS BY TYPE")
    print("=" * 80)
    
    # Filter if requested
    if filter_types:
        filter_set = set(filter_types)
        type_structures = {k: v for k, v in type_structures.items() if k in filter_set}
        type_counts = {k: v for k, v in type_counts.items() if k in filter_set}
    
    print(f"\nFound {len(type_structures)} different types:")
    for type_name in sorted(type_counts.keys()):
        print(f"  - {type_name}: {type_counts[type_name]} record(s)")
    
    if not filter_types:
        print("\n" + "=" * 80)
        print("TIP: Use --type-filter to focus on specific types for detailed analysis")
        print("     Example: --type-filter \"identity,showoci\"")
    
    print("\n" + "=" * 80)
    
    for type_name in sorted(type_structures.keys()):
        structure = type_structures[type_name]
        print(f"\nTYPE: {type_name}")
        print(f"Records: {type_counts[type_name]}")
        print("-" * 60)
        print("Data structure:")
        
        # Pretty print with better formatting
        if isinstance(structure, dict):
            print_dict_structure(structure, indent=2)
        else:
            print(f"  {structure}")
            
        # Show field count for complex structures
        if isinstance(structure, dict):
            print(f"  → {len(structure)} top-level fields")
        print()

def show_sample_data(data, sample_type, max_items=1):
    """Show sample data for a specific type."""
    print("=" * 80)
    print(f"SAMPLE DATA FOR TYPE: {sample_type}")
    print("=" * 80)
    
    count = 0
    for item in data:
        if isinstance(item, dict) and item.get('type') == sample_type:
            print(f"\nSample {count + 1}:")
            print("-" * 40)
            sample_data = json.dumps(item['data'], indent=2)
            if len(sample_data) > 2000:
                lines = sample_data.split('\n')
                truncated = '\n'.join(lines[:50])
                print(f"{truncated}\n... (truncated - showing first 50 lines)")
            else:
                print(sample_data)
            
            count += 1
            if count >= max_items:
                break
    
    if count == 0:
        print(f"No records found for type '{sample_type}'")

def main():
    """
    Main function to parse arguments, read JSON file, analyze by type,
    and print the results.
    """
    parser = argparse.ArgumentParser(
        description="Analyze JSON file structure grouped by 'type' field."
    )
    parser.add_argument("json_file", help="Path to the JSON file to analyze.")
    parser.add_argument(
        "--max-depth", 
        type=int,
        default=4,
        help="Maximum depth to analyze nested structures (default: 4)"
    )
    parser.add_argument(
        "--type-filter",
        help="Only analyze specific type(s), comma-separated"
    )
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="Just list all available types and exit"
    )
    parser.add_argument(
        "--sample",
        help="Show sample data for a specific type"
    )
    
    args = parser.parse_args()

    try:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f, object_pairs_hook=OrderedDict)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON file. {e}")
                return

        print(f"Analyzing file: {args.json_file}")
        
        type_structures, type_counts = analyze_json_by_type(data, args.max_depth)
        
        # List types mode
        if args.list_types:
            print("\nAvailable types/sections:")
            for type_name in sorted(type_counts.keys()):
                print(f"  - {type_name} ({type_counts[type_name]} records)")
            return
        
        # Sample data mode
        if args.sample:
            show_sample_data(data, args.sample)
            return
        
        # Filter by type if specified
        filter_types = None
        if args.type_filter:
            filter_types = [t.strip() for t in args.type_filter.split(',')]
            print(f"Filtering to types: {', '.join(filter_types)}")
        
        print_type_analysis(type_structures, type_counts, filter_types=filter_types)
        
        # Additional analysis info
        print("=" * 80)
        print("USAGE TIPS:")
        print(f"- Use --list-types to see all available types")
        print(f"- Use --type-filter \"type1,type2\" to focus on specific types")
        print(f"- Use --sample \"type_name\" to see actual sample data")
        print(f"- Use --max-depth N to control analysis depth (current: {args.max_depth})")

    except FileNotFoundError:
        print(f"Error: File not found at {args.json_file}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()