# todo

config_data = read_config()
scan_id = config_data['scan_id']
core_packages = config_data['scan_id']

if scan_id:
    #print that generating report from comment value = <scan_id>
    #execute this command: osh-cli find-tasks --comment --states=CLOSED <scan_id> 
    # store above command output into some variable
else:
    #there is no value set to scan_id of config.json which means report can not be generated, if you want generate report, please specify valid comment value

<create-temp-folder>
<create-core-folder> and store its absolute path in variables
<create-others-folder> and store its absolute path in variable

run this command to download result:
osh-cli download-results <number> -d <temp-folder>

change directory to <temp-folder>

if downloaded result name contains anything from core_packages:
    then move that result file to core-folder
else:
    then move that file into temp folder


make sure temp folder is  empty and delete it
change directory to core folder
create empty mega-scan-results-imp.err file
untar all the files one by one and append result of scan-results-imp.err into mega-scan-results-imp.err file 

