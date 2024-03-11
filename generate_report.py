from package_action import get_package_list, find_package
from local_manifest import create_manifest, get_manifest, lookup_in_manifest
import json
import os
import subprocess

TASK_LIST = []

with open('config.json') as config_file:
    config_data = json.load(config_file)
brew_tags = config_data['brew_tags']["osp17.1"]
original_dir = os.getcwd()
parent_dir = "reports"
if not os.path.exists(parent_dir):
    os.makedirs(parent_dir)
create_manifest(config_data['related_comments'])
manifest_tasklists = get_manifest()

for version in brew_tags:
    version_dir = os.path.join(parent_dir, version)
    os.makedirs(version_dir)
    package_names = get_package_list(version)[0:5]
    for package_name in package_names:
        taskid = find_package(package_name)
        print(taskid)
        if ((taskid is not None) and taskid in manifest_tasklists):
            print("=> {}: scan found! ".format(taskid))
            download_command = ["osh-cli", f"download-results {taskid}", f"-d {version_dir}"]
            output = subprocess.run(download_command, check=True)
            print(output)
            print("=> {}: scan downloded! ".format(taskid))
            TASK_LIST.append(taskid)

import ipdb;ipdb.set_trace()
    
    



# # todo

# config_data = read_config()
# scan_id = config_data['scan_id']
# core_packages = config_data['scan_id']

# if scan_id:
#     #print that generating report from comment value = <scan_id>
#     #execute this command: osh-cli find-tasks --comment --states=CLOSED <scan_id> 
#     # store above command output into some variable
# else:
#     #there is no value set to scan_id of config.json which means report can not be generated, if you want generate report, please specify valid comment value

# <create-temp-folder>
# <create-core-folder> and store its absolute path in variables
# <create-others-folder> and store its absolute path in variable

# run this command to download result:
# osh-cli download-results <number> -d <temp-folder>

# change directory to <temp-folder>

# if downloaded result name contains anything from core_packages:
#     then move that result file to core-folder
# else:
#     then move that file into temp folder


# make sure temp folder is  empty and delete it
# change directory to core folder
# create empty mega-scan-results-imp.err file
# untar all the files one by one and append result of scan-results-imp.err into mega-scan-results-imp.err file 

