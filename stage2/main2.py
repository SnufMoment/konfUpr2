import argparse
import sys
import json
import urllib.request
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

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


def fetch_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        raise RuntimeError(f"Failed to fetch JSON from {url}: {e}")


def fetch_xml(url: str) -> ET.Element:
    try:
        with urllib.request.urlopen(url) as response:
            return ET.fromstring(response.read().decode('utf-8'))
    except Exception as e:
        raise RuntimeError(f"Failed to fetch or parse XML from {url}: {e}")


def get_nuget_base_url() -> str:

    index = fetch_json(NUGET_SERVICE_INDEX)
    for resource in index.get("resources", []):
        if resource.get("@type") == PACKAGE_CONTENT_TYPE:
            return resource["@id"]
    raise RuntimeError("NuGet PackageBaseAddress not found in service index.")


def get_latest_version(base_url: str, package_id: str) -> str:

    package_id_lower = package_id.lower()
    versions_url = f"{base_url.rstrip('/')}/{package_id_lower}/index.json"
    data = fetch_json(versions_url)
    versions = data.get("versions", [])
    if not versions:
        raise RuntimeError(f"No versions found for package '{package_id}'")
    return max(versions)


def extract_dependencies(nuspec_root: ET.Element, package_id: str) -> list:

    ns = {'ns': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}
    metadata = nuspec_root.find('ns:metadata', ns)
    if metadata is None:
        return []

    deps_groups = metadata.find('ns:dependencies', ns)
    if deps_groups is None:
        return []

    seen = set()
    dependencies = []

    def add_dep(dep_id: str, dep_version: str):
        key = (dep_id, dep_version)
        if key not in seen:
            seen.add(key)
            dependencies.append({'id': dep_id, 'version': dep_version})

    for group in deps_groups.findall('ns:group', ns):
        for dep in group.findall('ns:dependency', ns):
            dep_id = dep.get('id')
            dep_version = dep.get('version', '*')
            if dep_id:
                add_dep(dep_id, dep_version)

    for dep in deps_groups.findall('ns:dependency', ns):
        dep_id = dep.get('id')
        dep_version = dep.get('version', '*')
        if dep_id:
            add_dep(dep_id, dep_version)

    return dependencies

def get_direct_dependencies(package_id: str) -> list:
    base_url = get_nuget_base_url()
    version = get_latest_version(base_url, package_id)
    package_id_lower = package_id.lower()
    nuspec_url = f"{base_url.rstrip('/')}/{package_id_lower}/{version}/{package_id_lower}.nuspec"

    root = fetch_xml(nuspec_url)
    deps = extract_dependencies(root, package_id)
    return deps


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Visualize NuGet package dependency graph (Stage 2: Data collection)."
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Name of the NuGet package to analyze (e.g., Newtonsoft.Json)."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository URL (for NuGet, typically ignored; must be a valid URL)."
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["online", "offline", "test"],
        help="Operation mode. Only 'online' is supported in Stage 2."
    )
    parser.add_argument(
        "--max-depth",
        required=True,
        help="Maximum depth (used in future stages)."
    )
    parser.add_argument(
        "--filter",
        default="",
        help="Substring to filter dependencies (applied in future stages)."
    )

    args = parser.parse_args()


    if args.mode != "online":
        print("Warning: Stage 2 only supports --mode online. Proceeding anyway.", file=sys.stderr)

    try:
        package = validate_package_name(args.package)
        max_depth = validate_max_depth(args.max_depth)

        if not args.repo.startswith(('http://', 'https://')):
            raise ValueError("--repo must be a URL (e.g., https://api.nuget.org/v3/index.json)")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    return {
        "package": package,
        "repo": args.repo,
        "mode": args.mode,
        "max_depth": max_depth,
        "filter": args.filter
    }


def main():
    config = parse_arguments()


    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()


    try:
        print(f"Fetching direct dependencies for package: {config['package']}")
        dependencies = get_direct_dependencies(config['package'])

        if not dependencies:
            print("No direct dependencies found.")
        else:
            print("Direct dependencies:")
            for dep in dependencies:
                print(f"  - {dep['id']} ({dep['version']})")
    except Exception as e:
        print(f"Error during dependency fetching: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()