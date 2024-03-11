import subprocess
import os
import json
import hashlib
from local_manifest import get_manifest, create_manifest, lookup_in_manifest
from package_action import get_package_list


def read_config():
    with open('config.json') as config_file:
        return json.load(config_file)

def download_and_scan_packages(version_dir, package_names):
    excluded_packages = []
    exclude_text = "No src packages available for "
    os.chdir(version_dir)
    get_manifest()
    for package_name in package_names:
        if lookup_in_manifest(package_name):
            continue
        else:
            download_command = ['brew', 'download-build', '--noprogress', '--arch=src', package_name]
            output = subprocess.run(download_command, capture_output=True, text=True).stdout
            if exclude_text in output: # gathering list of packages which are not downloaded
                excluded_packages.append(output.split(exclude_text)[1])
            for file_name in os.listdir():
                #TODO: Add failover mechanism if OSH auth is not provided: only give not scanned package names
                #TODO: Remove hardcoding of mock-config later
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

    if excluded_packages: # printing if there is list has excluded packages
        print("=> Following packages were not able to get downloaded:\n")
        for package_name in excluded_packages:
            print(package_name)

    
# def generate_report():
#     os.makedirs("reports", exist_ok=True)
#     print(TASK_LIST)
#     for taskid in TASK_LIST:
#         download_command = ["osh-cli", "download-results", {taskid}, "-d", "reports"]
#         subprocess.run(download_command, capture_output=True, text=True).stdout

def main():
    config_data = read_config()
    create_manifest(config_data['related_comments'])
    original_dir = os.getcwd()
    #TODO: take argument later which decides wheather to scan 17.1 or 18 or both
    brew_tags = config_data['brew_tags']["osp17.1"]

    for version in brew_tags:
        version_dir = os.path.join(original_dir, version)
        os.makedirs(version_dir, exist_ok=True)
        #TODO: Add dynamic way to handling comment aka scan_id
        # scan_id = "{}-{}".format(version, hashlib.sha256(os.urandom(32)).hexdigest()[:6])
        package_names = get_package_list(version)
        download_and_scan_packages(version_dir, package_names)
        os.chdir(original_dir)

if __name__ == "__main__":
    main()
