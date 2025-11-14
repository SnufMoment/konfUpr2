import argparse
import sys
import json
import urllib.request
from urllib.parse import urljoin
from xml.etree import ElementTree as ET
import os

NUGET_SERVICE_INDEX = "https://api.nuget.org/v3/index.json"
PACKAGE_CONTENT_TYPE = "PackageBaseAddress/3.0.0"

def validate_package_name(name: str) -> str:
    if not name or not name.strip():
        raise ValueError("Package name cannot be empty.")
    return name.strip()

def validate_max_depth(depth_str: str) -> int:
    try:
        depth = int(depth_str)
    except ValueError:
        raise ValueError("Max depth must be an integer.")
    if depth < 0:
        raise ValueError("Max depth must be non-negative.")
    return depth

def should_skip_package(pkg_name: str, filter_substring: str) -> bool:
    if not filter_substring:
        return False
    return filter_substring in pkg_name


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode('utf-8'))

def fetch_xml(url: str) -> ET.Element:
    with urllib.request.urlopen(url) as response:
        return ET.fromstring(response.read().decode('utf-8'))

def get_nuget_base_url() -> str:
    index = fetch_json(NUGET_SERVICE_INDEX)
    for resource in index.get("resources", []):
        if resource.get("@type") == PACKAGE_CONTENT_TYPE:
            return resource["@id"]
    raise RuntimeError("NuGet PackageBaseAddress not found.")

def get_latest_version(base_url: str, package_id: str) -> str:
    package_id_lower = package_id.lower()
    versions_url = f"{base_url.rstrip('/')}/{package_id_lower}/index.json"
    data = fetch_json(versions_url)
    versions = data.get("versions", [])
    if not versions:
        raise RuntimeError(f"No versions found for package '{package_id}'")
    return max(versions)

def extract_dependencies(nuspec_root: ET.Element) -> list:
    ns = {'ns': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}
    metadata = nuspec_root.find('ns:metadata', ns)
    if metadata is None:
        return []

    deps_groups = metadata.find('ns:dependencies', ns)
    if deps_groups is None:
        return []

    seen = set()
    deps = []

    def add(dep_id, dep_version):
        key = (dep_id, dep_version)
        if key not in seen:
            seen.add(key)
            deps.append(dep_id)  # Only name needed for graph

    for group in deps_groups.findall('ns:group', ns):
        for dep in group.findall('ns:dependency', ns):
            dep_id = dep.get('id')
            if dep_id:
                add(dep_id, dep.get('version', ''))

    for dep in deps_groups.findall('ns:dependency', ns):
        dep_id = dep.get('id')
        if dep_id:
            add(dep_id, dep.get('version', ''))

    return deps

def get_nuget_direct_deps(package_id: str) -> list:
    base_url = get_nuget_base_url()
    version = get_latest_version(base_url, package_id)
    package_id_lower = package_id.lower()
    nuspec_url = f"{base_url}/{package_id_lower}/{version}/{package_id_lower}.nuspec"
    root = fetch_xml(nuspec_url)
    return extract_dependencies(root)


