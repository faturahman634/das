#!/usr/bin/env python3
"""
Test script to verify DASS code structure and basic functionality.
This script validates the refactored implementation without requiring
a GUI environment or actual hardware.
"""

import sys
import inspect


def test_imports():
    """Test that all necessary modules can be imported."""
    print("Testing imports...")
    try:
        # These imports should work even without tkinter
        import serial.tools.list_ports
        import csv
        import os
        from datetime import datetime
        from typing import List, Optional, Dict, Any
        print("✓ Basic imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_class_structure():
    """Test that all classes are defined correctly."""
    print("\nTesting class structure...")
    try:
        # Import the module without running main
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "dass", "DASS_Ver_1_channel_name_3_auto_save.py"
        )
        if spec is None or spec.loader is None:
            print("✗ Could not load module")
            return False

        dass = importlib.util.module_from_spec(spec)

        # Check for expected classes
        expected_classes = [
            'SerialHandler',
            'ModbusHandler',
            'DataLogger',
            'PlotManager',
            'UIManager',
            'DASSApplication'
        ]

        for class_name in expected_classes:
            if hasattr(dass, class_name):
                print(f"✓ Class {class_name} defined")
            else:
                print(f"✗ Class {class_name} not found")
                return False

        print("✓ All expected classes found")
        return True
    except Exception as e:
        print(f"✗ Class structure test failed: {e}")
        return False


def test_constants():
    """Test that constants are defined."""
    print("\nTesting constants...")
    try:
        with open('DASS_Ver_1_channel_name_3_auto_save.py', 'r') as f:
            content = f.read()

        expected_constants = [
            'DEFAULT_BAUDRATE',
            'DEFAULT_TIMEOUT',
            'DEFAULT_MODBUS_SLAVE_ID',
            'DEFAULT_CHANNEL_COUNT',
            'MAX_DATA_POINTS',
            'LOG_DIRECTORY'
        ]

        for const in expected_constants:
            if const in content:
                print(f"✓ Constant {const} defined")
            else:
                print(f"✗ Constant {const} not found")
                return False

        print("✓ All constants defined")
        return True
    except Exception as e:
        print(f"✗ Constants test failed: {e}")
        return False


def test_documentation():
    """Test that classes and methods have documentation."""
    print("\nTesting documentation...")
    try:
        with open('DASS_Ver_1_channel_name_3_auto_save.py', 'r') as f:
            content = f.read()

        # Check for module docstring
        if content.startswith('"""') or content.startswith("'''"):
            print("✓ Module docstring present")
        else:
            print("✗ Module docstring missing")
            return False

        # Count docstrings
        docstring_count = content.count('"""')
        if docstring_count > 20:  # Expect many docstrings
            print(f"✓ Found {docstring_count // 2} docstrings")
        else:
            print(f"✗ Insufficient documentation (found {docstring_count // 2} docstrings)")
            return False

        print("✓ Documentation adequate")
        return True
    except Exception as e:
        print(f"✗ Documentation test failed: {e}")
        return False


def test_pep8_compliance():
    """Test basic PEP 8 compliance."""
    print("\nTesting PEP 8 compliance...")
    try:
        with open('DASS_Ver_1_channel_name_3_auto_save.py', 'r') as f:
            lines = f.readlines()

        issues = []

        # Check line length (warning, not failure)
        long_lines = [i+1 for i, line in enumerate(lines)
                      if len(line.rstrip()) > 100 and not line.strip().startswith('#')]
        if long_lines:
            print(f"⚠ {len(long_lines)} lines exceed 100 characters (lines: {long_lines[:5]}...)")

        # Check for trailing whitespace (skip docstring lines)
        in_docstring = False
        trailing_ws = []
        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
            elif not in_docstring and line.rstrip() != line and line.strip():
                trailing_ws.append(i+1)
        if trailing_ws:
            print(f"✗ Found trailing whitespace on lines: {trailing_ws[:5]}")
            return False

        # Check for proper imports organization
        in_imports = False
        import_section = []
        for line in lines[:50]:  # Check first 50 lines
            if line.startswith('import ') or line.startswith('from '):
                in_imports = True
                import_section.append(line)
            elif in_imports and line.strip() and not line.startswith('#'):
                break

        if import_section:
            print(f"✓ Found {len(import_section)} import statements")

        print("✓ Basic PEP 8 checks passed")
        return True
    except Exception as e:
        print(f"✗ PEP 8 test failed: {e}")
        return False


def test_file_structure():
    """Test file organization and structure."""
    print("\nTesting file structure...")
    try:
        with open('DASS_Ver_1_channel_name_3_auto_save.py', 'r') as f:
            content = f.read()

        # Check for main guard
        if 'if __name__ == "__main__":' in content:
            print("✓ Main guard present")
        else:
            print("✗ Main guard missing")
            return False

        # Check for class definitions
        class_count = content.count('class ')
        if class_count >= 6:  # Expect at least 6 classes
            print(f"✓ Found {class_count} class definitions")
        else:
            print(f"✗ Insufficient classes (found {class_count}, expected >= 6)")
            return False

        # Check for type hints
        if 'List[' in content and 'Optional[' in content and 'Dict[' in content:
            print("✓ Type hints used")
        else:
            print("✗ Type hints missing or insufficient")
            return False

        print("✓ File structure good")
        return True
    except Exception as e:
        print(f"✗ File structure test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("DASS Implementation Test Suite")
    print("=" * 60)

    tests = [
        test_imports,
        test_constants,
        test_documentation,
        test_pep8_compliance,
        test_file_structure,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    if all(results):
        print("\n✓ All tests passed! Code structure is good.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the code.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
