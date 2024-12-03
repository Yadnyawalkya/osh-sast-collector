import subprocess


def find_package(package_name, latest=False):
    scan_command = [
        "osh-cli",
        "find-tasks",
        "--states=CLOSED",
        "--latest",
        "-r",
        "{}".format(package_name),
    ]
    output = subprocess.run(scan_command, capture_output=True, text=True)
    output_lines = output.stdout.splitlines()
    if output_lines:
        taskid = int(output_lines[0])
        return taskid
    else:
        return None


def get_package_list(version):
    list_command = ["brew", "latest-pkg", "--all", version]
    command_output = subprocess.run(list_command, capture_output=True, text=True)
    output_lines = command_output.stdout.strip().split("\n")[2:]
    package_names = [line.split()[0] for line in output_lines]
    return package_names


# due to bug
def find_in_failed_list(package_name, latest=False):
    scan_command = [
        "osh-cli",
        "find-tasks",
        "--states=FAILED",
        "--latest",
        "-r",
        "{}".format(package_name),
    ]
    output = subprocess.run(scan_command, capture_output=True, text=True)
    output_lines = output.stdout.splitlines()
    if output_lines:
        taskid = int(output_lines[0])
        return taskid
    else:
        return None
