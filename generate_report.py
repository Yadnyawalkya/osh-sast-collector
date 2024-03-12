import json
import os
import subprocess
import tarfile
import re

from local_manifest import create_manifest, get_manifest
from package_action import find_package, get_package_list

TASK_LIST = []
# dir structure
# reports -> version_dir
parent_dir = os.path.join(os.getcwd(), "reports")
if not os.path.exists(parent_dir):
    os.makedirs(parent_dir)

with open('config.json') as config_file:
    config_data = json.load(config_file)

os.chdir(parent_dir)
create_manifest(config_data['related_comments'])
manifest_tasklists = get_manifest()
brew_tags = config_data['brew_tags']["osp17.1"]
all_entries = []

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
                        output_dir = core_dir if any(any(key in file_name for key in el) for el in config_data['core_packages']) else dep_dir
                        if "core" in output_dir:
                            file_id = "core"
                            output_dir_path = os.path.join(output_dir, '{}-scan-results.err'.format(file_id))
                        else:
                            file_id = "dep"
                            output_dir_path = os.path.join(output_dir, '{}-scan-results.err'.format(file_id))
                            lines = contents.split('\n\nRESULT_FILE: ')
                            output = [line if i == 0 else f"\n\nRESULT_FILE: {line}" for i, line in enumerate(lines)]
                            # entries = [entry.strip() for entry in entries if entry.strip()]
                            all_entries.extend(output)
                            dep_cwe_logs(output_dir)
                        with open(output_dir_path, 'w') as output_file:
                            output_file.write(contents)

def dep_cwe_logs(output_dir):
    # inside root reports dir -- core vs dep structure
    # with in dep dir strcture -- top25 cwe structure
    # also for remaining dependancy results will be in other-important.err
    # CWE list -- https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html
    print(all_entries)
    for entry in all_entries:
        cwe_number = "CWE-{}".format(int(re.findall(r"\(CWE-(\d+)\):", entry)[0]))
        if cwe_number in config_data['cwe_priority']:
            print(cwe_number)
            output_dir_path = os.path.join(output_dir, 'top25-cwe-sorted.err')
            with open(output_dir_path, 'w') as output_file:
                output_file.write(entry)
        else:
            output_dir_path = os.path.join(output_dir, 'other-important.err')
            with open(output_dir_path, 'w') as output_file:
                output_file.write(entry)

def iterate_and_generate():
    # Iterate over brew tags
    for version in brew_tags:
        version_dir = os.path.join(parent_dir, version)
        os.makedirs(version_dir, exist_ok=True)
        package_names = get_package_list(version)
        for package_name in package_names:
            taskid = find_package(package_name)
            if taskid is not None and taskid in manifest_tasklists:
                print("=> {}: Scan found!".format(taskid))
                download_command = ["osh-cli", "download-results", str(taskid), "-d", version_dir]
                output = subprocess.run(download_command)
                print("=> {}: Scan downloaded!".format(taskid))
                TASK_LIST.append(taskid)

    # Process files in subdirectories
    sub_dirs = brew_tags
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

iterate_and_generate()