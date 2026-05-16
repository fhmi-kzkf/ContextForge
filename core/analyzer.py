import os
import ast
import logging
from typing import List, Dict, Any, Set
from pathlib import Path

# Configure logging for the analyzer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepoAnalyzer:
    EXCLUDE_DIRS = {
        "test", "tests", "benchmarks", "bench", "doc", "docs",
        "examples", "scripts", ".github", "build_tools", "build",
        "dist", "node_modules", "__pycache__", ".git", "asv_benchmarks",
        "contrib", "tools", "ci", "setup", "egg-info"
    }
    
    ENTRY_POINT_NAMES = {
        "predict", "inference", "run", "forward", "score", "classify",
        "detect", "generate", "infer", "batch_predict"
    }

    CLASS_KEYWORDS = {"model", "predictor", "classifier", "detector"}
    
    # Configuration constants for scan limits
    MAX_FILE_SIZE = 200 * 1024  # 200KB
    MAX_DEPTH = 10  # Maximum directory depth to prevent deep recursion
    MAX_SYMLINK_DEPTH = 3  # Maximum symlink follow depth

    def __init__(self, repo_path: str):
        """Accept path to extracted repo folder."""
        self.repo_path = repo_path
        self.analysis_data = {}
        self._cached_scan = None
        self._visited_paths: Set[str] = set()  # Track visited paths for symlink detection
        self._scan_errors: List[Dict[str, str]] = []  # Track errors during scanning

    def _is_safe_path(self, path: str, current_depth: int = 0) -> bool:
        """
        Check if a path is safe to traverse.
        Handles symlinks, depth limits, and circular references.
        
        Args:
            path: Path to check
            current_depth: Current directory depth
            
        Returns:
            bool: True if path is safe to traverse
        """
        try:
            # Check depth limit
            if current_depth > self.MAX_DEPTH:
                logger.warning(f"Skipping deep nested path (depth {current_depth}): {path}")
                self._scan_errors.append({
                    "type": "depth_limit",
                    "path": path,
                    "message": f"Exceeded maximum depth of {self.MAX_DEPTH}"
                })
                return False
            
            # Resolve real path to detect symlinks
            real_path = os.path.realpath(path)
            
            # Check if it's a symlink
            if os.path.islink(path):
                # Check if we've already visited this real path (circular reference)
                if real_path in self._visited_paths:
                    logger.warning(f"Skipping circular symlink: {path} -> {real_path}")
                    self._scan_errors.append({
                        "type": "circular_symlink",
                        "path": path,
                        "target": real_path,
                        "message": "Circular symlink reference detected"
                    })
                    return False
                
                logger.debug(f"Following symlink: {path} -> {real_path}")
            
            # Mark this path as visited
            self._visited_paths.add(real_path)
            return True
            
        except (OSError, ValueError) as e:
            logger.error(f"Error checking path safety for {path}: {e}")
            self._scan_errors.append({
                "type": "path_check_error",
                "path": path,
                "message": str(e)
            })
            return False

    def _safe_get_file_size(self, file_path: str) -> int:
        """
        Safely get file size with error handling.
        
        Args:
            file_path: Path to file
            
        Returns:
            int: File size in bytes, or -1 if error
        """
        try:
            return os.path.getsize(file_path)
        except (OSError, IOError) as e:
            logger.warning(f"Cannot get size for {file_path}: {e}")
            self._scan_errors.append({
                "type": "file_size_error",
                "path": file_path,
                "message": str(e)
            })
            return -1

    def _is_valid_file(self, file_path: str) -> bool:
        """
        Check if a file is valid and readable.
        
        Args:
            file_path: Path to file
            
        Returns:
            bool: True if file is valid and readable
        """
        try:
            # Check if file exists and is a regular file
            if not os.path.isfile(file_path):
                return False
            
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                logger.warning(f"File not readable: {file_path}")
                self._scan_errors.append({
                    "type": "permission_error",
                    "path": file_path,
                    "message": "File is not readable"
                })
                return False
            
            return True
            
        except (OSError, IOError) as e:
            logger.error(f"Error validating file {file_path}: {e}")
            self._scan_errors.append({
                "type": "validation_error",
                "path": file_path,
                "message": str(e)
            })
            return False

    def scan_files(self) -> dict:
        """
        Walk the repo directory tree with smart filtering and robust error handling.
        
        Improvements:
        - Symlink detection and circular reference prevention
        - Depth limiting to prevent deep recursion in test directories
        - File corruption and permission error handling
        - Comprehensive error logging
        - Safe file size checking
        
        Returns:
            dict: Scan results with file lists and metadata
        """
        if self._cached_scan:
            return self._cached_scan

        # Reset tracking for new scan
        self._visited_paths.clear()
        self._scan_errors.clear()

        all_python_files = []
        notebook_files = []
        config_files = []
        model_files = []
        
        config_names = {"requirements.txt", "setup.py", "pyproject.toml"}
        model_exts = {".pkl", ".pt", ".h5", ".onnx", ".joblib"}
        
        total_count = 0
        skipped_count = 0
        
        logger.info(f"Starting repository scan: {self.repo_path}")
        
        try:
            # Validate repo path exists
            if not os.path.exists(self.repo_path):
                logger.error(f"Repository path does not exist: {self.repo_path}")
                raise ValueError(f"Repository path does not exist: {self.repo_path}")
            
            for root, dirs, files in os.walk(self.repo_path, followlinks=False):
                try:
                    # Calculate current depth
                    rel_root = os.path.relpath(root, self.repo_path)
                    current_depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1
                    
                    # Check if current directory is safe to traverse
                    if not self._is_safe_path(root, current_depth):
                        dirs[:] = []  # Don't descend into this directory
                        skipped_count += 1
                        continue
                    
                    # Prune excluded directories from search
                    if any(part in self.EXCLUDE_DIRS for part in rel_root.split(os.sep)):
                        dirs[:] = []  # Don't descend into excluded directories
                        continue
                    
                    # Filter out excluded subdirectories before descending
                    dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

                    for file in files:
                        total_count += 1
                        full_path = os.path.join(root, file)
                        
                        # Validate file before processing
                        if not self._is_valid_file(full_path):
                            skipped_count += 1
                            continue
                        
                        rel_path = os.path.relpath(full_path, self.repo_path)
                        
                        try:
                            if file.endswith(".py"):
                                # Safe file size check
                                file_size = self._safe_get_file_size(full_path)
                                if file_size == -1:
                                    skipped_count += 1
                                    continue
                                
                                # File size guard
                                if file_size < self.MAX_FILE_SIZE:
                                    all_python_files.append(rel_path)
                                else:
                                    logger.debug(f"Skipping large Python file ({file_size} bytes): {rel_path}")
                                    skipped_count += 1
                                    
                            elif file.endswith(".ipynb"):
                                notebook_files.append(rel_path)
                            elif file in config_names:
                                config_files.append(rel_path)
                            elif any(file.endswith(ext) for ext in model_exts):
                                model_files.append(rel_path)
                                
                        except Exception as e:
                            logger.error(f"Error processing file {rel_path}: {e}")
                            self._scan_errors.append({
                                "type": "file_processing_error",
                                "path": rel_path,
                                "message": str(e)
                            })
                            skipped_count += 1
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing directory {root}: {e}")
                    self._scan_errors.append({
                        "type": "directory_error",
                        "path": root,
                        "message": str(e)
                    })
                    continue

        except Exception as e:
            logger.error(f"Critical error during repository scan: {e}")
            self._scan_errors.append({
                "type": "critical_scan_error",
                "path": self.repo_path,
                "message": str(e)
            })

        # Smart Filtering Strategy
        filtered_python = []
        strategy = "root"
        
        # Step 1: Root-level
        root_py = [f for f in all_python_files if os.sep not in f]
        if root_py:
            filtered_python = root_py[:20]
            strategy = "root"
        else:
            # Step 2: Shallow (Depth 2)
            shallow_py = [f for f in all_python_files if f.count(os.sep) == 1]
            if shallow_py:
                filtered_python = shallow_py[:30]
                strategy = "shallow"
            else:
                # Step 3: Fallback
                filtered_python = all_python_files[:50]
                strategy = "full"

        # Final cap
        filtered_python = filtered_python[:50]
        
        logger.info(f"Scan complete: {len(all_python_files)} Python files found, "
                   f"{len(filtered_python)} selected for analysis, "
                   f"{skipped_count} files skipped, "
                   f"{len(self._scan_errors)} errors encountered")

        results = {
            "all_python_files": all_python_files,
            "python_files": filtered_python,
            "notebook_files": notebook_files,
            "config_files": config_files,
            "model_files": model_files,
            "file_count_total": total_count,
            "file_count_analyzed": len(filtered_python),
            "file_count_skipped": skipped_count,
            "scan_strategy": strategy,
            "scan_errors": self._scan_errors.copy(),  # Include errors in results
            "error_count": len(self._scan_errors)
        }
        self._cached_scan = results
        return results

    def parse_python_file(self, file_path: str) -> dict:
        """
        Use Python's ast module to parse a .py file with robust error handling.
        
        Args:
            file_path: Relative path to Python file from repo root
            
        Returns:
            dict: Parsed file structure with imports, functions, classes, and variables
        """
        full_path = os.path.join(self.repo_path, file_path)
        
        try:
            # Check if file is readable
            if not os.access(full_path, os.R_OK):
                logger.warning(f"Cannot read file (permission denied): {file_path}")
                return {"imports": [], "functions": [], "classes": [], "global_vars": [], "parse_error": "permission_denied"}
            
            # Try to read and parse the file
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Check for empty or very small files
            if len(content.strip()) == 0:
                logger.debug(f"Skipping empty file: {file_path}")
                return {"imports": [], "functions": [], "classes": [], "global_vars": [], "parse_error": "empty_file"}
            
            tree = ast.parse(content, filename=file_path)
            
        except UnicodeDecodeError as e:
            logger.warning(f"Unicode decode error in {file_path}: {e}")
            # Try with different encoding
            try:
                with open(full_path, "r", encoding="latin-1") as f:
                    content = f.read()
                tree = ast.parse(content, filename=file_path)
            except Exception as e2:
                logger.error(f"Failed to parse {file_path} with alternate encoding: {e2}")
                return {"imports": [], "functions": [], "classes": [], "global_vars": [], "parse_error": "encoding_error"}
                
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return {"imports": [], "functions": [], "classes": [], "global_vars": [], "parse_error": "syntax_error"}
            
        except OSError as e:
            logger.error(f"OS error reading {file_path}: {e}")
            return {"imports": [], "functions": [], "classes": [], "global_vars": [], "parse_error": "os_error"}
            
        except Exception as e:
            logger.error(f"Unexpected error parsing {file_path}: {e}")
            return {"imports": [], "functions": [], "classes": [], "global_vars": [], "parse_error": "unknown_error"}

        imports = []
        functions = []
        classes = []
        global_vars = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        imports.append(n.name)
                else:
                    imports.append(node.module or "")
            
            elif isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node) or ""
                args = [arg.arg for arg in node.args.args]
                functions.append({
                    "name": node.name,
                    "args": args,
                    "docstring": docstring,
                    "is_method": False
                })
            
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node) or ""
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            "name": item.name,
                            "args": [arg.arg for arg in item.args.args],
                            "docstring": ast.get_docstring(item) or ""
                        })
                classes.append({
                    "name": node.name,
                    "methods": methods,
                    "docstring": docstring
                })
            
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        global_vars.append(target.id)

        return {
            "imports": sorted(list(set(imports))),
            "functions": functions,
            "classes": classes,
            "global_vars": global_vars
        }

    def detect_ml_framework(self) -> str:
        frameworks = {
            "sklearn": "sklearn", "torch": "pytorch", "tensorflow": "tensorflow",
            "keras": "keras", "xgboost": "xgboost"
        }
        
        all_imports = set()
        scan = self.scan_files()
        for py_file in scan["python_files"]:
            parsed = self.parse_python_file(py_file)
            all_imports.update(parsed["imports"])
            
        for imp in all_imports:
            for key, val in frameworks.items():
                if imp.startswith(key):
                    return val
        return "unknown"

    def find_entry_points(self) -> list:
        """
        Identify likely prediction/inference functions (BUG 2 FIX).
        """
        entry_points = []
        scan = self.scan_files()
        
        for py_file in scan["python_files"]:
            if "test" in py_file.lower():
                continue
                
            parsed = self.parse_python_file(py_file)
            
            # Check top-level functions
            for func in parsed["functions"]:
                if func["name"] in self.ENTRY_POINT_NAMES:
                    # At least 1 parameter
                    if len(func["args"]) >= 1:
                        entry_points.append({
                            "file": py_file,
                            "function_name": func["name"],
                            "args": func["args"],
                            "docstring": func["docstring"],
                            "priority": self._calculate_priority(py_file, func["name"])
                        })
            
            # Check class methods
            for cls in parsed["classes"]:
                is_model_class = any(kw in cls["name"].lower() for kw in self.CLASS_KEYWORDS)
                if is_model_class:
                    for method in cls["methods"]:
                        if method["name"] in self.ENTRY_POINT_NAMES:
                            # At least 1 param other than self
                            non_self_args = [a for a in method["args"] if a != "self"]
                            if len(non_self_args) >= 1:
                                entry_points.append({
                                    "file": py_file,
                                    "function_name": method["name"],
                                    "args": non_self_args,
                                    "docstring": method["docstring"],
                                    "priority": self._calculate_priority(py_file, method["name"])
                                })

        # Deduplicate and sort by priority
        entry_points.sort(key=lambda x: x["priority"], reverse=True)
        seen = {}
        unique_eps = []
        for ep in entry_points:
            if ep["function_name"] not in seen:
                seen[ep["function_name"]] = True
                # Clean up priority before returning
                ep.pop("priority")
                unique_eps.append(ep)
                
        return unique_eps

    def _calculate_priority(self, file_path: str, func_name: str) -> int:
        score = 0
        if os.sep not in file_path: score += 10
        if any(name in file_path.lower() for name in ["predict.py", "inference.py", "model.py"]):
            score += 20
        if func_name == "predict": score += 5
        return score

    def build_dependency_graph(self) -> dict:
        """
        Map which modules import which other modules within the repo (BUG 4A FIX).
        """
        scan = self.scan_files()
        filtered_files = scan["python_files"]
        all_python = scan["all_python_files"]
        
        module_names = {os.path.splitext(f)[0].replace(os.sep, '.') for f in all_python}
        
        full_graph = {}
        for py_file in all_python:
            mod_name = os.path.splitext(py_file)[0].replace(os.sep, '.')
            parsed = self.parse_python_file(py_file)
            internal_imports = [imp for imp in parsed["imports"] if imp in module_names]
            full_graph[mod_name] = internal_imports

        # Summary Graph
        summary_graph = {}
        centrality = {}
        
        # Filtered set of modules
        filtered_mod_names = {os.path.splitext(f)[0].replace(os.sep, '.') for f in filtered_files}
        
        for mod in filtered_mod_names:
            summary_graph[mod] = full_graph.get(mod, [])
            
        # Count incoming edges for centrality
        for mod, deps in full_graph.items():
            for dep in deps:
                centrality[dep] = centrality.get(dep, 0) + 1
        
        sorted_mods = sorted(summary_graph.keys(), key=lambda x: centrality.get(x, 0), reverse=True)
        summary_graph_final = {mod: summary_graph[mod] for mod in sorted_mods[:15]}
        
        return {
            "full_graph": full_graph,
            "summary_graph": summary_graph_final
        }

    def get_requirements(self) -> list:
        req_path = os.path.join(self.repo_path, "requirements.txt")
        if not os.path.exists(req_path): return []
        requirements = []
        try:
            with open(req_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        requirements.append(line)
        except Exception: pass
        return requirements

    def full_analysis(self) -> dict:
        scan = self.scan_files()
        framework = self.detect_ml_framework()
        entry_points = self.find_entry_points()
        dep_graph_data = self.build_dependency_graph()
        requirements = self.get_requirements()
        
        python_analysis = {}
        for py_file in scan["python_files"]:
            python_analysis[py_file] = self.parse_python_file(py_file)

        return {
            "repo_name": os.path.basename(self.repo_path),
            "scan": scan,
            "framework": framework,
            "entry_points": entry_points,
            "dependency_graph": dep_graph_data["full_graph"],
            "summary_graph": dep_graph_data["summary_graph"],
            "requirements": requirements,
            "python_analysis": python_analysis
        }
