import os
import subprocess

FILENAME = "manifest.txt"

def get_manifest():
    manifest_tasklists = []
    with open(FILENAME, 'a+') as file:
        file.seek(0)  # Set the file pointer to the beginning
        for line in file:
            manifest_tasklists.append(int(line.strip()))
    return manifest_tasklists

def create_manifest(extensions):
    for ext in extensions:
        scan_command = ['osh-cli', 'find-tasks', '--states=CLOSED','-r', ext]
        output = subprocess.run(scan_command, capture_output=True, text=True).stdout
        numbers = [int(x) for x in output.split("\n") if x.strip()]
        with open(FILENAME, 'a') as manifest_file:
            for number in numbers:
                manifest_file.write(str(number) + '\n')
    print("=> Manifest file has been created at {}".format(os.path.abspath(FILENAME)))
