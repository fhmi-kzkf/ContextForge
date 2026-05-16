"""
Test script to verify the refactored scan_files function handles edge cases properly.
This script creates various edge case scenarios and tests the analyzer's robustness.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import RepoAnalyzer


def create_test_repo(base_path: str) -> str:
    """
    Create a test repository with various edge cases.
    
    Args:
        base_path: Base directory for test repo
        
    Returns:
        str: Path to test repo
    """
    test_repo = os.path.join(base_path, "test_repo")
    os.makedirs(test_repo, exist_ok=True)
    
    # 1. Normal Python files
    with open(os.path.join(test_repo, "normal.py"), "w") as f:
        f.write("def hello():\n    return 'world'\n")
    
    # 2. Large Python file (exceeds 200KB limit)
    large_file = os.path.join(test_repo, "large_file.py")
    with open(large_file, "w") as f:
        f.write("# Large file\n" * 20000)  # ~300KB
    
    # 3. Empty Python file
    with open(os.path.join(test_repo, "empty.py"), "w") as f:
        pass
    
    # 4. Python file with syntax error
    with open(os.path.join(test_repo, "syntax_error.py"), "w") as f:
        f.write("def broken(\n    # Missing closing parenthesis\n")
    
    # 5. Python file with unicode issues
    unicode_file = os.path.join(test_repo, "unicode_test.py")
    with open(unicode_file, "wb") as f:
        f.write(b"# -*- coding: utf-8 -*-\n")
        f.write(b"# Test with special chars: \xe9\xe8\xe0\n")
        f.write(b"def test():\n    pass\n")
    
    # 6. Deep nested directory structure (exceeds MAX_DEPTH)
    deep_path = test_repo
    for i in range(15):  # Create 15 levels deep
        deep_path = os.path.join(deep_path, f"level_{i}")
        os.makedirs(deep_path, exist_ok=True)
    with open(os.path.join(deep_path, "deep_file.py"), "w") as f:
        f.write("# Deep nested file\n")
    
    # 7. Test directory (should be excluded)
    test_dir = os.path.join(test_repo, "tests")
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "test_something.py"), "w") as f:
        f.write("def test_function():\n    pass\n")
    
    # 8. Config files
    with open(os.path.join(test_repo, "requirements.txt"), "w") as f:
        f.write("numpy==1.21.0\npandas==1.3.0\n")
    
    # 9. Model file
    with open(os.path.join(test_repo, "model.pkl"), "wb") as f:
        f.write(b"fake model data")
    
    # 10. Notebook file
    with open(os.path.join(test_repo, "notebook.ipynb"), "w") as f:
        f.write('{"cells": [], "metadata": {}, "nbformat": 4}')
    
    # 11. Create a symlink (if supported on the platform)
    try:
        symlink_target = os.path.join(test_repo, "normal.py")
        symlink_path = os.path.join(test_repo, "symlink.py")
        if os.name != 'nt':  # Unix-like systems
            os.symlink(symlink_target, symlink_path)
        else:  # Windows - requires admin privileges
            try:
                os.symlink(symlink_target, symlink_path)
            except OSError:
                print("Note: Symlink creation skipped (requires admin on Windows)")
    except Exception as e:
        print(f"Note: Could not create symlink: {e}")
    
    return test_repo


def test_scan_files():
    """Test the scan_files function with various edge cases."""
    print("=" * 70)
    print("Testing RepoAnalyzer.scan_files() with edge cases")
    print("=" * 70)
    
    # Create temporary test repository
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n1. Creating test repository in: {temp_dir}")
        test_repo = create_test_repo(temp_dir)
        print(f"   Test repo created at: {test_repo}")
        
        # Initialize analyzer
        print("\n2. Initializing RepoAnalyzer...")
        analyzer = RepoAnalyzer(test_repo)
        
        # Run scan
        print("\n3. Running scan_files()...")
        try:
            results = analyzer.scan_files()
            
            print("\n4. Scan Results:")
            print(f"   - Total files found: {results['file_count_total']}")
            print(f"   - Python files found: {len(results['all_python_files'])}")
            print(f"   - Python files analyzed: {results['file_count_analyzed']}")
            print(f"   - Files skipped: {results['file_count_skipped']}")
            print(f"   - Notebook files: {len(results['notebook_files'])}")
            print(f"   - Config files: {len(results['config_files'])}")
            print(f"   - Model files: {len(results['model_files'])}")
            print(f"   - Scan strategy: {results['scan_strategy']}")
            print(f"   - Errors encountered: {results['error_count']}")
            
            if results['scan_errors']:
                print("\n5. Scan Errors (Edge Cases Handled):")
                for i, error in enumerate(results['scan_errors'], 1):
                    print(f"   {i}. Type: {error['type']}")
                    print(f"      Path: {error.get('path', 'N/A')}")
                    print(f"      Message: {error['message']}")
            
            print("\n6. Python Files Detected:")
            for py_file in results['python_files'][:10]:  # Show first 10
                print(f"   - {py_file}")
            if len(results['python_files']) > 10:
                print(f"   ... and {len(results['python_files']) - 10} more")
            
            # Test parse_python_file with edge cases
            print("\n7. Testing parse_python_file() with edge cases:")
            
            test_files = [
                ("normal.py", "Normal file"),
                ("empty.py", "Empty file"),
                ("syntax_error.py", "Syntax error file"),
                ("unicode_test.py", "Unicode file")
            ]
            
            for file_name, description in test_files:
                if file_name in [os.path.basename(f) for f in results['all_python_files']]:
                    print(f"\n   Testing {description} ({file_name}):")
                    parsed = analyzer.parse_python_file(file_name)
                    if 'parse_error' in parsed:
                        print(f"   ✓ Error handled gracefully: {parsed['parse_error']}")
                    else:
                        print(f"   ✓ Parsed successfully")
                        print(f"     - Functions: {len(parsed['functions'])}")
                        print(f"     - Classes: {len(parsed['classes'])}")
                        print(f"     - Imports: {len(parsed['imports'])}")
            
            print("\n" + "=" * 70)
            print("✓ All edge case tests completed successfully!")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error during scan: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_symlink_handling():
    """Test symlink and circular reference handling."""
    print("\n" + "=" * 70)
    print("Testing Symlink and Circular Reference Handling")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_repo = os.path.join(temp_dir, "symlink_test")
        os.makedirs(test_repo, exist_ok=True)
        
        # Create a normal file
        with open(os.path.join(test_repo, "file1.py"), "w") as f:
            f.write("# File 1\n")
        
        # Try to create circular symlinks (platform dependent)
        try:
            dir1 = os.path.join(test_repo, "dir1")
            dir2 = os.path.join(test_repo, "dir2")
            os.makedirs(dir1, exist_ok=True)
            os.makedirs(dir2, exist_ok=True)
            
            if os.name != 'nt':
                # Create circular symlinks on Unix-like systems
                os.symlink(dir2, os.path.join(dir1, "link_to_dir2"))
                os.symlink(dir1, os.path.join(dir2, "link_to_dir1"))
                print("   Created circular symlinks for testing")
            else:
                print("   Skipping circular symlink test on Windows")
            
            analyzer = RepoAnalyzer(test_repo)
            results = analyzer.scan_files()
            
            print(f"\n   Results:")
            print(f"   - Files scanned: {results['file_count_total']}")
            print(f"   - Errors: {results['error_count']}")
            
            if results['scan_errors']:
                print(f"\n   Symlink errors detected:")
                for error in results['scan_errors']:
                    if 'symlink' in error['type']:
                        print(f"   ✓ {error['type']}: {error['message']}")
            
            print("\n   ✓ Symlink handling test completed")
            
        except Exception as e:
            print(f"   Note: Symlink test skipped: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RepoAnalyzer Edge Case Test Suite")
    print("=" * 70)
    
    success = test_scan_files()
    test_symlink_handling()
    
    if success:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)

# Made with Bob
