import sys
import os
import main
from unittest.mock import patch
import pytest
import subprocess

# Adjusting the path to find 'main.py' in the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def mock_config_data():
    # Mocking the data that would be loaded from config.json
    return {
        "related_comments": "Test Comment",
        "brew_tags": [["v1", "v2"], ["v3"]],
    }


@patch("main.subprocess.run")
def test_scan_packages(mock_subprocess, mock_config_data):
    # Setting up a mock return value for the subprocess run call
    mock_subprocess.return_value.stdout = "Scan successful"
    mock_subprocess.return_value.returncode = 0

    package_name = "test-package"
    result_package, result_output = main.scan_packages(package_name)

    # Verifying the function returns correct values
    assert result_package is None
    assert result_output == "Scan successful"


@patch("main.subprocess.run")
def test_scan_packages_failure(mock_subprocess, mock_config_data):
    # Simulating a subprocess error (failure)
    mock_subprocess.side_effect = subprocess.CalledProcessError(
        1, "osh-cli", "Error during scan"
    )

    package_name = "test-package"
    result_package, result_output = main.scan_packages(package_name)

    # Verifying the function handles the failure correctly
    assert result_package == "test-package"
    assert "Error during scan" in result_output


@patch("main.get_package_list")
@patch("main.get_manifest")
@patch("main.lookup_in_manifest")
@patch("main.create_manifest")
def test_main(
    mock_create_manifest,
    mock_lookup_in_manifest,
    mock_get_manifest,
    mock_get_package_list,
    mock_config_data,
):
    # Mocking all the necessary function calls in the 'main' function
    mock_get_manifest.return_value = "mocked_manifest"
    mock_get_package_list.return_va
