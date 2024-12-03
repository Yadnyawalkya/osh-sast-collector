# Collector Module for OpenScanHub  

This module utilizes **OSC-cli utility**, a CLI for OpenScanHub, to streamline security scanning process and reporting.  

### Key Features
- Identifies related builds from build systems like **Brew** or **Koji**.  
- Verifies if security scans exist in **OpenScanHub** for the identified builds.  
- Automatically initiates scans for builds without existing security scans.  
- Generates a zip report upon scan completion  

### Report Highlights
- Analyzes vulnerabilities based on **OWASP Top 10** and **KEV Top 25**.  
- Compares findings between **core** and **non-core packages**.

### Installation
```
python -m venv myenv
source myenv/bin/activate
pip install .
```

