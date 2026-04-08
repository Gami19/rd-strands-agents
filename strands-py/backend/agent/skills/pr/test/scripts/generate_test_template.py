#!/usr/bin/env python3
"""Test Template Generator - test skill execution script.

Generates test file templates based on Khorikov's 4-pillar methodology.
Reads a source file (Python or TypeScript), extracts public function/method
signatures, and produces a test template with AAA pattern structure.

Usage:
    python generate_test_template.py <source_file> [--framework pytest|jest|vitest] [--output test_file]

Examples:
    # Python file with pytest (default)
    python generate_test_template.py src/calculator.py

    # TypeScript file with vitest
    python generate_test_template.py src/userService.ts --framework vitest

    # Specify output location
    python generate_test_template.py src/auth.py --output tests/test_auth.py
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_FRAMEWORKS: list[str] = ["pytest", "jest", "vitest"]

# Regex patterns for TypeScript extraction (simple, not full parse)
TS_FUNCTION_PATTERN: re.Pattern[str] = re.compile(
    r"^export\s+(?:async\s+)?function\s+(\w+)\s*"
    r"(?:<[^>]*>)?\s*"  # Optional generic
    r"\(([^)]*)\)"  # Parameters
    r"(?:\s*:\s*([^{]+))?"  # Optional return type
    r"\s*\{",
    re.MULTILINE,
)

TS_ARROW_PATTERN: re.Pattern[str] = re.compile(
    r"^export\s+const\s+(\w+)\s*"
    r"(?::\s*[^=]+)?\s*=\s*"  # Optional type annotation
    r"(?:async\s+)?"
    r"(?:\([^)]*\)|(\w+))"  # Parameters or single param
    r"(?:\s*:\s*[^=]+)?\s*"  # Optional return type
    r"=>\s*",
    re.MULTILINE,
)

TS_METHOD_PATTERN: re.Pattern[str] = re.compile(
    r"^\s+(?:public\s+)?(?:async\s+)?(\w+)\s*"
    r"(?:<[^>]*>)?\s*"  # Optional generic
    r"\(([^)]*)\)"  # Parameters
    r"(?:\s*:\s*([^{]+))?"  # Optional return type
    r"\s*\{",
    re.MULTILINE,
)

TS_CLASS_PATTERN: re.Pattern[str] = re.compile(
    r"^export\s+(?:abstract\s+)?class\s+(\w+)",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Parameter:
    """A function/method parameter."""

    name: str
    type_hint: str = ""
    default: str = ""
    is_optional: bool = False


@dataclass
class FunctionInfo:
    """Extracted information about a function or method."""

    name: str
    params: list[Parameter] = field(default_factory=list)
    return_type: str = ""
    is_async: bool = False
    is_method: bool = False
    class_name: str = ""
    is_static: bool = False
    is_classmethod: bool = False
    docstring: str = ""


# ---------------------------------------------------------------------------
# Python AST extraction
# ---------------------------------------------------------------------------


def extract_python_functions(source_path: Path) -> list[FunctionInfo]:
    """Extract public function and method signatures from a Python file.

    Uses the ast module for reliable parsing. Skips private functions
    (names starting with underscore) and dunder methods other than __init__.

    Args:
        source_path: Path to the Python source file.

    Returns:
        List of FunctionInfo objects.

    Raises:
        SyntaxError: If the Python file has syntax errors.
    """
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))

    functions: list[FunctionInfo] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            # Skip private functions (but allow __init__)
            if node.name.startswith("_") and node.name != "__init__":
                continue

            # Determine if this is a method (inside a class)
            class_name = ""
            is_method = False
            is_static = False
            is_classmethod = False

            for parent in ast.walk(tree):
                if isinstance(parent, ast.ClassDef):
                    for child in ast.iter_child_nodes(parent):
                        if child is node:
                            class_name = parent.name
                            is_method = True
                            break

            # Check decorators for static/classmethod
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    if decorator.id == "staticmethod":
                        is_static = True
                    elif decorator.id == "classmethod":
                        is_classmethod = True

            # Extract parameters
            params = _extract_python_params(node.args, is_method, is_classmethod)

            # Extract return type
            return_type = ""
            if node.returns:
                return_type = ast.unparse(node.returns)

            # Extract docstring
            docstring = ast.get_docstring(node) or ""

            functions.append(FunctionInfo(
                name=node.name,
                params=params,
                return_type=return_type,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                is_method=is_method,
                class_name=class_name,
                is_static=is_static,
                is_classmethod=is_classmethod,
                docstring=docstring,
            ))

    return functions


def _extract_python_params(
    args: ast.arguments,
    is_method: bool,
    is_classmethod: bool,
) -> list[Parameter]:
    """Extract parameters from a Python function's arguments AST node.

    Args:
        args: The arguments AST node.
        is_method: Whether the function is an instance method.
        is_classmethod: Whether the function is a classmethod.

    Returns:
        List of Parameter objects (excluding self/cls).
    """
    params: list[Parameter] = []
    defaults_offset = len(args.args) - len(args.defaults)

    for i, arg in enumerate(args.args):
        # Skip self/cls
        if i == 0 and is_method and arg.arg in ("self", "cls"):
            continue
        if i == 0 and is_classmethod and arg.arg == "cls":
            continue

        type_hint = ast.unparse(arg.annotation) if arg.annotation else ""
        default = ""
        is_optional = False

        default_idx = i - defaults_offset
        if default_idx >= 0 and default_idx < len(args.defaults):
            default = ast.unparse(args.defaults[default_idx])
            is_optional = True

        params.append(Parameter(
            name=arg.arg,
            type_hint=type_hint,
            default=default,
            is_optional=is_optional,
        ))

    # Handle *args and **kwargs
    if args.vararg:
        type_hint = ast.unparse(args.vararg.annotation) if args.vararg.annotation else ""
        params.append(Parameter(
            name=f"*{args.vararg.arg}",
            type_hint=type_hint,
            is_optional=True,
        ))

    if args.kwarg:
        type_hint = ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else ""
        params.append(Parameter(
            name=f"**{args.kwarg.arg}",
            type_hint=type_hint,
            is_optional=True,
        ))

    return params


# ---------------------------------------------------------------------------
# TypeScript regex extraction
# ---------------------------------------------------------------------------


def extract_typescript_functions(source_path: Path) -> list[FunctionInfo]:
    """Extract exported function and method signatures from a TypeScript file.

    Uses regex-based extraction (not a full parser). Extracts:
    - Exported functions (export function ...)
    - Exported arrow functions (export const ... = ...)
    - Class methods (public methods in exported classes)

    Args:
        source_path: Path to the TypeScript source file.

    Returns:
        List of FunctionInfo objects.
    """
    source = source_path.read_text(encoding="utf-8")
    functions: list[FunctionInfo] = []

    # Extract exported functions
    for match in TS_FUNCTION_PATTERN.finditer(source):
        name = match.group(1)
        params_str = match.group(2)
        return_type = (match.group(3) or "").strip()
        is_async = "async" in source[match.start():match.start() + 50]

        params = _parse_ts_params(params_str)
        functions.append(FunctionInfo(
            name=name,
            params=params,
            return_type=return_type,
            is_async=is_async,
        ))

    # Extract exported arrow functions
    for match in TS_ARROW_PATTERN.finditer(source):
        name = match.group(1)
        # Arrow functions: minimal param extraction
        functions.append(FunctionInfo(
            name=name,
            is_async="async" in source[match.start():match.start() + 80],
        ))

    # Extract class methods
    class_matches = list(TS_CLASS_PATTERN.finditer(source))
    for class_match in class_matches:
        class_name = class_match.group(1)
        # Find class body (rough: from class declaration to next top-level declaration)
        class_start = class_match.end()
        brace_count = 0
        class_end = class_start
        in_class = False
        for i in range(class_start, len(source)):
            if source[i] == "{":
                brace_count += 1
                in_class = True
            elif source[i] == "}":
                brace_count -= 1
                if in_class and brace_count == 0:
                    class_end = i
                    break

        class_body = source[class_start:class_end]

        for method_match in TS_METHOD_PATTERN.finditer(class_body):
            method_name = method_match.group(1)
            # Skip constructor and private-looking methods
            if method_name.startswith("_") or method_name == "constructor":
                continue

            params_str = method_match.group(2)
            return_type = (method_match.group(3) or "").strip()
            is_async = "async" in class_body[
                max(0, method_match.start() - 20):method_match.start()
            ]

            params = _parse_ts_params(params_str)
            functions.append(FunctionInfo(
                name=method_name,
                params=params,
                return_type=return_type,
                is_async=is_async,
                is_method=True,
                class_name=class_name,
            ))

    return functions


def _parse_ts_params(params_str: str) -> list[Parameter]:
    """Parse a TypeScript parameter string into Parameter objects.

    Args:
        params_str: Raw parameter string from regex extraction.

    Returns:
        List of Parameter objects.
    """
    params: list[Parameter] = []
    if not params_str.strip():
        return params

    # Split by comma (simple — does not handle nested generics perfectly)
    depth = 0
    current = ""
    for char in params_str:
        if char in ("<", "(", "[", "{"):
            depth += 1
            current += char
        elif char in (">", ")", "]", "}"):
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            params.append(_parse_single_ts_param(current.strip()))
            current = ""
        else:
            current += char

    if current.strip():
        params.append(_parse_single_ts_param(current.strip()))

    return params


def _parse_single_ts_param(param_str: str) -> Parameter:
    """Parse a single TypeScript parameter.

    Args:
        param_str: Single parameter string (e.g. 'name: string', 'age?: number').

    Returns:
        Parameter object.
    """
    is_optional = "?" in param_str
    param_str = param_str.replace("?", "")

    parts = param_str.split(":", 1)
    name = parts[0].strip()
    type_hint = parts[1].strip() if len(parts) > 1 else ""

    # Check for default value
    default = ""
    if "=" in type_hint:
        type_parts = type_hint.split("=", 1)
        type_hint = type_parts[0].strip()
        default = type_parts[1].strip()
        is_optional = True
    elif "=" in name:
        name_parts = name.split("=", 1)
        name = name_parts[0].strip()
        default = name_parts[1].strip()
        is_optional = True

    return Parameter(
        name=name,
        type_hint=type_hint,
        default=default,
        is_optional=is_optional,
    )


# ---------------------------------------------------------------------------
# Test template generation — pytest
# ---------------------------------------------------------------------------


def generate_pytest_template(
    functions: list[FunctionInfo],
    source_path: Path,
) -> str:
    """Generate a pytest test file template.

    Args:
        functions: List of extracted function signatures.
        source_path: Path to the original source file.

    Returns:
        Generated test file content as a string.
    """
    module_name = source_path.stem
    lines: list[str] = []

    # Header
    lines.append(f'"""Tests for {module_name} module.')
    lines.append("")
    lines.append("Test methodology: Khorikov's 4-pillar approach")
    lines.append("  1. Regression protection — detect bugs in business logic")
    lines.append("  2. Refactoring resistance — verify behavior, not implementation")
    lines.append("  3. Fast feedback — minimize process-external dependencies")
    lines.append("  4. Maintainability — keep tests short, readable, independent")
    lines.append('"""')
    lines.append("")
    lines.append("import pytest")
    lines.append("")

    # Import statement (relative or absolute — user adjusts)
    lines.append(f"# TODO: Adjust the import path to match your project structure")
    lines.append(f"# from {module_name} import ...")
    lines.append("")
    lines.append("")

    # Group by class
    standalone_functions = [f for f in functions if not f.is_method]
    class_groups: dict[str, list[FunctionInfo]] = {}
    for func in functions:
        if func.is_method:
            class_groups.setdefault(func.class_name, []).append(func)

    # Generate tests for standalone functions
    if standalone_functions:
        lines.append("# " + "=" * 68)
        lines.append(f"# Standalone function tests")
        lines.append("# " + "=" * 68)
        lines.append("")

        for func in standalone_functions:
            lines.extend(_generate_pytest_function_tests(func))
            lines.append("")

    # Generate tests for class methods
    for class_name, methods in class_groups.items():
        lines.append("# " + "=" * 68)
        lines.append(f"# {class_name} tests")
        lines.append("# " + "=" * 68)
        lines.append("")

        lines.append(f"class Test{class_name}:")
        lines.append(f'    """Tests for {class_name} class."""')
        lines.append("")

        # Fixture for class instantiation
        lines.append("    @pytest.fixture")
        lines.append(f"    def {_to_snake_case(class_name)}(self) -> {class_name}:")
        lines.append(f'        """Create a {class_name} instance for testing."""')
        lines.append(f"        # TODO: Set up {class_name} with appropriate dependencies")
        lines.append(f"        return {class_name}()")
        lines.append("")

        for method in methods:
            method_tests = _generate_pytest_method_tests(method, class_name)
            for line in method_tests:
                lines.append(f"    {line}" if line.strip() else line)
            lines.append("")

    return "\n".join(lines)


