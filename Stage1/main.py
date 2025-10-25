import argparse
import sys
import os
from urllib.parse import urlparse

def validate_package_name(name: str) -> str:
    if not name or not name.strip():
        raise ValueError("Package name cannot be empty.")
    return name.strip()

def validate_repo_url_or_path(repo: str) -> str:
    repo = repo.strip()
    if not repo:
        raise ValueError("Repository URL or path cannot be empty.")
    parsed = urlparse(repo)
    if parsed.scheme in ('http', 'https', 'file'):
        return repo
    elif os.path.exists(repo):

        return os.path.abspath(repo)
    else:
        raise ValueError(f"Repository must be a valid URL or an existing file path: '{repo}'")

def validate_mode(mode: str) -> str:
    allowed_modes = {'online', 'offline', 'test'}
    mode = mode.lower().strip()
    if mode not in allowed_modes:
        raise ValueError(f"Mode must be one of {allowed_modes}, got '{mode}'")
    return mode

def validate_max_depth(depth_str: str) -> int:
    try:
        depth = int(depth_str)
    except ValueError:
        raise ValueError("Max depth must be an integer.")
    if depth < 0:
        raise ValueError("Max depth must be non-negative.")
    return depth

def validate_filter_substring(substring: str) -> str:
    return substring if substring is not None else ""

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Visualize package dependency graph (Stage 1: Configurable CLI prototype)."
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Name of the package to analyze."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="URL of the repository or path to a test repository file."
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["online", "offline", "test"],
        help="Operation mode: online (real repo), offline/test (mocked data)."
    )
    parser.add_argument(
        "--max-depth",
        required=True,
        help="Maximum depth for dependency traversal (non-negative integer)."
    )
    parser.add_argument(
        "--filter",
        default="",
        help="Substring to filter package names (optional)."
    )

    args = parser.parse_args()

    try:
        package = validate_package_name(args.package)
        repo = validate_repo_url_or_path(args.repo)
        mode = validate_mode(args.mode)
        max_depth = validate_max_depth(args.max_depth)
        filter_substring = validate_filter_substring(args.filter)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    return {
        "package": package,
        "repo": repo,
        "mode": mode,
        "max_depth": max_depth,
        "filter": filter_substring
    }

def main():
    config = parse_arguments()
    for key, value in config.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()