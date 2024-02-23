import subprocess
import os
import json
import hashlib
from local_manifest import get_manifest, create_manifest

def lookup_in_manifest(package_name, manifest_tasklists):
    lookup_result = find_packages(package_name)
    for i in lookup_result:
        if i in manifest_tasklists:
            print("=> {}: Scan is already done! ".format(i))
            return True
        else:
            return False

def read_config():
    with open('config.json') as config_file:
        return json.load(config_file)

def download_and_scan_packages(version_dir, package_names, manifest_tasklists):
    excluded_packages = []
    exclude_text = "No src packages available for "
    os.chdir(version_dir)
    for package_name in package_names:
        if lookup_in_manifest(package_name, manifest_tasklists):
            continue
        else:
            download_command = ['brew', 'download-build', '--noprogress', '--arch=src',package_name]
            output = subprocess.run(download_command, capture_output=True, text=True).stdout
            if exclude_text in output: # gathering list of packages which are not downloaded
                excluded_packages.append(output.split(exclude_text)[1])
            # scan_command = [
            # 'osh-cli', 'mock-build', '--priority=0',
            # '--comment={}'.format(scan_id),
            # "./{}".format(package_name)
            # ]
            # subprocess.run(scan_command)

    if excluded_packages: # printing if there is list has excluded packages
        print("=> Following packages were not able to get downloaded:\n")
        for package_name in excluded_packages:
            print(package_name)

def find_packages(package_name, latest=False):
    scan_command = ['osh-cli', 'find-tasks', "--states=CLOSED", "--latest", "{}".format(package_name)]
    output = subprocess.run(scan_command, capture_output=True, text=True)
    output_lines = output.stdout.splitlines()
    task_ids = [int(line.split()[0]) for line in output_lines] if output_lines else []

    if latest:
        sorted_task_ids = sorted(task_ids)
        max_task_id = sorted_task_ids[-1] if sorted_task_ids else None
        return max_task_id # when latest=True returns single maximum/latest taskid
    else:
        return task_ids # return 1 or more tasks ids

def main():
    config_data = read_config()
    scan_id = hashlib.sha256(os.urandom(32)).hexdigest()[:6]
    create_manifest(config_data['rpm_extensions'])
    manifest_tasklists = get_manifest()
    original_dir = os.getcwd()
    brew_tags = config_data['brew_tags']

    for version in brew_tags:
        version_dir = os.path.join(original_dir, version)
        os.makedirs(version_dir, exist_ok=True)

        list_command = ['brew', 'latest-pkg', '--all', version]
        command_output = subprocess.run(list_command, capture_output=True, text=True)
        output_lines = command_output.stdout.strip().split('\n')[2:]
        package_names = [line.split()[0] for line in output_lines]
        download_and_scan_packages(version_dir, package_names, manifest_tasklists)
        os.chdir(original_dir)
    config_data["scan_id"] = scan_id

if __name__ == "__main__":
    main()