def _generate_pytest_function_tests(func: FunctionInfo) -> list[str]:
    """Generate pytest test cases for a standalone function.

    Args:
        func: Function information.

    Returns:
        List of code lines.
    """
    lines: list[str] = []
    fn_name = func.name
    async_prefix = "async " if func.is_async else ""
    await_prefix = "await " if func.is_async else ""
    decorator = "@pytest.mark.asyncio\n" if func.is_async else ""

    # Test: happy path
    lines.append(f"{decorator}def test_{fn_name}_with_valid_input_returns_expected_result() -> None:")
    lines.append(f'    """Verify {fn_name} produces correct output for a typical valid input.')
    lines.append("")
    lines.append("    4-pillar focus: Regression protection (verify correct behavior)")
    lines.append('    """')
    lines.append("    # Arrange")
    for param in func.params:
        if not param.is_optional:
            lines.append(f"    {param.name} = ...  # TODO: provide a valid {param.type_hint or 'value'}")
    lines.append("")
    lines.append("    # Act")
    param_names = ", ".join(
        p.name for p in func.params if not p.name.startswith("*")
    )
    lines.append(f"    result = {await_prefix}{fn_name}({param_names})")
    lines.append("")
    lines.append("    # Assert")
    lines.append(f"    assert result == ...  # TODO: expected value (hard-code, do NOT replicate logic)")
    lines.append("")

    # Test: edge case
    lines.append(f"{decorator}def test_{fn_name}_with_boundary_value_handles_correctly() -> None:")
    lines.append(f'    """Verify {fn_name} handles boundary/edge cases.')
    lines.append("")
    lines.append("    4-pillar focus: Regression protection (boundary coverage)")
    lines.append('    """')
    lines.append("    # Arrange")
    lines.append("    # TODO: Set up boundary value inputs (empty, zero, max, min, None)")
    lines.append("")
    lines.append("    # Act")
    lines.append(f"    result = {await_prefix}{fn_name}(...)  # TODO: boundary input")
    lines.append("")
    lines.append("    # Assert")
    lines.append("    assert result == ...  # TODO: expected boundary behavior")
    lines.append("")

    # Test: error case
    lines.append(f"{decorator}def test_{fn_name}_with_invalid_input_raises_error() -> None:")
    lines.append(f'    """Verify {fn_name} raises appropriate error for invalid input.')
    lines.append("")
    lines.append("    4-pillar focus: Regression protection (error handling)")
    lines.append('    """')
    lines.append("    # Arrange")
    lines.append("    # TODO: Set up invalid inputs that should cause an error")
    lines.append("")
    lines.append("    # Act & Assert")
    lines.append(f"    with pytest.raises(ValueError):  # TODO: specify the expected exception type")
    lines.append(f"        {await_prefix}{fn_name}(...)  # TODO: invalid input")
    lines.append("")

    return lines


