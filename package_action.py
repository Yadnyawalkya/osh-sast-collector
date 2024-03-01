import subprocess

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
