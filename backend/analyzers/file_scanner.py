import os

# CONSTANTS

# file types that are scanned
# keeping it to Python for now
SUPPORTED_EXTENSIONS = ['.py']

# files and folders to completely ignore
# files with no useful code to analyse
IGNORED_DIRS = {
    '.git', # Git internal files
    '__pycache__', # Python compiled cache
    'venv', # Virtuak environments
    'env',
    '.env',
    'node_modules', # JavaScript packages
    '.idea', #IDE config files
    '.vscode',
    'dist', # build output
    'build',
    'eggs',
    '.eggs',
    '*.egg-info',
    'migrations', # database migrations
}

IGNORED_FILES = {
    '__init__.py', # not useful to analyse
    'setup.py', # package setup not business logic
    'conftest.py', #Pytest config
}

# if a file is bigger than this skip it
# very large files are usually auto generated
MAX_FILE_SIZE_KB = 500

# HELPER FUNCTIONS

def should_ignore_directory(dir_name: str) -> bool:
    """
    returns True if we should skip this entire directory
    """
    return dir_name in IGNORED_DIRS or dir_name.startswith('.')

def should_ignore_file(file_name: str, file_size_bytes: int) -> bool:
    """
    returns True if we should skip this specific file
    """
    # skip files in the ignore list
    if file_name in IGNORED_FILES:
        return True
    
    # skip files that are too large
    file_size_kb = file_size_bytes / 1024
    if file_size_kb > MAX_FILE_SIZE_KB:
        return True
    
    return False

def get_file_extension(file_name: str) -> str:
    """
    returns the file extension
    """
    _, ext = os.path.splitext(file_name)
    return ext.lower()

def read_file_safely(file_path: str) -> str | None:
    """
    reads a file and returns its content as a string
    returns None if the file can't be read

    trying UTF-8 first (most common) then fall back to latin-1
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception:
            return None
    except Exception:
        return None

def count_lines(content: str) -> dict:
    """
    counts different types of lines in a file

    returns:
        - total: all lines
        - code: actual code lines
        - blank: empty lines
        - comments: lines starting with #
    """
    lines = content.split('\n')
    total = len(lines)
    blank = sum(1 for line in lines if line.strip() == '')
    comments = sum(1 for line in lines if line.strip().startswith('#'))
    code = total - blank - comments

    return {
        "total": total,
        "code": code,
        "blank": blank,
        "comments": comments
    }

def extract_functions_and_classes(content: str) -> dict:
    """
    does a simple scan for function and class definitions
    no complex parsing just looks for 'def ' and 'class ' at the start of lines

    this gives useful metadata about what is in each file
    """
    lines = content.split('\n')
    functions = []
    classes = []

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # look for function definitions
        if stripped.startswith('def '):
            # extract just the function name
            try:
                func_name = stripped[4:].split('(')[0].strip()
                functions.append({
                    "name": func_name,
                    "line_number": i
                })
            except Exception:
                pass
        
        # look for class definitions
        elif stripped.startswith('class'):
            try:
                class_name = stripped[6:].split('(')[0].split(':')[0].strip()
                classes.append({
                    "name": class_name,
                    "line_number": i
                })
            except Exception:
                pass

    return {
        "functions": function,
        "classes": classes,
        "function_count": len(functions),
        "class_count": len(classes)
    }