def _generate_pytest_method_tests(
    func: FunctionInfo,
    class_name: str,
) -> list[str]:
    """Generate pytest test cases for a class method.

    Args:
        func: Method information.
        class_name: Name of the containing class.

    Returns:
        List of code lines (unindented — caller adds class indentation).
    """
    lines: list[str] = []
    method_name = func.name
    fixture_name = _to_snake_case(class_name)
    async_prefix = "async " if func.is_async else ""
    await_prefix = "await " if func.is_async else ""
    decorator = "@pytest.mark.asyncio\n    " if func.is_async else ""

    # Test: happy path
    lines.append(f"{decorator}def test_{method_name}_with_valid_input_returns_expected_result(self, {fixture_name}: {class_name}) -> None:")
    lines.append(f'    """Verify {class_name}.{method_name} produces correct output.')
    lines.append("")
    lines.append("    4-pillar focus: Regression protection")
    lines.append('    """')
    lines.append("    # Arrange")
    for param in func.params:
        if not param.is_optional:
            lines.append(f"    {param.name} = ...  # TODO: valid {param.type_hint or 'value'}")
    lines.append("")
    lines.append("    # Act")
    param_names = ", ".join(
        p.name for p in func.params if not p.name.startswith("*")
    )
    lines.append(f"    result = {await_prefix}{fixture_name}.{method_name}({param_names})")
    lines.append("")
    lines.append("    # Assert")
    lines.append(f"    assert result == ...  # TODO: hard-coded expected value")
    lines.append("")

    # Test: edge case
    lines.append(f"{decorator}def test_{method_name}_with_edge_case_handles_correctly(self, {fixture_name}: {class_name}) -> None:")
    lines.append(f'    """Verify {class_name}.{method_name} handles edge cases.')
    lines.append("")
    lines.append("    4-pillar focus: Regression protection + Refactoring resistance")
    lines.append('    """')
    lines.append("    # Arrange")
    lines.append("    # TODO: boundary/edge case setup")
    lines.append("")
    lines.append("    # Act")
    lines.append(f"    result = {await_prefix}{fixture_name}.{method_name}(...)  # TODO")
    lines.append("")
    lines.append("    # Assert")
    lines.append("    assert result == ...  # TODO: expected edge behavior")
    lines.append("")

    return lines


