import sys
import os
import pytest
from unittest.mock import patch
from reports.report_generator import generate_report

# Adjusting the path to find 'main.py' in the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Test case 1: Test valid report generation with mock data
def test_valid_report_generation():
    mock_data = {
        "task_id": "12345",
        "task_name": "Test Task",
        "related_comments": "Test Comment",
    }

    # Assuming generate_report returns a dictionary or similar report object
    result = generate_report(mock_data)

    # Check if the report contains the expected keys
    assert "task_id" in result
    assert "task_name" in result
    assert "related_comments" in result
    assert result["task_id"] == "12345"
    assert result["task_name"] == "Test Task"


# Test case 2: Test report generation with empty data
def test_empty_data_report():
    mock_data = {}

    result = generate_report(mock_data)

    # Assuming it returns a default report or error
    assert "task_id" not in result  # Adjust based on your function's behavior
    assert "task_name" not in result
    assert "related_comments" not in result


# Test case 3: Test report generation with invalid data format
def test_invalid_data_format():
    mock_data = (
        "Invalid data"  # Simulating invalid format (e.g., string instead of dictionary)
    )

    with pytest.raises(ValueError):  # Assuming ValueError is raised for invalid format
        generate_report(mock_data)


# Test case 4: Test report generation with missing required parameters
def test_missing_parameters():
    mock_data = {
        "task_id": "12345"
        # Missing 'task_name' and 'related_comments'
    }

    result = generate_report(mock_data)

    # Check if a default value is returned for missing parameters or handle it accordingly
    assert "task_name" in result  # Assuming a default value is set for missing keys
    assert "related_comments" in result


# Test case 5: Test report generation in JSON format (Assuming your function supports format choice)
def test_json_report_format():
    mock_data = {
        "task_id": "12345",
        "task_name": "Test Task",
        "related_comments": "Test Comment",
    }

    result = generate_report(
        mock_data, format="json"
    )  # Assuming the 'format' argument is accepted

    assert isinstance(result, dict)  # JSON will typically be returned as a dictionary


# Test case 6: Test report generation in CSV format
def test_csv_report_format():
    mock_data = {
        "task_id": "12345",
        "task_name": "Test Task",
        "related_comments": "Test Comment",
    }

    result = generate_report(
        mock_data, format="csv"
    )  # Assuming the 'format' argument is accepted

    # Check if result is in CSV format (simplified check for demonstration)
    assert isinstance(result, str)  # CSV output is usually a string
    assert "task_id" in result
    assert "task_name" in result


# Test case 7: Test report generation in PDF format (Assuming the 'format' argument is accepted)
def test_pdf_report_format():
    mock_data = {
        "task_id": "12345",
        "task_name": "Test Task",
        "related_comments": "Test Comment",
    }

    result = generate_report(mock_data, format="pdf")

    # For PDF, we might just check if the result contains expected data or a file path
    assert isinstance(result, bytes)  # Assuming the PDF is returned as a byte object
    assert len(result) > 0  # Check if PDF data is returned


# Test case 8: Test report generation with external data source (mocking external call)
@patch(
    "your_module.external_data_source",
    return_value={"task_id": "12345", "task_name": "External Task"},
)
def test_external_data_source(mock_data_source):
    result = generate_report(None)  # The function fetches data from the external source

    # Verify that the external data source is called
    mock_data_source.assert_called_once()

    # Verify that the generated report contains the expected task name
    assert result["task_name"] == "External Task"
