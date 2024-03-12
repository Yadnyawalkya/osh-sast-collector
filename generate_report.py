import json
import os
import subprocess
import tarfile

from local_manifest import create_manifest, get_manifest
from package_action import find_package, get_package_list

TASK_LIST = []
parent_dir = "reports"

with open('config.json') as config_file:
    config_data = json.load(config_file)
brew_tags = config_data['brew_tags']["osp17.1"]

if not os.path.exists(parent_dir):
    os.makedirs(parent_dir)

create_manifest(config_data['related_comments'])
manifest_tasklists = get_manifest()

# Iterate over brew tags
for version in brew_tags:
    version_dir = os.path.join(parent_dir, version)
    os.makedirs(version_dir, exist_ok=True)
    package_names = get_package_list(version)[:5]  # Limit to first 5 packages
    for package_name in package_names:
        taskid = find_package(package_name)
        if taskid is not None and taskid in manifest_tasklists:
            print("=> {}: Scan found!".format(taskid))
            download_command = ["osh-cli", "download-results", str(taskid), "-d", version_dir]
            output = subprocess.run(download_command)
            print(output)
            print("=> {}: Scan downloaded!".format(taskid))
            TASK_LIST.append(taskid)

# Function to extract scan results and handle errors
def extract_scan_results_err(file_name, tar_file_path, core_dir, dep_dir):
    with tarfile.open(tar_file_path, 'r:xz') as tar:
        for member in tar.getmembers():
            if 'scan-results.err' in os.path.basename(member.name):
                with tar.extractfile(member) as extracted_file:
                    contents = extracted_file.read().decode('utf-8')
                    if contents:
                        contents = f'RESULT_FILE: {file_name}\n{contents}'  # First part
                        contents = contents.replace('\n\nError: ', '\n\nRESULT_FILE: {}\nError: '.format(file_name))  # Middle part
                        contents += '\n'  # Last part
                        output_dir = core_dir if any(package in file_name for package in config_data['core_packages']) else dep_dir
                        with open(os.path.join(output_dir, 'meta-scan-results.err'), 'w') as output_file:
                            output_file.write(contents)

# Process files in subdirectories
sub_dirs = os.listdir(parent_dir)
for subdir in sub_dirs:
    subdir_path = os.path.join(parent_dir, subdir)
    for file_name in os.listdir(subdir_path):
        if file_name.endswith(".tar.xz"):
            file_path = os.path.join(subdir_path, file_name)
            core_dir = os.path.join(parent_dir, 'core_results_{}'.format(subdir))
            dep_dir = os.path.join(parent_dir, 'dep_results_{}'.format(subdir))
            os.makedirs(core_dir, exist_ok=True)
            os.makedirs(dep_dir, exist_ok=True)
            extract_scan_results_err(file_name, file_path, core_dir, dep_dir)