# ---------------------------------------------------------------------------
# Test template generation — jest / vitest
# ---------------------------------------------------------------------------


def generate_jest_template(
    functions: list[FunctionInfo],
    source_path: Path,
    framework: Literal["jest", "vitest"],
) -> str:
    """Generate a Jest or Vitest test file template.

    Args:
        functions: List of extracted function signatures.
        source_path: Path to the original source file.
        framework: 'jest' or 'vitest'.

    Returns:
        Generated test file content as a string.
    """
    module_name = source_path.stem
    lines: list[str] = []

    # Import block
    if framework == "vitest":
        lines.append("import { describe, it, expect, beforeEach } from 'vitest';")
    lines.append("")

    # TODO import
    lines.append("// TODO: Adjust the import path to match your project structure")
    export_names = [f.name for f in functions if not f.is_method]
    class_names = list({f.class_name for f in functions if f.is_method})
    all_imports = export_names + class_names
    if all_imports:
        lines.append(f"// import {{ {', '.join(all_imports)} }} from './{module_name}';")
    lines.append("")

    # Header comment
    lines.append("/**")
    lines.append(f" * Tests for {module_name} module.")
    lines.append(" *")
    lines.append(" * Test methodology: Khorikov's 4-pillar approach")
    lines.append(" *   1. Regression protection — detect bugs in business logic")
    lines.append(" *   2. Refactoring resistance — verify behavior, not implementation")
    lines.append(" *   3. Fast feedback — minimize process-external dependencies")
    lines.append(" *   4. Maintainability — keep tests short, readable, independent")
    lines.append(" */")
    lines.append("")

    # Standalone functions
    standalone = [f for f in functions if not f.is_method]
    for func in standalone:
        lines.extend(_generate_js_function_tests(func))
        lines.append("")

    # Class methods
    class_groups: dict[str, list[FunctionInfo]] = {}
    for func in functions:
        if func.is_method:
            class_groups.setdefault(func.class_name, []).append(func)

    for class_name, methods in class_groups.items():
        var_name = _to_camel_case(class_name)
        lines.append(f"describe('{class_name}', () => {{")
        lines.append(f"  let {var_name}: {class_name};")
        lines.append("")
        lines.append("  beforeEach(() => {")
        lines.append(f"    // TODO: Set up {class_name} with appropriate dependencies")
        lines.append(f"    {var_name} = new {class_name}();")
        lines.append("  });")
        lines.append("")

        for method in methods:
            method_lines = _generate_js_method_tests(method, var_name)
            for line in method_lines:
                lines.append(f"  {line}" if line.strip() else "")
            lines.append("")

        lines.append("});")
        lines.append("")

    return "\n".join(lines)


