import subprocess
import os
import json

with open('config.json') as config_file:
    config_data = json.load(config_file)
    versions = config_data['versions']

for version in versions:
    version_dir = os.path.join(os.getcwd(), version)
    os.makedirs(version_dir, exist_ok=True)

    list_command = ['brew', 'latest-pkg', '--all', version]
    command_output = subprocess.run(list_command, capture_output=True, text=True)

    package_names = command_output.stdout.split('\n')[2:]  # Skip the first two lines

    for package_name in package_names:
        download_command = ['brew', 'download-build', '--noprogress', '--arch=src', '-d', version_dir, package_name]
        subprocess.run(download_command)
