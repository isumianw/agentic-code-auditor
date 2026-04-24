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

# MAIN SCANNER FUNCTION

def scan_repository(local_path: str) -> dict:
    """
    main function - scans an entire repository and returns all file data

    takes:
        local_path - the path to the cloned repo

    returns:
        a dict with:
        - success
        - repo_path
        - summary (counts, totals)
        - files (list of file data)
        - errors (any files that failed)
    """

    # check the repo actually exists
    if not os.path.exists(local_path):
        return {
            "success": False,
            "repo_path": local_path,
            "summary": {},
            "files": [],
            "errors": [f"Repository path does not exist: {local_path}"]
        }
    
    scanned_files = []
    skipped_files = []
    errors = []

    print(f"\nScanning repository: {local_path}")
    print("-" * 50)

    # os.walk() visits every single folder and subfolder in the repo
    # for each folder it gives:
    #   root = current folder path
    #   dirs = list of subfolders in it
    #   files = list of files in it
    for root, dirs, files in os.walk(local_path):
        # filter out directors that need to be ignored
        dirs[:] = [
            d for d in dirs
            if not should_ignore_directory(d)
        ]

        # process each file
        for file_name in files:
            # only process supported file types
            extension = get_file_extension(file_name)
            if extension not in SUPPORTED_EXTENSIONS:
                continue

            # build the full path to this file
            file_path = os.path.join(root, file_name)

            # get file size
            try:
                file_size_bytes = os.path.getsize(file_path)
            except OSError:
                errors.append(f"Could not get size of: {file_path}")
                continue

            # check if this file should be skipped
            if should_ignore_file(file_name, file_size_bytes):
                skipped_files.append(file_name)
                continue

            # read the file content
            content = read_file_safely(file_path)
            if content is None:
                errors.append(f"Could not read file: {file_path}")
                continue

            # build a clean relative path
            relative_path = os.path.relpath(file_path, local_path)
            # normalise slashes for consistency
            relative_path = relative_path.replace('\\', '/')

            # count lines
            line_info = count_lines(content)

            # extract structure info
            structure = extract_functions_and_classes(content)

            # package everything about this file
            file_data = {
                "file_name": file_name,
                "relative_path": relative_path,
                "absolute_path": file_path,
                "extension": extension,
                "size_bytes": file_size_bytes,
                "size_kb": round(file_size_bytes / 1024, 2),
                "lines": line_info,
                "structure": structure,
                "content": content
            }

            scanned_files.append(file_data)
            print(f"  ✓ {relative_path} ({line_info['total']} lines)")

    
    # build the summary
    total_lines = sum(f["lines"]["total"] for f in scanned_files)
    total_functions = sum(f["structure"]["function_count"] for f in scanned_files)
    total_classes = sum(f["structure"]["class_count"] for f in scanned_files)

    summary = {
        "total_files_scanned": len(scanned_files),
        "total_files_skipped": len(skipped_files),
        "total_lines_of_code": total_lines,
        "total_functions_found": total_functions,
        "total_classes_found": total_classes,
        "languages_detected": ["Python"],
        "skipped_files": skipped_files
    }

    print(f"\nScan complete:")
    print(f"  Files scanned : {summary['total_files_scanned']}")
    print(f"  Total lines   : {summary['total_lines_of_code']}")
    print(f"  Functions     : {summary['total_functions_found']}")
    print(f"  Classes       : {summary['total_classes_found']}")

    return {
        "success": True,
        "repo_path": local_path,
        "summary": summary,
        "files": scanned_files,
        "errors": errors
    }

def get_file_by_path(local_path: str, relative_file_path: str) -> dict:
    """
    gets data for a single specific file in the repo
    useful to analyse just one file
    """
    full_path = os.path.join(local_path, relative_file_path)

    if not os.path.exists(full_path):
        return {
            "success": False,
            "message": f"File not found: {relative_file_path}"
        }
    
    content = read_file_safely(full_path)
    if content is None:
        return {
            "success": False,
            "message": f"Could not read file: {relative_file_path}"
        }
    
    file_size_bytes = os.path.getsize(full_path)
    line_info = count_lines(content)
    structure = extract_functions_and_classes(content)

    return {
        "success": True,
        "file_name": os.path.basename(full_path),
        "relative_path": relative_file_path,
        "size_kb": round(file_size_bytes / 1024, 2),
        "lines": line_info,
        "structure": structure,
        "content": content
    }