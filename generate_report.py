import json
import os
import subprocess
import tarfile
import re
import threading
from datetime import date
import shutil
import os
import re
from prettytable import PrettyTable

from local_manifest import create_manifest, get_manifest
from package_action import find_package, get_package_list

current_date = date.today()
TASK_LIST = []
all_entries = []
d = {}

# dir structure
# reports -> version_dir
with open('config.json') as config_file:
    config_data = json.load(config_file)

parent_dir = os.path.join(os.getcwd(), f"reports-{current_date}")
stats_file_name = f"stats-{current_date}.txt"
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
    os.makedirs(version_dir, exist_ok=True)
    
    core_dir = os.path.join(parent_dir, version, 'core_results')
    dep_dir = os.path.join(parent_dir, version, 'dep_results')
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
                            contents = f'RESULT_FILE: {file_name}\n{contents}'  # First part
                            contents = contents.replace('\n\nError: ', '\n\nRESULT_FILE: {}\nError: '.format(file_name))  # Middle part
                            contents += '\n'  # Last part
                            lines = contents.split('\n\nRESULT_FILE: ')
                            output = [line if i == 0 else f"\n\nRESULT_FILE: {line}" for i, line in enumerate(lines)]
                            output = set(output)  # remove duplicates
                            for entry in output:
                                try:
                                    cwe_number = "CWE-{}".format(int(re.findall(r"\(CWE-(\d+)\):", entry)[0]))
                                    if cwe_number in config_data['cwe_priority']:
                                        output_dir_path = os.path.join(dep_dir, 'dep-top25-cwe-sorted.err')
                                    else:
                                        output_dir_path = os.path.join(dep_dir, 'dep-other-important.err')
                                except IndexError:
                                    output_dir_path = os.path.join(dep_dir, 'dep-other-important.err')
                                with open(output_dir_path, 'a+') as output_file:
                                    output_file.write(entry)
                        os.rename(os.path.join(output_dir, member.name), destination_dir)
                        shutil.rmtree(os.path.join(output_dir, member.name.split("/")[0]))

def process_file(file_name, tar_file_path, version):
    extract_scan_results_err(file_name, tar_file_path, version)

def prepare_stats():
    error_pattern = r'^Error: '

    for version in os.listdir(parent_dir):
        version_data = {}
        for dir_name in ["core_results", "dep_results", "dep_results/collective"]:
            total_errors = 0
            file_count = 0  # initializing file count for each directory
            dir_path = os.path.join(parent_dir, version, dir_name)
            if os.path.isdir(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    file_count += len(files)  # incrementing file count for each file found
                    dep_count = 0
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                for line in f:
                                    if re.match(error_pattern, line):
                                        total_errors += 1
                                        dep_count += 1
                                    else:
                                        print(line)
                        if "dep-top25-cwe-sorted.err" in file:
                            version_data.setdefault(dir_name, {}).update({'top25_cwe': dep_count})
                            dep_count = 0
                        elif "dep-other-important.err" in file:
                            version_data.setdefault(dir_name, {}).update({'other_important': dep_count})
                            dep_count = 0
            if dir_name in ("core_results", "dep_results/collective"):
                version_data.setdefault(dir_name, {}).update({'total_files': file_count, 'total_errors': total_errors})  # Storing both file count and total errors
        d[version] = version_data


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
    shutil.rmtree(temp_dir)

    prepare_stats()

    table = PrettyTable()
    table.field_names = ["Product version", "Core Components", "Dep Components", "Core results", "Dep results", "Dep top-25 CWE results", "Other dep results"]

    # populating the table
    for version, data in d.items():
        core_files = data.get("core_results", {}).get("total_files", 0)
        dep_files = data.get("dep_results/collective", {}).get("total_files", 0)
        core_errors = data.get("core_results", {}).get("total_errors", 0)
        dep_errors = data.get("dep_results/collective", {}).get("total_errors", 0)
        top25_cwe = data.get("dep_results", {}).get("top25_cwe", 0)
        other_important = data.get("dep_results", {}).get("other_important", 0)
        table.add_row([version, core_files, dep_files, core_errors, dep_errors, top25_cwe, other_important])

    # adding total count row with header style
    total_core_files = sum(data.get("core_results", {}).get("total_files", 0) for data in d.values())
    total_dep_files = sum(data.get("dep_results/collective", {}).get("total_files", 0) for data in d.values())
    total_core_errors = sum(data.get("core_results", {}).get("total_errors", 0) for data in d.values())
    total_dep_errors = sum(data.get("dep_results/collective", {}).get("total_errors", 0) for data in d.values())
    total_top25_cwe = sum(data.get("dep_results", {}).get("top25_cwe", 0) for data in d.values())
    total_other_important = sum(data.get("dep_results", {}).get("other_important", 0) for data in d.values())
    table.add_row([f"\033[1mTotal\033[0m", total_core_files, total_dep_files, total_core_errors, total_dep_errors, total_top25_cwe, total_other_important])

    with open(os.path.join(parent_dir, stats_file_name), "w") as file:
        file.write(str(table))
        print(table)

    table2 = PrettyTable()
    table2.field_names = ["Product version", "All Components", "All findings"]

    for version, data in d.items():
        core_files = data.get("core_results", {}).get("total_files", 0)
        dep_files = data.get("dep_results/collective", {}).get("total_files", 0)
        core_errors = data.get("core_results", {}).get("total_errors", 0)
        dep_errors = data.get("dep_results/collective", {}).get("total_errors", 0)
        total_files = core_files + dep_files
        total_errors = core_errors + dep_errors
        table.add_row([version, core_files, dep_files, core_errors, dep_errors])

    table.add_row([f"\033[1mTotal\033[0m", total_files, total_errors])

    with open(os.path.join(parent_dir, stats_file_name), "a+") as file:
        file.write("\n\n{}".format(str(table)))
        print(table)
   
iterate_and_generate()
