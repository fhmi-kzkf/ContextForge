import ast
import os

class ASTParser:
    """
    Utilities for parsing Python code using AST to identify classes, functions, and imports.
    """
    @staticmethod
    def parse_file(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        return tree

    @staticmethod
    def get_imports(tree):
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"{node.module}.{node.names[0].name}")
        return imports

    @staticmethod
    def get_classes(tree):
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes

    @staticmethod
    def get_functions(tree):
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions

def parse_module_info(file_path):
    """
    Convenience function used by RepoAnalyzer.
    """
    try:
        parser = ASTParser()
        tree = parser.parse_file(file_path)
        return {
            "file": os.path.basename(file_path),
            "imports": parser.get_imports(tree),
            "classes": parser.get_classes(tree),
            "functions": parser.get_functions(tree)
        }
    except Exception as e:
        return {"file": os.path.basename(file_path), "error": str(e)}
