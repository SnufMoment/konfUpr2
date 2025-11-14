import argparse
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET
import subprocess
import os


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


def get_nuget_direct_deps(package_id: str) -> list:
    try:
        package_id_lower = package_id.lower()
        versions_url = f"https://api.nuget.org/v3-flatcontainer/{package_id_lower}/index.json"
        with urllib.request.urlopen(versions_url) as r:
            versions = json.loads(r.read().decode())["versions"]
        version = max(versions)
        nuspec_url = f"https://api.nuget.org/v3-flatcontainer/{package_id_lower}/{version}/{package_id_lower}.nuspec"
        with urllib.request.urlopen(nuspec_url) as r:
            root = ET.fromstring(r.read().decode())
        ns = {'ns': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}
        metadata = root.find('ns:metadata', ns)
        if metadata is None:
            return []
        deps_node = metadata.find('ns:dependencies', ns)
        if deps_node is None:
            return []
        deps = []
        for group in deps_node.findall('ns:group', ns):
            for dep in group.findall('ns:dependency', ns):
                i = dep.get('id')
                if i and i not in deps:
                    deps.append(i)
        for dep in deps_node.findall('ns:dependency', ns):
            i = dep.get('id')
            if i and i not in deps:
                deps.append(i)
        return deps
    except Exception as e:
        print(f"  Error: {e}")
        return []


def load_test_repo(repo_path: str) -> dict:
    if not os.path.isfile(repo_path):
        raise ValueError(f"Test repo file not found: {repo_path}")
    with open(repo_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for pkg in data.keys():
            if not (pkg.isupper() and pkg.isalpha()):
                raise ValueError(f"Invalid package name: '{pkg}' (must be uppercase letters only)")
        return data


def get_test_direct_deps(package_id: str, test_repo: dict) -> list:
    return test_repo.get(package_id, [])


def dfs_build_graph(current: str, depth: int, max_depth: int, filter_substring: str, visited_path: set, graph: dict,
                    processed: set, get_deps_func, **kwargs):
    if depth > max_depth:
        return
    if should_skip_package(current, filter_substring):
        return
    if current in visited_path:
        return
    if current in processed:
        return

    print(f"Processing: {current} (depth {depth})")
    new_visited = visited_path | {current}

    try:
        direct_deps = get_deps_func(current, **kwargs)
        print(f"Dependencies of {current}: {direct_deps}")
    except Exception as e:
        print(f"Error getting dependencies for {current}: {str(e)}")
        processed.add(current)
        return

    filtered_deps = [dep for dep in direct_deps if not should_skip_package(dep, filter_substring)]
    graph[current] = filtered_deps
    print(f"Added to graph: {current} -> {filtered_deps}")

    for dep in filtered_deps:
        dfs_build_graph(dep, depth + 1, max_depth, filter_substring, new_visited, graph, processed, get_deps_func,
                        **kwargs)
    processed.add(current)


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
    return [node for node in result if node not in in_cycle]


def generate_d2_code(graph: dict) -> str:
    if not graph:
        return "# Empty dependency graph"
    lines = []
    lines.append("// Dependency graph in D2 format")
    lines.append("direction: right")
    added = set()
    for pkg, deps in graph.items():
        if pkg not in added:
            lines.append(f'"{pkg}"')
            added.add(pkg)
        for dep in deps:
            if dep not in added:
                lines.append(f'"{dep}"')
                added.add(dep)
            lines.append(f'"{pkg}" -> "{dep}"')
    return "\n".join(lines)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Stage 5: Build, analyze, and visualize dependency graph (D2 format).")
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
        processed = set()
        dfs_build_graph(
            current=config["package"],
            depth=0,
            max_depth=config["max_depth"],
            filter_substring=config["filter"],
            visited_path=set(),
            graph=graph,
            processed=processed,
            get_deps_func=get_test_direct_deps,
            test_repo=test_repo
        )
    else:
        processed = set()
        dfs_build_graph(
            current=config["package"],
            depth=0,
            max_depth=config["max_depth"],
            filter_substring=config["filter"],
            visited_path=set(),
            graph=graph,
            processed=processed,
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
    print()
    d2_code = generate_d2_code(graph)
    print("D2 diagram code:")
    print("=" * 40)
    print(d2_code)
    output_name = config['package'] + "_dependencies"
    export_d2_to_image(d2_code, output_name)
    print("=" * 40)
    if config["mode"] == "online":
        print("\nℹ️  Comparison note:")
        print("   Our tool uses the official NuGet Search API")
        print("   and shows dependencies of the latest package version.")
        print("   Real tools (e.g., Rider, dotnet CLI) may show different")
        print("   results due to version constraints, target frameworks,")
        print("   or package downgrades. But the core dependency set is accurate.")


def export_d2_to_image(d2_code: str, output_name: str):
    try:
        svg_file = output_name + ".svg"
        d2_file = output_name + ".d2"

        with open(d2_file, "w", encoding="utf-8") as f:
            f.write(d2_code)

        result = subprocess.run(
            ["d2", d2_file, svg_file],
            capture_output=True,
            text=True,
            timeout=15
        )

        os.remove(d2_file)

        if result.returncode == 0:
            print(f"Diagram saved to: {svg_file}")
        else:
            print(f"d2 error: {result.stderr}")

    except FileNotFoundError:
        print("d2 CLI not found. Install from https://github.com/terrastruct/d2/releases")
    except subprocess.TimeoutExpired:
        print("d2 timed out. Graph may be very large.")
    except Exception as e:
        print(f"Export failed: {e}")
if __name__ == "__main__":
    main()