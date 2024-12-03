import os
import subprocess
from package.package_action import find_package

MANIFEST_FILENAME = "manifest.txt"
TASK_LIST = []


def get_manifest():
    manifest_tasklists = []
    with open(MANIFEST_FILENAME, "a+") as file:
        file.seek(0)  # Set the file pointer to the beginning
        for line in file:
            manifest_tasklists.append(int(line.strip()))
    return manifest_tasklists


def create_manifest(related_comments):
    for comment in related_comments:
        scan_command = ["osh-cli", "find-tasks", "--states=CLOSED", "-c", comment]
        output = subprocess.run(scan_command, capture_output=True, text=True).stdout
        numbers = [int(x) for x in output.split("\n") if x.strip()]
        with open(MANIFEST_FILENAME, "a+") as manifest_file:
            for number in numbers:
                manifest_file.write(str(number) + "\n")
    print(
        "=> Manifest file has been created at {}".format(
            os.path.abspath(MANIFEST_FILENAME)
        )
    )
    return os.path.abspath(MANIFEST_FILENAME)


def lookup_in_manifest(package_name, manifest_tasklists):
    taskid = find_package(package_name)
    if (taskid is not None) and taskid in manifest_tasklists:
        print("=> {}: Scan is already done! ".format(taskid))
        TASK_LIST.append(taskid)
        return True
    else:
        return False
