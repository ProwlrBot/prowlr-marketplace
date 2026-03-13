---
name: doc-generator
description: Use this skill when the user wants to generate documentation, write docstrings, create API docs, build a README, or produce HTML/PDF documentation from code.
---

# Doc Generator

## Overview

Generates documentation from code: API reference docs via pdoc/sphinx, docstrings from function signatures, README sections, and OpenAPI specs from FastAPI/Flask routes.

## Generate API Docs with pdoc

```bash
pip install pdoc
pdoc src/mypackage --output-dir docs/api --html
# or serve live:
pdoc src/mypackage
```

```python
import pdoc, pathlib

def generate_api_docs(module_path: str, output_dir: str = "docs/api") -> None:
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    pdoc.render.configure(show_source=True)
    pdoc.pdoc(module_path, output_directory=pathlib.Path(output_dir))
```

## Extract Docstrings with AST

```python
import ast

def extract_docstrings(source: str) -> dict[str, str]:
    """Extract all function/class docstrings from Python source."""
    tree = ast.parse(source)
    docs = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant)):
                docs[node.name] = node.body[0].value.value
    return docs

def generate_docstring(func_source: str) -> str:
    """
    Given a function's source without a docstring,
    analyze its signature and body to write a Google-style docstring.
    """
    # Use this as a prompt template when writing docstrings:
    # Args section: one line per parameter with type and description
    # Returns section: what the function returns
    # Raises section: exceptions the function may raise
    # Example: show a brief usage example
    pass
```

## Google-Style Docstring Template

```python
def example_function(param1: str, param2: int = 0) -> list[str]:
    """Brief one-line description ending with period.

    Longer description if needed. Explain what the function does,
    any important behavior, and edge cases.

    Args:
        param1: Description of param1. What it represents.
        param2: Description of param2. Defaults to 0.

    Returns:
        Description of the return value and its structure.

    Raises:
        ValueError: When param1 is empty.
        TypeError: When param2 is not an integer.

    Example:
        >>> result = example_function("hello", 3)
        >>> print(result)
        ['hello', 'hello', 'hello']
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return [param1] * param2
```

## Sphinx Setup

```bash
pip install sphinx sphinx-rtd-theme myst-parser
sphinx-quickstart docs
# Edit docs/conf.py:
```

```python
# docs/conf.py key settings
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",   # Google/NumPy docstrings
    "sphinx.ext.viewcode",
    "myst_parser",
]
html_theme = "sphinx_rtd_theme"
autodoc_default_options = {"members": True, "undoc-members": True}
```

```bash
cd docs && make html
```

## README Generator

```python
def generate_readme_section(module_path: str) -> str:
    """Generate a README section from a Python module's public API."""
    import importlib.util, inspect
    spec = importlib.util.spec_from_file_location("mod", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    lines = ["## API Reference\n"]
    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_"):
            sig = inspect.signature(obj)
            doc = inspect.getdoc(obj) or "No description."
            lines.append(f"### `{name}{sig}`\n\n{doc}\n")
    return "\n".join(lines)
```

## OpenAPI Spec from FastAPI

```python
import json
# FastAPI auto-generates OpenAPI — just export it:
from myapp.main import app
spec = app.openapi()
print(json.dumps(spec, indent=2))
# Or serve at /openapi.json automatically
```

## Quick Reference

| Task | Tool | Command |
|------|------|---------|
| API reference | pdoc | `pdoc src/pkg --output-dir docs/` |
| Sphinx HTML | sphinx | `cd docs && make html` |
| OpenAPI spec | FastAPI | `app.openapi()` returns dict |
| Extract docstrings | ast | `ast.parse()` + walk |
| Serve live docs | pdoc | `pdoc src/pkg` (opens browser) |