def _generate_js_function_tests(func: FunctionInfo) -> list[str]:
    """Generate Jest/Vitest test cases for a standalone function.

    Args:
        func: Function information.

    Returns:
        List of code lines.
    """
    lines: list[str] = []
    fn_name = func.name
    async_kw = "async " if func.is_async else ""
    await_kw = "await " if func.is_async else ""

    lines.append(f"describe('{fn_name}', () => {{")

    # Happy path
    lines.append(f"  it('returns expected result for valid input', {async_kw}() => {{")
    lines.append("    // Arrange")
    for param in func.params:
        if not param.is_optional:
            lines.append(f"    const {param.name} = undefined; // TODO: valid {param.type_hint or 'value'}")
    lines.append("")
    lines.append("    // Act")
    param_names = ", ".join(p.name for p in func.params if not p.name.startswith("*"))
    lines.append(f"    const result = {await_kw}{fn_name}({param_names});")
    lines.append("")
    lines.append("    // Assert")
    lines.append("    // 4-pillar: Hard-code expected value (do NOT replicate logic)")
    lines.append("    expect(result).toBe(undefined); // TODO: expected value")
    lines.append("  });")
    lines.append("")

    # Edge case
    lines.append(f"  it('handles boundary values correctly', {async_kw}() => {{")
    lines.append("    // Arrange — TODO: boundary inputs (empty, zero, max, null, undefined)")
    lines.append("")
    lines.append("    // Act")
    lines.append(f"    const result = {await_kw}{fn_name}(/* TODO: boundary input */);")
    lines.append("")
    lines.append("    // Assert")
    lines.append("    expect(result).toBe(undefined); // TODO: expected boundary behavior")
    lines.append("  });")
    lines.append("")

    # Error case
    lines.append(f"  it('throws error for invalid input', {async_kw}() => {{")
    lines.append("    // Arrange — TODO: invalid inputs")
    lines.append("")
    lines.append("    // Act & Assert")
    if func.is_async:
        lines.append(f"    await expect({fn_name}(/* TODO */)).rejects.toThrow();")
    else:
        lines.append(f"    expect(() => {fn_name}(/* TODO */)).toThrow();")
    lines.append("  });")

    lines.append("});")
    return lines


