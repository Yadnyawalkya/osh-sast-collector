import subprocess
import os
import json
import hashlib
from local_manifest import get_manifest, create_manifest, lookup_in_manifest
from package_action import get_package_list
from concurrent.futures import ThreadPoolExecutor
import shutil
from datetime import datetime
import logging

excluded_packages = []

def read_config():
    with open('config.json') as config_file:
        return json.load(config_file)
    
def scan_packages(version_dir, file_name):
    os.chdir(version_dir)
    if ".el8ost" in file_name:
        mock_config = "rhos-rhel-8-x86_64"
    else:
        mock_config = "rhos-rhel-9-x86_64"
    #TODO: If package name does not got rpm extension, assuming it is podified container
    scan_id = "openstack"
    if (".el8ost" or ".el9ost") not in file_name:
        scan_id = "openstack-podified"
    scan_command = [
    'osh-cli', 'mock-build', '--priority=0', '--nowait',
    '--comment={}'.format(scan_id), 
    "--config={}".format(mock_config),
    "./{}".format(file_name)
    ]
    scanned_output = subprocess.run(scan_command)
    print(scanned_output)

def download_packages(version_dir, manifest_tasklists, package_name):
    exclude_text = "No src packages available for "
    os.chdir(version_dir)
    if lookup_in_manifest(package_name, manifest_tasklists):
        continue
    else:
        os.chdir(version_dir)
        download_command = ['brew', 'download-build', '--noprogress', '--arch=src', package_name]
        output = subprocess.run(download_command, capture_output=True, text=True).stdout
        if exclude_text in output: # gathering list of packages which are not downloaded
            excluded_packages.append(output.split(exclude_text)[1])

def main():
    # dir structure
    # temp -> version_dir
    config_data = read_config()
    root_dir = os.path.join(os.getcwd(), "temp")
    runner_log_dir = os.path.join(os.getcwd(), "runner_log")
    current_datetime = datetime.now().strftime("%Y%m%d:%H%M")
    logging.basicConfig(filename='runner_{}.log'.format(current_datetime), level=logging.INFO)
    os.makedirs(root_dir, exist_ok=True)
    os.makedirs(runner_log_dir, exist_ok=True)
    os.chdir(root_dir)
    create_manifest(config_data['related_comments'])
    #TODO: take argument later which decides wheather to scan 17.1 or 18 or both
    all_tags = config_data['brew_tags']
    manifest_tasklists = get_manifest()

    for brew_tags in all_tags:
        for version in brew_tags:
            version_dir = os.path.join(root_dir, version)
            os.makedirs(version_dir, exist_ok=True)
            #TODO: Add dynamic way to handling comment aka scan_id
            # scan_id = "{}-{}".format(version, hashlib.sha256(os.urandom(32)).hexdigest()[:6])
            package_names = get_package_list(version)

            with ThreadPoolExecutor(max_workers=200) as executor:
                futures = []
                for package_name in package_names:
                    futures.append(executor.submit(download_packages, version_dir, manifest_tasklists, file_name))           
                for future in futures:
                    future.result()

            with ThreadPoolExecutor(max_workers=200) as executor:
                futures = []
                for file_name in os.listdir():
                    futures.append(executor.submit(scan_packages(version_dir, file_name)))
                for future in futures:
                    future.result()
            os.chdir(root_dir)

    if excluded_packages: # printing if there is list has excluded packages
        print("=> Following packages were not able to get downloaded:\n")
        for package_name in excluded_packages:
            print(package_name)
    shutil.rmtree(root_dir)

if __name__ == "__main__":
    main()