def load_test_repo(repo_path: str) -> dict:
    if not os.path.isfile(repo_path):
        raise ValueError(f"Test repo file not found: {repo_path}")
    with open(repo_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for pkg in data:
            if not pkg.isupper() or not pkg.isalpha():
                raise ValueError(f"Invalid package name in test repo: '{pkg}' (must be uppercase letters only)")
        return data

def get_test_direct_deps(package_id: str, test_repo: dict) -> list:
    return test_repo.get(package_id, [])


def dfs_build_graph(
    current: str,
    depth: int,
    max_depth: int,
    filter_substring: str,
    visited_path: set,
    graph: dict,
    get_deps_func,
    **kwargs
):
    if depth > max_depth:
        return

    if should_skip_package(current, filter_substring):
        return

    if current in visited_path:
        return

    if current not in graph:
        graph[current] = []

    try:
        direct_deps = get_deps_func(current, **kwargs)
    except Exception as e:
        print(f"⚠️ Warning: failed to fetch dependencies for '{current}': {e}", file=sys.stderr)
        return

    filtered_deps = [
        dep for dep in direct_deps
        if not should_skip_package(dep, filter_substring)
    ]

    graph[current] = filtered_deps

    new_visited = visited_path | {current}
    for dep in filtered_deps:
        if dep not in graph or depth + 1 <= max_depth:
            dfs_build_graph(
                dep,
                depth + 1,
                max_depth,
                filter_substring,
                new_visited,
                graph,
                get_deps_func,
                **kwargs
            )


def topological_sort(graph: dict) -> list:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    result = []
    in_cycle = set()

    def dfs(node):
        if color[node] == GRAY:
            in_cycle.add(node)
            return False
        if color[node] == BLACK:
            return True

        color[node] = GRAY
        for dep in graph.get(node, []):
            if dep not in graph:
                continue
            if not dfs(dep):
                in_cycle.add(node)
                color[node] = WHITE
                return False
        color[node] = BLACK
        result.append(node)
        return True

    for node in graph:
        if color[node] == WHITE:
            dfs(node)

    safe_order = [node for node in result if node not in in_cycle]
    return safe_order



def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Stage 4: Build dependency graph and output installation order (topological sort)."
    )
    parser.add_argument("--package", required=True, help="Root package name.")
    parser.add_argument("--repo", required=True, help="URL (online) or path to test repo JSON (test mode).")
    parser.add_argument("--mode", required=True, choices=["online", "test"], help="Operation mode.")
    parser.add_argument("--max-depth", required=True, help="Max traversal depth (non-negative integer).")
    parser.add_argument("--filter", default="", help="Substring to exclude packages containing it.")

    args = parser.parse_args()

    package = validate_package_name(args.package)
    max_depth = validate_max_depth(args.max_depth)
    filter_substring = args.filter

    if args.mode == "test":
        if not os.path.exists(args.repo):
            raise ValueError(f"In test mode, --repo must be an existing file: {args.repo}")
    else:
        if not args.repo.startswith(('http://', 'https://')):
            raise ValueError("--repo must be a URL in online mode")

    return {
        "package": package,
        "repo": args.repo,
        "mode": args.mode,
        "max_depth": max_depth,
        "filter": filter_substring
    }


def main():
    config = parse_arguments()

    print("Configuration:")
    for k, v in config.items():
        print(f"  {k}: {v}")
    print()

    graph = {}

    if config["mode"] == "test":
        test_repo = load_test_repo(config["repo"])
        dfs_build_graph(
            current=config["package"],
            depth=0,
            max_depth=config["max_depth"],
            filter_substring=config["filter"],
            visited_path=set(),
            graph=graph,
            get_deps_func=get_test_direct_deps,
            test_repo=test_repo
        )
    else:
        dfs_build_graph(
            current=config["package"],
            depth=0,
            max_depth=config["max_depth"],
            filter_substring=config["filter"],
            visited_path=set(),
            graph=graph,
            get_deps_func=get_nuget_direct_deps
        )

    print("Dependency graph:")
    if not graph:
        print("  (empty)")
    else:
        for pkg, deps in graph.items():
            print(f"  {pkg} -> {deps}")

    print()

    install_order = topological_sort(graph)
    print("Installation (load) order:")
    if not install_order:
        print("  (no safe order — all packages in cycles or empty)")
    else:
        for i, pkg in enumerate(install_order, 1):
            print(f"  {i}. {pkg}")

    if config["mode"] == "online":
        print("\nℹ️  Comparison note:")
        print("   NuGet resolves dependencies using version constraints and")
        print("   may select different versions than the latest. Our tool")
        print("   uses the latest version and ignores version ranges,")
        print("   so order may differ from `dotnet restore` or Visual Studio.")


if __name__ == "__main__":
    main()