def _generate_js_method_tests(func: FunctionInfo, var_name: str) -> list[str]:
    """Generate Jest/Vitest test cases for a class method.

    Args:
        func: Method information.
        var_name: Variable name for the class instance.

    Returns:
        List of code lines (indented for class describe block).
    """
    lines: list[str] = []
    method_name = func.name
    async_kw = "async " if func.is_async else ""
    await_kw = "await " if func.is_async else ""

    lines.append(f"describe('{method_name}', () => {{")

    # Happy path
    lines.append(f"  it('returns expected result for valid input', {async_kw}() => {{")
    lines.append("    // Arrange")
    for param in func.params:
        if not param.is_optional:
            lines.append(f"    const {param.name} = undefined; // TODO: valid {param.type_hint or 'value'}")
    lines.append("")
    lines.append("    // Act")
    param_names = ", ".join(p.name for p in func.params if not p.name.startswith("*"))
    lines.append(f"    const result = {await_kw}{var_name}.{method_name}({param_names});")
    lines.append("")
    lines.append("    // Assert")
    lines.append("    expect(result).toBe(undefined); // TODO: hard-coded expected value")
    lines.append("  });")
    lines.append("")

    # Edge case
    lines.append(f"  it('handles edge case correctly', {async_kw}() => {{")
    lines.append("    // Arrange — TODO: boundary/edge case setup")
    lines.append("")
    lines.append("    // Act")
    lines.append(f"    const result = {await_kw}{var_name}.{method_name}(/* TODO */);")
    lines.append("")
    lines.append("    // Assert")
    lines.append("    expect(result).toBe(undefined); // TODO: expected edge behavior")
    lines.append("  });")

    lines.append("});")
    return lines


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case.

    Args:
        name: CamelCase string.

    Returns:
        snake_case string.
    """
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    result = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", result)
    return result.lower()


def _to_camel_case(name: str) -> str:
    """Convert PascalCase to camelCase.

    Args:
        name: PascalCase string.

    Returns:
        camelCase string.
    """
    if not name:
        return name
    return name[0].lower() + name[1:]


def detect_language(source_path: Path) -> Literal["python", "typescript"]:
    """Detect the source language from file extension.

    Args:
        source_path: Path to the source file.

    Returns:
        'python' or 'typescript'.

    Raises:
        ValueError: If the file extension is not supported.
    """
    suffix = source_path.suffix.lower()
    if suffix == ".py":
        return "python"
    elif suffix in (".ts", ".tsx"):
        return "typescript"
    elif suffix in (".js", ".jsx"):
        return "typescript"  # Use TS extraction (JS is subset-compatible)
    else:
        raise ValueError(
            f"Unsupported file extension: {suffix}. "
            f"Supported: .py, .ts, .tsx, .js, .jsx"
        )


def determine_framework(
    language: Literal["python", "typescript"],
    framework_arg: str | None,
) -> str:
    """Determine the test framework based on language and user preference.

    Args:
        language: Detected source language.
        framework_arg: User-specified framework (or None for auto).

    Returns:
        Framework name.

    Raises:
        ValueError: If the framework is incompatible with the language.
    """
    if framework_arg:
        if language == "python" and framework_arg != "pytest":
            raise ValueError(
                f"Framework '{framework_arg}' is not compatible with Python. Use 'pytest'."
            )
        if language == "typescript" and framework_arg not in ("jest", "vitest"):
            raise ValueError(
                f"Framework '{framework_arg}' is not compatible with TypeScript. Use 'jest' or 'vitest'."
            )
        return framework_arg

    # Auto-select
    if language == "python":
        return "pytest"
    return "vitest"  # Default for TS


def determine_output_path(
    source_path: Path,
    output_arg: Path | None,
    framework: str,
) -> Path:
    """Determine the output test file path.

    Args:
        source_path: Path to the original source file.
        output_arg: User-specified output path (or None for auto).
        framework: Test framework name.

    Returns:
        Output file path.
    """
    if output_arg:
        return output_arg.resolve()

    stem = source_path.stem
    if framework == "pytest":
        return source_path.parent / f"test_{stem}.py"
    else:
        ext = source_path.suffix
        return source_path.parent / f"{stem}.test{ext}"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Test Template Generator - test skill execution script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generate_test_template.py src/calculator.py\n"
            "  python generate_test_template.py src/userService.ts --framework vitest\n"
            "  python generate_test_template.py src/auth.py --output tests/test_auth.py\n"
        ),
    )
    parser.add_argument(
        "source_file", type=Path,
        help="Path to the source file (Python or TypeScript)",
    )
    parser.add_argument(
        "--framework", type=str, default=None,
        choices=SUPPORTED_FRAMEWORKS,
        help="Test framework (default: auto-detect from language)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output test file path (default: auto-generated next to source)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the test template generator.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    args = parse_args(argv)
    source_path: Path = args.source_file.resolve()

    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}", file=sys.stderr)
        return 1

    # Detect language
    try:
        language = detect_language(source_path)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Determine framework
    try:
        framework = determine_framework(language, args.framework)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Extract functions
    print(f"Analyzing {source_path} ({language})...")
    try:
        if language == "python":
            functions = extract_python_functions(source_path)
        else:
            functions = extract_typescript_functions(source_path)
    except SyntaxError as e:
        print(f"ERROR: Syntax error in source file: {e}", file=sys.stderr)
        return 1

    if not functions:
        print("WARNING: No public functions/methods found in the source file.")
        print("Skipping test generation.")
        return 0

    print(f"Found {len(functions)} public function(s)/method(s):")
    for func in functions:
        prefix = f"  {func.class_name}." if func.is_method else "  "
        async_marker = "async " if func.is_async else ""
        params = ", ".join(
            f"{p.name}: {p.type_hint}" if p.type_hint else p.name
            for p in func.params
        )
        ret = f" -> {func.return_type}" if func.return_type else ""
        print(f"{prefix}{async_marker}{func.name}({params}){ret}")

    # Generate template
    print(f"\nGenerating {framework} test template...")
    if framework == "pytest":
        content = generate_pytest_template(functions, source_path)
    else:
        content = generate_jest_template(functions, source_path, framework)

    # Determine output path
    output_path = determine_output_path(source_path, args.output, framework)

    # Check if output file already exists
    if output_path.exists():
        print(f"WARNING: Output file already exists: {output_path}")
        print("Overwriting...")

    # Write output
    output_path.write_text(content, encoding="utf-8")
    print(f"\nTest template written to: {output_path}")
    print(f"Functions covered: {len(functions)}")
    print(f"Test cases generated: {len(functions) * 3} (happy path + edge case + error case)")
    print()
    print("Next steps:")
    print("  1. Update import paths in the generated file")
    print("  2. Replace TODO placeholders with actual test data")
    print("  3. Hard-code expected values (do NOT replicate production logic)")
    print("  4. Run tests to verify they pass")

    return 0


if __name__ == "__main__":
    sys.exit(main())
