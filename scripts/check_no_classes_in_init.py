#!/usr/bin/env python3
"""
Pre-commit hook to disallow class or function definitions in __init__.py files.

Checks each __init__.py file for class, function, or async function definitions and
exits with an error if any are found.
"""

import ast
import os
import sys


def is_complex_assignment(value: ast.AST) -> tuple[bool, str]:
    """Check if the assignment value is a disallowed complex expression."""
    match value:
        case ast.Lambda():
            return True, "lambda expression"
        case ast.ListComp():
            return True, "list comprehension"
        case ast.DictComp():
            return True, "dictionary comprehension"
        case ast.SetComp():
            return True, "set comprehension"
        case ast.GeneratorExp():
            return True, "generator expression"
        case _:
            return False, ""


def has_disallowed_definitions(code: str) -> tuple[bool, str]:
    """Check if the code contains class, function, or async function definitions.

    Args:
        code (str): The source code to check.

    Returns:
        tuple[bool, str]: A tuple containing (has_violation, violation_details)
                          where violation_details is empty if no violation is found.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        # Well, if we can't parse the file, we can't forbid anything
        print(f"[WARNING] Syntax error in file: {e}")
        return False, ""

    for node in tree.body:
        match node:
            # Check for direct class/function definitions
            case ast.ClassDef(name=name):
                return True, f"class '{name}'"
            case ast.FunctionDef(name=name):
                return True, f"function '{name}'"
            case ast.AsyncFunctionDef(name=name):
                return True, f"async function '{name}'"
            # Check for complex assignments that might contain logic
            case ast.Assign(value=value):
                has_complex, detail = is_complex_assignment(value)
                if has_complex:
                    return True, detail
            # Check for other control flow structures
            case ast.If() | ast.For() | ast.While() | ast.Try() | ast.With():
                return True, f"control flow structure: {node.__class__.__name__}"

    return False, ""


def main():
    """
    Main entry point. Checks all provided __init__.py files for disallowed definitions.

    Returns:
        int: Exit code (0 if all files are clean, 1 if any file contains disallowed
             definitions).
    """
    exit_code = 0
    for file_path in sys.argv[1:]:
        if os.path.basename(file_path) != "__init__.py":
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
        except (IOError, OSError) as e:
            print(f"[ERROR] Could not read file {file_path}: {e}")
            exit_code = 1
            continue

        has_violation, violation_details = has_disallowed_definitions(code)
        if has_violation:
            print(
                f"[ERROR] {file_path} "
                f"contains disallowed construct: {violation_details}"
            )
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
