#!/usr/bin/env python3
"""
Plugin Validation Test Suite for DGT Centaur Mods

This script validates that plugins follow the required structure and conventions.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class PluginValidator:
    """Validates plugin files for correct structure and conventions."""

    REQUIRED_IMPORTS = [
        'chess',
        'Plugin',
        'Centaur',
        'Enums'
    ]

    OPTIONAL_CALLBACKS = [
        'splash_screen',
        'on_start_callback',
        'key_callback',
        'event_callback',
        'move_callback',
        'undo_callback',
        'field_callback',
        'start',
        'stop'
    ]

    def __init__(self, plugin_path: str):
        self.plugin_path = Path(plugin_path)
        self.plugin_name = self.plugin_path.stem
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate(self) -> bool:
        """Run all validation checks. Returns True if valid."""
        print(f"\n{'='*60}")
        print(f"Validating plugin: {self.plugin_name}")
        print(f"{'='*60}\n")

        if not self.plugin_path.exists():
            self.errors.append(f"File does not exist: {self.plugin_path}")
            return False

        # Read file content
        try:
            with open(self.plugin_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False

        # Run all validation checks
        self._check_file_extension()
        self._check_license_header()
        self._check_python_syntax()
        self._check_imports()
        self._check_class_definition()
        self._check_callbacks()
        self._check_docstring()

        # Print results
        self._print_results()

        return len(self.errors) == 0

    def _check_file_extension(self):
        """Check that file has .py extension."""
        if self.plugin_path.suffix != '.py':
            self.errors.append(f"Invalid file extension: {self.plugin_path.suffix} (must be .py)")
        else:
            self.info.append("✓ File extension is correct (.py)")

    def _check_license_header(self):
        """Check for GPL license header."""
        if "GNU General Public" in self.content or "DGTCentaur Mods" in self.content:
            self.info.append("✓ GPL license header found")
        else:
            self.warnings.append("GPL license header not found")

    def _check_python_syntax(self):
        """Check that the file has valid Python syntax."""
        try:
            self.ast_tree = ast.parse(self.content)
            self.info.append("✓ Python syntax is valid")
        except SyntaxError as e:
            self.errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            self.ast_tree = None

    def _check_imports(self):
        """Check for required imports."""
        if self.ast_tree is None:
            return

        imports_found = set()

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports_found.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports_found.add(node.module)
                for alias in node.names:
                    imports_found.add(alias.name)

        missing_imports = []
        for required in self.REQUIRED_IMPORTS:
            # Check if the import or part of it exists
            found = any(required in imp or imp in required for imp in imports_found)
            if found:
                self.info.append(f"✓ Required import found: {required}")
            else:
                missing_imports.append(required)

        if missing_imports:
            self.warnings.append(f"Missing recommended imports: {', '.join(missing_imports)}")

    def _check_class_definition(self):
        """Check that class exists and matches filename."""
        if self.ast_tree is None:
            return

        classes = [node for node in ast.walk(self.ast_tree)
                  if isinstance(node, ast.ClassDef)]

        if not classes:
            self.errors.append("No class definition found in file")
            return

        # Check if any class matches the filename
        matching_class = None
        for cls in classes:
            if cls.name == self.plugin_name:
                matching_class = cls
                break

        if matching_class is None:
            class_names = [cls.name for cls in classes]
            self.errors.append(
                f"Class name must match filename. "
                f"Expected: '{self.plugin_name}', Found: {class_names}"
            )
            return

        self.info.append(f"✓ Class name matches filename: {self.plugin_name}")

        # Check inheritance
        if matching_class.bases:
            base_names = []
            for base in matching_class.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(base.attr)

            if 'Plugin' in base_names:
                self.info.append("✓ Class inherits from Plugin")
            else:
                self.errors.append(
                    f"Class must inherit from Plugin. Found bases: {base_names}"
                )
        else:
            self.errors.append("Class does not inherit from Plugin")

        self.plugin_class = matching_class

    def _check_callbacks(self):
        """Check for callback methods."""
        if self.ast_tree is None or not hasattr(self, 'plugin_class'):
            return

        methods = {}
        for node in self.plugin_class.body:
            if isinstance(node, ast.FunctionDef):
                methods[node.name] = node

        # Check for __init__
        if '__init__' in methods:
            self.info.append("✓ __init__ method found")
            # Check if it calls super().__init__
            init_method = methods['__init__']
            calls_super = False
            for node in ast.walk(init_method):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if (isinstance(node.func.value, ast.Call) and
                            isinstance(node.func.value.func, ast.Name) and
                            node.func.value.func.id == 'super'):
                            calls_super = True
                            break

            if calls_super:
                self.info.append("✓ __init__ calls super().__init__()")
            else:
                self.warnings.append("__init__ should call super().__init__(id)")
        else:
            self.warnings.append("No __init__ method found")

        # Check for optional callbacks
        callbacks_found = []
        for callback in self.OPTIONAL_CALLBACKS:
            if callback in methods:
                callbacks_found.append(callback)

        if callbacks_found:
            self.info.append(f"✓ Callbacks implemented: {', '.join(callbacks_found)}")
        else:
            self.warnings.append("No callbacks implemented (all are optional)")

        # Check for start/stop methods
        if 'start' in methods:
            self.info.append("✓ start() method found")
        if 'stop' in methods:
            self.info.append("✓ stop() method found")

    def _check_docstring(self):
        """Check for class docstring."""
        if self.ast_tree is None or not hasattr(self, 'plugin_class'):
            return

        docstring = ast.get_docstring(self.plugin_class)
        if docstring:
            self.info.append("✓ Class has docstring")
        else:
            self.warnings.append("Class should have a docstring describing its purpose")

    def _print_results(self):
        """Print validation results."""
        print("\n" + "─" * 60)

        if self.info:
            print("\n✓ PASSED CHECKS:")
            for info in self.info:
                print(f"  {info}")

        if self.warnings:
            print("\n⚠ WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if self.errors:
            print("\n✗ ERRORS:")
            for error in self.errors:
                print(f"  ✗ {error}")

        print("\n" + "─" * 60)

        if len(self.errors) == 0:
            print(f"\n✓ Plugin '{self.plugin_name}' is VALID!")
            if self.warnings:
                print(f"  ({len(self.warnings)} warning(s))")
        else:
            print(f"\n✗ Plugin '{self.plugin_name}' has {len(self.errors)} error(s)")

        print()


def find_all_plugins(plugins_dir: str) -> List[Path]:
    """Find all Python files in the plugins directory."""
    plugins_path = Path(plugins_dir)
    if not plugins_path.exists():
        print(f"Error: Plugins directory not found: {plugins_dir}")
        return []

    plugins = []
    for file_path in plugins_path.glob("*.py"):
        # Skip test files and __init__.py
        if file_path.name.startswith('test_') or file_path.name.startswith('__'):
            continue
        plugins.append(file_path)

    return sorted(plugins)


def main():
    """Main entry point for the test suite."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate DGT Centaur Mods plugins',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all plugins in the default directory
  python test_plugins.py

  # Test all plugins in a specific directory
  python test_plugins.py --dir /path/to/plugins

  # Test a specific plugin
  python test_plugins.py --plugin RandomBot.py

  # Test multiple specific plugins
  python test_plugins.py --plugin RandomBot.py --plugin Squiz.py
        """
    )

    parser.add_argument(
        '--dir',
        default='.',
        help='Directory containing plugin files (default: current directory)'
    )

    parser.add_argument(
        '--plugin',
        action='append',
        help='Specific plugin file(s) to test (can be used multiple times)'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Determine which plugins to test
    if args.plugin:
        # Test specific plugins
        plugins = [Path(args.dir) / plugin for plugin in args.plugin]
    else:
        # Test all plugins in directory
        plugins = find_all_plugins(args.dir)

    if not plugins:
        print("No plugins found to test.")
        return 1

    print(f"\nFound {len(plugins)} plugin(s) to test\n")

    # Validate each plugin
    results = {}
    for plugin_path in plugins:
        validator = PluginValidator(plugin_path)
        is_valid = validator.validate()
        results[plugin_path.name] = {
            'valid': is_valid,
            'errors': len(validator.errors),
            'warnings': len(validator.warnings)
        }

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    valid_count = sum(1 for r in results.values() if r['valid'])
    invalid_count = len(results) - valid_count

    print(f"\nTotal plugins tested: {len(results)}")
    print(f"✓ Valid: {valid_count}")
    print(f"✗ Invalid: {invalid_count}")

    if invalid_count > 0:
        print("\nInvalid plugins:")
        for name, result in results.items():
            if not result['valid']:
                print(f"  ✗ {name} ({result['errors']} error(s))")

    print()

    return 0 if invalid_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
