import json
import os
import subprocess
import tarfile
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from prettytable import PrettyTable

from manifest.local_manifest import create_manifest, get_manifest
from package.package_action import find_package, get_package_list, find_in_failed_list

current_datetime = datetime.now().strftime("%Y%m%d:%H%M")
root_dir = os.path.join(os.getcwd(), "all_reports")
latest_dir = os.path.join(root_dir, "latest")
parent_dir = os.path.join(root_dir, f"reports-{current_datetime}")
stats_file_name = f"stats-{current_datetime}.txt"
temp_dir = os.path.join(parent_dir, "temp")
total_excluded_components = {}
total_excluded_components2 = {}
total_package_count = {}
os.makedirs(root_dir, exist_ok=True)
os.makedirs(latest_dir, exist_ok=True)
os.makedirs(parent_dir, exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)


def extract_scan_results_err(file_name, tar_file_path, version, config_data):
    core_dir = os.path.join(parent_dir, version, "core_results")
    dep_dir = os.path.join(parent_dir, version, "dep_results")
    os.makedirs(core_dir, exist_ok=True)
    os.makedirs(dep_dir, exist_ok=True)

    with tarfile.open(tar_file_path, "r:xz") as tar:
        for member in tar.getmembers():
            if "scan-results.err" in os.path.basename(member.name):
                with tar.extractfile(member) as extracted_file:
                    contents = extracted_file.read().decode("utf-8")
                    if contents:
                        output_dir = (
                            core_dir
                            if any(
                                any(key in file_name for key in el)
                                for el in config_data["core_packages"]
                            )
                            else dep_dir
                        )
                        tar.extract(member, path=output_dir)
                        if "core" in output_dir:
                            file_id = "core"
                            destination_dir = os.path.join(
                                output_dir,
                                f"{file_id}-{member.name.split('/')[0]}-scan-results.err",
                            )
                        else:
                            file_id = "dep"
                            collective_dir = os.path.join(dep_dir, "collective")
                            os.makedirs(collective_dir, exist_ok=True)
                            destination_dir = os.path.join(
                                output_dir,
                                "collective",
                                f"{file_id}-{member.name.split('/')[0]}-scan-results.err",
                            )
                            contents = (
                                f"RESULT_FILE: {file_name}\n{contents}"  # First part
                            )
                            contents = contents.replace(
                                "\n\nError: ",
                                "\n\nRESULT_FILE: {}\nError: ".format(file_name),
                            )  # Middle part
                            contents += "\n"  # Last part
                            lines = contents.split("\n\nRESULT_FILE: ")
                            output = [
                                line if i == 0 else f"\n\nRESULT_FILE: {line}"
                                for i, line in enumerate(lines)
                            ]
                            output = set(output)  # remove duplicates
                            for entry in output:
                                try:
                                    cwe_number = "CWE-{}".format(
                                        int(re.findall(r"\(CWE-(\d+)\):", entry)[0])
                                    )
                                    if cwe_number in config_data["cwe_priority"]:
                                        output_dir_path = os.path.join(
                                            dep_dir, "dep-top25-cwe-sorted.err"
                                        )
                                    else:
                                        output_dir_path = os.path.join(
                                            dep_dir, "dep-other-important.err"
                                        )
                                except IndexError:
                                    output_dir_path = os.path.join(
                                        dep_dir, "dep-other-important.err"
                                    )
                                with open(output_dir_path, "a+") as output_file:
                                    output_file.write(entry)
                        os.rename(
                            os.path.join(output_dir, member.name), destination_dir
                        )
                        shutil.rmtree(
                            os.path.join(output_dir, member.name.split("/")[0])
                        )


def process_file(file_name, tar_file_path, version, config_data):
    extract_scan_results_err(file_name, tar_file_path, version, config_data)


