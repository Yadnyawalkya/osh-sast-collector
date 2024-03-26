import json
import os
import subprocess
import tarfile
import re
import threading
from datetime import date

from local_manifest import create_manifest, get_manifest
from package_action import find_package, get_package_list

current_date = date.today()
TASK_LIST = []
all_entries = []
# dir structure
# reports -> version_dir
with open('config.json') as config_file:
    config_data = json.load(config_file)

parent_dir = os.path.join(os.getcwd(), f"reports-{current_date}")
if not os.path.exists(parent_dir):
    os.makedirs(parent_dir)
temp_dir = os.path.join(parent_dir, "temp")
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir, exist_ok=True)
create_manifest(config_data['related_comments'])
manifest_tasklists = get_manifest()
os.chdir(parent_dir)


def extract_scan_results_err(file_name, tar_file_path, version):
    version_dir = os.path.join(parent_dir, temp_dir, version)
    if not os.path.exists(version_dir):
        os.makedirs(version_dir, exist_ok=True)
    core_dir = os.path.join(parent_dir, f'{version}', 'core_results')
    dep_dir = os.path.join(parent_dir,  f'{version}', 'dep_results')
    os.makedirs(core_dir, exist_ok=True)
    os.makedirs(dep_dir, exist_ok=True)

    with tarfile.open(tar_file_path, 'r:xz') as tar:
        for member in tar.getmembers():
            if 'scan-results.err' in os.path.basename(member.name):
                with tar.extractfile(member) as extracted_file:
                    contents = extracted_file.read().decode('utf-8')
                    if contents:
                        output_dir = core_dir if any(any(key in file_name for key in el) for el in config_data['core_packages']) else dep_dir
                        tar.extract(member, path=output_dir)
                        if "core" in output_dir:
                            file_id = "core"
                            destination_dir = os.path.join(output_dir, f"{file_id}-{member.name.split('/')[0]}-scan-results.err")
                        else:
                            file_id = "dep"
                            collective_dir = os.path.join(dep_dir, 'collective')
                            os.makedirs(collective_dir, exist_ok=True)
                            destination_dir = os.path.join(output_dir, 'collective', f"{file_id}-{member.name.split('/')[0]}-scan-results.err")
                            dep_cwe_logs(file_name, contents, dep_dir)
                        os.rename(os.path.join(output_dir, member.name), destination_dir)
                        os.rmdir(os.path.join(output_dir, member.name.split("/")[0]))

def dep_cwe_logs(file_name, contents, dep_dir):
    # inside root reports dir -- core vs dep structure
    # with in dep dir strcture -- top25 cwe structure
    # also for remaining dependancy results will be in other-important.err
    # CWE list -- https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html
    contents = f'RESULT_FILE: {file_name}\n{contents}'  # First part
    contents = contents.replace('\n\nError: ', '\n\nRESULT_FILE: {}\nError: '.format(file_name))  # Middle part
    contents += '\n'  # Last part
    lines = contents.split('\n\nRESULT_FILE: ')
    output = [line if i == 0 else f"\n\nRESULT_FILE: {line}" for i, line in enumerate(lines)]
    all_entries.extend(output)

    for entry in all_entries:
        try:
            cwe_number = "CWE-{}".format(int(re.findall(r"\(CWE-(\d+)\):", entry)[0]))
            if cwe_number in config_data['cwe_priority']:
                output_dir_path = os.path.join(dep_dir, 'top25-cwe-sorted.err')
                with open(output_dir_path, 'a+') as output_file:
                    output_file.write(entry)
            else:
                output_dir_path = os.path.join(dep_dir, 'other-important.err')
                with open(output_dir_path, 'a+') as output_file:
                    output_file.write(entry)
        except IndexError:
            pass

def process_file(file_name, tar_file_path, version):
    extract_scan_results_err(file_name, tar_file_path, version)

def iterate_and_generate():
    for brew_tags in config_data['brew_tags']:
        for version in brew_tags:
            version_dir = os.path.join(parent_dir, temp_dir, version)
            if not os.path.exists(version_dir):
                os.makedirs(version_dir, exist_ok=True)
            package_names = get_package_list(version)
            for package_name in package_names:
                taskid = find_package(package_name)
                if taskid is not None and taskid in manifest_tasklists:
                    print("=> {}: Scan found!".format(taskid))
                    download_command = ["osh-cli", "download-results", str(taskid), "-d", version_dir]
                    output = subprocess.run(download_command)
                    print("=> {}: Scan report downloaded!".format(taskid))
                    TASK_LIST.append(taskid)

            for file_name in os.listdir(version_dir):
                if file_name.endswith(".tar.xz"):
                    file_path = os.path.join(version_dir, file_name)
                    thread = threading.Thread(target=process_file, args=(file_name, file_path, version))
                    thread.start()
    os.rmdir(temp_dir)

iterate_and_generate()