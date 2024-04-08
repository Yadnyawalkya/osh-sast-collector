# OpenStack SAST Tool

These scripts facilitates mass-scanning of all OpenStack components and centralizes gathering of their results.

## How is it works?
### 1. Scan Initiation and Completion Check
The pipeline verify if all components across active and upcoming product versions of OpenStack have undergone scanning. If scans are not done already, pipeline will initiate them.
### 2. Result Gathering and Categorization
For all OpenStack versions and RHEL variants, scan will happen and results will be collected. Findings will be categorized into two groups:

**Core results**: The pipeline maintains a list of core Red Hat OpenStack services. Components containing names matching these services will be classified as core results.

**Dependency results**: These are findings from dependency components. This results will be further divided into:
  * **Top 25 CWE**: Findings aligned with [most critical Common Weakness Enumerations (CWE) list](https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html) will be prioritized.
  * **Other Findings**: Remaining weakness will be categorized separately.

![image](https://github.com/Yadnyawalkya/openstack-sast/assets/10824880/4dfda442-279d-4326-b39f-2857b5ad852b)