def prepare_stats(parent_dir, d):
    error_pattern = r"^Error: "
    for version in os.listdir(parent_dir):
        version_data = {}
        for dir_name in ["core_results", "dep_results", "dep_results/collective"]:
            total_errors = 0
            file_count = 0  # initializing file count for each directory
            dir_path = os.path.join(parent_dir, version, dir_name)
            if os.path.isdir(dir_path):
                for root, _, files in os.walk(dir_path):
                    file_count += len(
                        files
                    )  # incrementing file count for each file found
                    dep_count = 0
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            with open(file_path, "r", encoding="utf-8") as f:
                                for line in f:
                                    if re.match(error_pattern, line):
                                        total_errors += 1
                                        dep_count += 1
                        if "dep-top25-cwe-sorted.err" in file:
                            version_data.setdefault(dir_name, {}).update(
                                {"top25_cwe": dep_count}
                            )
                            dep_count = 0
                        elif "dep-other-important.err" in file:
                            version_data.setdefault(dir_name, {}).update(
                                {"other_important": dep_count}
                            )
                            dep_count = 0
            if dir_name in ("core_results", "dep_results/collective"):
                version_data.setdefault(dir_name, {}).update(
                    {"total_files": file_count, "total_errors": total_errors}
                )  # Storing both file count and total errors
        d[version] = version_data


