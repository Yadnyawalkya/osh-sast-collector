import os

def get_manifest():
    filename = "manifest.txt"
    manifest_tasklists = []

    with open(filename, 'a+') as file:
        file.seek(0)  # Set the file pointer to the beginning
        for line in file:
            manifest_tasklists.append(int(line.strip()))

    return manifest_tasklists
