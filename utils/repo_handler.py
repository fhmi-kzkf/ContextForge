import os
import shutil
import zipfile
import io
import stat
import re
try:
    from git import Repo
except ImportError:
    Repo = None

def remove_readonly(func, path, excinfo):
    """Error handler for shutil.rmtree to handle read-only files (like in .git) on Windows."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clean_repo_name(name: str) -> str:
    """Strip version numbers or hashes from repo name (BUG 6 FIX)."""
    # Remove things like -1.4.0, -master, -abc1234
    name = re.sub(r'[-_.]([0-9]+(\.[0-9]+)*|master|main|[a-f0-9]{7,40})$', '', name, flags=re.IGNORECASE)
    return name or "my-ml-project"

def extract_zip(uploaded_file, extract_to: str) -> tuple:
    """
    Extract .zip upload to a temp directory. 
    Return (path_to_extracted_root, cleaned_repo_name).
    """
    if os.path.exists(extract_to):
        shutil.rmtree(extract_to, onerror=remove_readonly)
    os.makedirs(extract_to)
    
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    # Detect actual repo name (BUG 6 FIX)
    contents = os.listdir(extract_to)
    repo_name = "my-ml-project"
    
    if len(contents) == 1 and os.path.isdir(os.path.join(extract_to, contents[0])):
        # Case 1: Single top-level folder
        repo_name = contents[0]
        actual_path = os.path.join(extract_to, contents[0])
    else:
        # Case 2: Flat extraction
        zip_filename = getattr(uploaded_file, 'name', 'my-ml-project.zip')
        repo_name = os.path.splitext(zip_filename)[0]
        actual_path = extract_to

    cleaned_name = clean_repo_name(repo_name)
    return actual_path, cleaned_name

def clone_github_repo(github_url: str, clone_to: str) -> tuple:
    """Git clone a public repo. Return (path, cleaned_repo_name)."""
    if os.path.exists(clone_to):
        shutil.rmtree(clone_to, onerror=remove_readonly)
    
    if Repo:
        Repo.clone_from(github_url, clone_to)
    else:
        raise ImportError("GitPython is not installed or git is not in PATH")
    
    # Extract name from URL
    repo_name = github_url.rstrip('/').split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
        
    return clone_to, clean_repo_name(repo_name)

def build_file_tree(root_path: str) -> str:
    """Return a formatted string representation of the directory tree."""
    tree = []
    for root, dirs, files in os.walk(root_path):
        level = root.replace(root_path, '').count(os.sep)
        indent = ' ' * 4 * level
        tree.append(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            tree.append(f'{subindent}{f}')
    return "\n".join(tree)

def read_all_python_files(root_path: str) -> dict:
    """Return {relative_path: file_content} for all .py files in the repo."""
    py_files = {}
    for root, _, files in os.walk(root_path):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        py_files[rel_path] = f.read()
                except Exception:
                    continue
    return py_files

def create_output_zip(file_dict: dict) -> bytes:
    """
    Accept {filename: content_string} dict.
    Create an in-memory zip file.
    Return bytes for st.download_button.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in file_dict.items():
            zip_file.writestr(filename, content)
    return buf.getvalue()
