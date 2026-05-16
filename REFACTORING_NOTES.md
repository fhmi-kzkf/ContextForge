# RepoAnalyzer Refactoring - Edge Case Handling

## Overview
This document describes the refactoring of the `scan_files()` function in `core/analyzer.py` to include robust error handling for various edge cases that can occur during repository analysis.

## Date
May 16, 2026

## Changes Made

### 1. Enhanced Imports and Logging
- Added `logging` module for comprehensive error tracking
- Added `Set` type hint from typing module
- Added `Path` from pathlib for better path handling
- Configured logger for the analyzer module

### 2. New Class Constants
```python
MAX_FILE_SIZE = 200 * 1024  # 200KB file size limit
MAX_DEPTH = 10              # Maximum directory depth
MAX_SYMLINK_DEPTH = 3       # Maximum symlink follow depth
```

### 3. New Instance Variables
- `_visited_paths: Set[str]` - Tracks visited paths to detect circular symlinks
- `_scan_errors: List[Dict[str, str]]` - Collects all errors encountered during scanning

### 4. New Helper Methods

#### `_is_safe_path(path: str, current_depth: int) -> bool`
**Purpose**: Validates if a path is safe to traverse

**Features**:
- Checks directory depth against `MAX_DEPTH` limit
- Detects and handles symlinks
- Prevents circular symlink references
- Tracks visited paths to avoid infinite loops
- Logs warnings for skipped paths

**Error Types Handled**:
- `depth_limit`: Directory exceeds maximum depth
- `circular_symlink`: Circular symlink reference detected
- `path_check_error`: OS-level path validation errors

#### `_safe_get_file_size(file_path: str) -> int`
**Purpose**: Safely retrieves file size with error handling

**Features**:
- Returns -1 on error instead of raising exception
- Handles OSError and IOError gracefully
- Logs warnings for inaccessible files

**Error Types Handled**:
- `file_size_error`: Cannot determine file size

#### `_is_valid_file(file_path: str) -> bool`
**Purpose**: Validates file accessibility and readability

**Features**:
- Checks if path is a regular file
- Verifies read permissions
- Handles permission errors gracefully

**Error Types Handled**:
- `permission_error`: File is not readable
- `validation_error`: General file validation errors

### 5. Refactored `scan_files()` Method

#### New Features:
1. **Initialization**
   - Clears tracking sets for each scan
   - Resets error collection

2. **Repository Validation**
   - Validates repository path exists before scanning
   - Raises clear error if path is invalid

3. **Enhanced Directory Walking**
   - Calculates current depth for each directory
   - Uses `_is_safe_path()` to validate before descending
   - Prunes excluded directories more efficiently
   - Filters subdirectories before traversal

4. **Robust File Processing**
   - Validates each file with `_is_valid_file()`
   - Uses safe file size checking
   - Wraps file processing in try-except blocks
   - Continues on individual file errors

5. **Comprehensive Error Tracking**
   - Tracks skipped file count
   - Collects all errors with context
   - Includes error details in scan results

6. **Enhanced Return Data**
   ```python
   {
       "all_python_files": [...],
       "python_files": [...],
       "notebook_files": [...],
       "config_files": [...],
       "model_files": [...],
       "file_count_total": int,
       "file_count_analyzed": int,
       "file_count_skipped": int,      # NEW
       "scan_strategy": str,
       "scan_errors": [...],            # NEW
       "error_count": int               # NEW
   }
   ```

### 6. Enhanced `parse_python_file()` Method

#### New Features:
1. **Permission Checking**
   - Validates file read permissions before parsing
   - Returns error indicator for permission denied

2. **Empty File Detection**
   - Checks for empty or whitespace-only files
   - Avoids unnecessary parsing attempts

3. **Multi-Encoding Support**
   - Primary attempt with UTF-8 encoding
   - Fallback to latin-1 encoding for legacy files
   - Handles UnicodeDecodeError gracefully

4. **Specific Error Handling**
   - `SyntaxError`: Invalid Python syntax
   - `UnicodeDecodeError`: Encoding issues
   - `OSError`: File system errors
   - Generic `Exception`: Unexpected errors

5. **Error Reporting**
   - Returns `parse_error` field in result dict
   - Provides specific error type for debugging

## Edge Cases Handled

### 1. Symlinks
- **Detection**: Uses `os.path.islink()` and `os.path.realpath()`
- **Circular References**: Tracks visited real paths
- **Logging**: Warns when circular symlinks are detected
- **Action**: Skips circular symlinks, follows valid ones

