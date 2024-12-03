import subprocess
import json
from package.package_action import get_package_list
from manifest.local_manifest import get_manifest, create_manifest, lookup_in_manifest
from concurrent.futures import ProcessPoolExecutor
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

excluded_packages = []
problematic_scans = []


def read_config():
    with open("config.json") as config_file:
        return json.load(config_file)


def scan_packages(package_name):
    scan_id = (
        "openstack"
        if (".el8ost" not in package_name and ".el9ost" not in package_name)
        else "openstack-podified"
    )
    scan_command = [
        "osh-cli",
        "mock-build",
        "--priority=0",
        "--nowait",
        "--comment={}".format(scan_id),
        "--config=auto",
        "--nvr={}".format(package_name),
    ]
    try:
        result = subprocess.run(
            scan_command, capture_output=True, text=True, check=True
        )
        return None, result.stdout
    except subprocess.CalledProcessError as e:
        return package_name, e.output


def main():
    config_data = read_config()
    create_manifest(config_data["related_comments"])
    all_tags = config_data["brew_tags"]
    manifest_tasklists = get_manifest()
    manifest_lookup_cache = {}

    for brew_tags in all_tags:
        for version in brew_tags:
            package_names = get_package_list(version)
            with ProcessPoolExecutor(max_workers=300) as executor:
                futures = []
                for package_name in package_names:
                    if manifest_lookup_cache.get(package_name) is None:
                        manifest_lookup_cache[package_name] = lookup_in_manifest(
                            package_name, manifest_tasklists
                        )
                    if not manifest_lookup_cache[package_name]:
                        futures.append(executor.submit(scan_packages, package_name))
                        excluded_packages.append(package_name)
                for future in futures:
                    package_name, output = future.result()
                    if package_name:
                        problematic_scans.append(package_name)
                        logging.error(f"Problem scanning {package_name}: {output}")

    if excluded_packages:
        logging.info("Excluded packages already scanned:")
        for package_name in excluded_packages:
            logging.info(package_name)

    if problematic_scans:
        logging.warning("Problematic packages:")
        for package_name in problematic_scans:
            logging.warning(package_name)


if __name__ == "__main__":
    main()