def download_and_append_task_first(package_name, version, manifest_tasklists):
    version_dir = os.path.join(parent_dir, temp_dir, version)
    taskid = find_package(package_name)
    if (taskid is not None) and (taskid in manifest_tasklists):
        print("=> {}: Scan found!".format(taskid))
        download_command = [
            "osh-cli",
            "download-results",
            str(taskid),
            "-d",
            version_dir,
        ]
        process = subprocess.Popen(
            download_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, error = process.communicate()
        if process.returncode == 0:
            print("=> {}: Scan report downloaded!".format(taskid))
            return taskid
        else:
            print(f"Failed to download scan report for task {taskid}")
            # Print the error message, if any
            print("Error:", error.decode())
    else:
        total_excluded_components2[version].append(package_name)
    return None


def download_and_append_task_second(package_name, version, manifest_tasklists):
    version_dir = os.path.join(parent_dir, temp_dir, version)
    taskid = find_in_failed_list(package_name)
    if (taskid is not None) and (taskid in manifest_tasklists):
        print("=> {}: Scan found!".format(taskid))
        download_command = [
            "osh-cli",
            "download-results",
            str(taskid),
            "-d",
            version_dir,
        ]
        process = subprocess.Popen(
            download_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, error = process.communicate()
        if process.returncode == 0:
            print("=> {}: Scan report downloaded!".format(taskid))
            return taskid
        else:
            print(f"Failed to download scan report for task {taskid}")
            # Print the error message, if any
            print("Error:", error.decode())
    else:
        total_excluded_components[version].append(package_name)
    return None


def write_and_print(file, content):
    file.write(content)
    print(content, end="")
    file.write("\n\n")
    print("\n\n")


def generate_tables_and_write_to_file(d, parent_dir, stats_file_name):
    compare_table = PrettyTable()
    compare_table.field_names = [
        "Version Tag",
        "Total component present",
        "Total components scanned",
        "Unscanned",
    ]
    for version_tag in (
        total_excluded_components.keys() & d.keys() & total_package_count.keys()
    ):
        total_files = d[version_tag].get("core_results", {}).get("total_files", 0) + d[
            version_tag
        ].get("dep_results/collective", {}).get("total_files", 0)
        compare_table.add_row(
            [
                version_tag,
                total_package_count[version_tag],
                total_files,
                len(total_excluded_components[version_tag]),
            ]
        )

    table = PrettyTable()
    table.field_names = [
        "Product Version",
        "Core Components",
        "Dep Components",
        "Core Results",
        "Dep Results",
        "Dep Top-25 CWE Results",
        "Other Dep Results",
    ]

    for version, data in d.items():
        core_files = data.get("core_results", {}).get("total_files", 0)
        dep_files = data.get("dep_results/collective", {}).get("total_files", 0)
        core_errors = data.get("core_results", {}).get("total_errors", 0)
        dep_errors = data.get("dep_results/collective", {}).get("total_errors", 0)
        top25_cwe = data.get("dep_results", {}).get("top25_cwe", 0)
        other_important = data.get("dep_results", {}).get("other_important", 0)
        table.add_row(
            [
                version,
                core_files,
                dep_files,
                core_errors,
                dep_errors,
                top25_cwe,
                other_important,
            ]
        )

    total_core_files = sum(
        data.get("core_results", {}).get("total_files", 0) for data in d.values()
    )
    total_dep_files = sum(
        data.get("dep_results/collective", {}).get("total_files", 0)
        for data in d.values()
    )
    total_core_errors = sum(
        data.get("core_results", {}).get("total_errors", 0) for data in d.values()
    )
    total_dep_errors = sum(
        data.get("dep_results/collective", {}).get("total_errors", 0)
        for data in d.values()
    )
    total_top25_cwe = sum(
        data.get("dep_results", {}).get("top25_cwe", 0) for data in d.values()
    )
    total_other_important = sum(
        data.get("dep_results", {}).get("other_important", 0) for data in d.values()
    )
    table.add_row(
        [
            "\033[1mTotal\033[0m",
            total_core_files,
            total_dep_files,
            total_core_errors,
            total_dep_errors,
            total_top25_cwe,
            total_other_important,
        ]
    ) # noqa

    total_table = PrettyTable()
    total_table.field_names = ["Product Version", "Total Components", "Total Results"]

    for version, data in d.items():
        total_files = data.get("core_results", {}).get("total_files", 0) + data.get(
            "dep_results/collective", {}
        ).get("total_files", 0)
        total_errors = data.get("core_results", {}).get("total_errors", 0) + data.get(
            "dep_results/collective", {}
        ).get("total_errors", 0)
        total_table.add_row([version, total_files, total_errors])
    total_table.add_row(
        [
            "\033[1mTotal\033[0m",
            total_core_files + total_dep_files,
            total_core_errors + total_dep_errors,
        ]
    )

    with open(os.path.join(parent_dir, stats_file_name), "w") as file:
        write_and_print(file, "Detailed Stats:\n")
        write_and_print(file, str(table))
        write_and_print(file, "Total Components & Results:\n")
        write_and_print(file, str(total_table))
        write_and_print(file, "Meta Stats: Component Scanned & Not Scanned:\n")
        write_and_print(file, str(compare_table))
        write_and_print(file, "Following list of packages are not been scanned:")
        for key, values in total_excluded_components.items():
            exclude_text = f"* Tags: {key} => {values}"
            write_and_print(file, exclude_text)


def iterate_and_generate(config_data, parent_dir, temp_dir):
    manifest_tasklists = get_manifest()
    d = {}

    for brew_tags in config_data["brew_tags"]:
        for version in brew_tags:
            total_excluded_components[version] = []
            total_excluded_components2[version] = []
            version_dir = os.path.join(parent_dir, temp_dir, version)
            os.makedirs(version_dir, exist_ok=True)
            package_names = get_package_list(version)
            total_package_count[version] = len(package_names)

            with ThreadPoolExecutor(max_workers=200) as executor:
                futures = []
                for package_name in package_names:
                    futures.append(
                        executor.submit(
                            download_and_append_task_first,
                            package_name,
                            version,
                            manifest_tasklists,
                        )
                    )
                for future in futures:
                    future.result()

            with ThreadPoolExecutor(max_workers=200) as executor:
                futures = []
                for package_name in total_excluded_components[version]:
                    futures.append(
                        executor.submit(
                            download_and_append_task_second,
                            package_name,
                            version,
                            manifest_tasklists,
                        )
                    )
                for future in futures:
                    future.result()

            with ThreadPoolExecutor(max_workers=400) as executor:
                futures = []
                for file_name in os.listdir(version_dir):
                    if file_name.endswith(".tar.xz"):
                        file_path = os.path.join(version_dir, file_name)
                        futures.append(
                            executor.submit(
                                process_file, file_name, file_path, version, config_data
                            )
                        )
                for future in as_completed(futures):
                    pass

    shutil.rmtree(temp_dir)

    prepare_stats(parent_dir, d)
    generate_tables_and_write_to_file(d, parent_dir, stats_file_name)


config_data = {}
with open("../config.json") as config_file:
    config_data = json.load(config_file)

manifest_path = create_manifest(config_data.get("related_comments", []))
iterate_and_generate(config_data, parent_dir, temp_dir)
shutil.rmtree(latest_dir)
shutil.copytree(parent_dir, latest_dir)
os.remove(manifest_path)