### 2. Deep Nested Directories
- **Detection**: Calculates directory depth during traversal
- **Limit**: Configurable `MAX_DEPTH` (default: 10 levels)
- **Common Case**: Deep test directories that slow analysis
- **Action**: Stops descending beyond depth limit

### 3. Corrupted Files
- **Detection**: Multiple encoding attempts (UTF-8, latin-1)
- **Syntax Errors**: Caught and logged during AST parsing
- **Action**: Returns empty structure with error indicator

### 4. Permission Errors
- **Detection**: Uses `os.access()` with `os.R_OK`
- **File System Errors**: Catches OSError and IOError
- **Action**: Skips inaccessible files, logs warning

### 5. Large Files
- **Detection**: Safe file size checking before processing
- **Limit**: 200KB for Python files
- **Action**: Skips files exceeding size limit

### 6. Empty Files
- **Detection**: Checks content length after reading
- **Action**: Returns empty structure with error indicator

## Error Types Tracked

| Error Type | Description | Action |
|------------|-------------|--------|
| `depth_limit` | Directory exceeds max depth | Skip directory |
| `circular_symlink` | Circular symlink detected | Skip symlink |
| `path_check_error` | Path validation failed | Skip path |
| `file_size_error` | Cannot determine file size | Skip file |
| `permission_error` | File not readable | Skip file |
| `validation_error` | File validation failed | Skip file |
| `file_processing_error` | Error processing file | Skip file |
| `directory_error` | Error processing directory | Skip directory |
| `critical_scan_error` | Critical scan failure | Log and continue |

## Testing

A comprehensive test suite (`test_analyzer_edge_cases.py`) was created to verify:

1. ✅ Normal file processing
2. ✅ Large file handling (>200KB)
3. ✅ Empty file detection
4. ✅ Syntax error handling
5. ✅ Unicode/encoding issues
6. ✅ Deep nested directories (>10 levels)
7. ✅ Excluded directory filtering
8. ✅ Config and model file detection
9. ✅ Symlink handling (platform-dependent)
10. ✅ Circular reference prevention

### Test Results
```
✓ All edge case tests completed successfully!
- Total files found: 8
- Python files analyzed: 4
- Files skipped: 2
- Errors encountered: 1 (depth_limit)
```

## Performance Considerations

1. **Early Pruning**: Excluded directories are pruned before traversal
2. **Depth Limiting**: Prevents excessive recursion in deep structures
3. **Size Checking**: Large files are skipped early
4. **Caching**: Scan results are cached to avoid re-scanning
5. **Lazy Evaluation**: Only analyzes filtered subset of files

## Backward Compatibility

✅ **Fully backward compatible**
- All existing return fields preserved
- New fields are additions only
- Existing code will continue to work
- Enhanced error handling is transparent to callers

## Usage Example

```python
from core.analyzer import RepoAnalyzer

analyzer = RepoAnalyzer("/path/to/repo")
results = analyzer.scan_files()

# Check for errors
if results['error_count'] > 0:
    print(f"Encountered {results['error_count']} errors during scan")
    for error in results['scan_errors']:
        print(f"  - {error['type']}: {error['message']}")

# Process files
for py_file in results['python_files']:
    parsed = analyzer.parse_python_file(py_file)
    if 'parse_error' in parsed:
        print(f"Could not parse {py_file}: {parsed['parse_error']}")
    else:
        print(f"Successfully parsed {py_file}")
```

## Future Enhancements

Potential improvements for future iterations:

1. **Configurable Limits**: Make MAX_DEPTH and MAX_FILE_SIZE configurable
2. **Parallel Processing**: Add option for concurrent file scanning
3. **Progress Callbacks**: Support progress reporting for large repos
4. **Binary File Detection**: Better handling of binary files
5. **Git Integration**: Use .gitignore patterns for exclusion
6. **Metrics Collection**: Track scan performance metrics

## Conclusion

The refactored `scan_files()` function now provides:
- ✅ Robust error handling for all edge cases
- ✅ Comprehensive logging for debugging
- ✅ Protection against infinite loops and deep recursion
- ✅ Graceful degradation on errors
- ✅ Detailed error reporting
- ✅ Backward compatibility
- ✅ Improved maintainability

The analyzer is now production-ready for handling real-world repositories with various edge cases and potential issues.