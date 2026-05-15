import os
import ast
from typing import List, Dict, Any

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

    def __init__(self, repo_path: str):
        """Accept path to extracted repo folder."""
        self.repo_path = repo_path
        self.analysis_data = {}
        self._cached_scan = None

    def scan_files(self) -> dict:
        """
        Walk the repo directory tree with smart filtering (BUG 1 FIX).
        """
        if self._cached_scan:
            return self._cached_scan

        all_python_files = []
        notebook_files = []
        config_files = []
        model_files = []
        
        config_names = {"requirements.txt", "setup.py", "pyproject.toml"}
        model_exts = {".pkl", ".pt", ".h5", ".onnx", ".joblib"}
        
        total_count = 0
        for root, dirs, files in os.walk(self.repo_path):
            rel_root = os.path.relpath(root, self.repo_path)
            
            # Prune excluded directories from search
            if any(part in self.EXCLUDE_DIRS for part in rel_root.split(os.sep)):
                continue

            for file in files:
                total_count += 1
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.repo_path)
                
                if file.endswith(".py"):
                    # File size guard (200KB)
                    if os.path.getsize(full_path) < 200 * 1024:
                        all_python_files.append(rel_path)
                elif file.endswith(".ipynb"):
                    notebook_files.append(rel_path)
                elif file in config_names:
                    config_files.append(rel_path)
                elif any(file.endswith(ext) for ext in model_exts):
                    model_files.append(rel_path)

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

        results = {
            "all_python_files": all_python_files, # For background analysis if needed
            "python_files": filtered_python,
            "notebook_files": notebook_files,
            "config_files": config_files,
            "model_files": model_files,
            "file_count_total": total_count,
            "file_count_analyzed": len(filtered_python),
            "scan_strategy": strategy
        }
        self._cached_scan = results
        return results

    def parse_python_file(self, file_path: str) -> dict:
        """
        Use Python's ast module to parse a .py file.
        """
        try:
            with open(os.path.join(self.repo_path, file_path), "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception:
            return {"imports": [], "functions": [], "classes": [], "global_vars": []}

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
