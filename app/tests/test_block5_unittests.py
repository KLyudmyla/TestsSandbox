import pytest
import re
from typing import List, Dict, Any


class FileUploadValidationError(Exception):
    """Raised when a batch of uploaded files violates size, count, or format rules."""
    pass

# =====================================================================
# BLOCK 5: Advanced Business Validation (File Upload Rules)
# ---------------------------------------------------------------------
# Testing Guidance:
# - Practice structural mapping testing by passing arrays of complex dictionaries.
# - Verify cascading limits: trigger file count limit first, then validation extension, then size limits.
# - Apply 'pytest.fixture' to pass pre-configured clean state files into your test cases.
# =====================================================================

class FileUploadValidator:
    """
    Validates a batch of files uploaded by a user based on strict corporate limits.
    """

    def __init__(self, max_files: int = 3, max_total_size_mb: float = 10.0):
        self.max_files = max_files
        self.max_total_size_mb = max_total_size_mb
        self.allowed_extensions = {".pdf", ".txt", ".docx"}

    def validate_batch(self, files: List[Dict[str, Any]]) -> bool:
        """
        Validates a list of file dictionaries.
        Each dictionary represents a file: {"name": "document.pdf", "size_mb": 2.5}

        Rules:
        - Total number of files must not exceed max_files.
        - Total cumulative size of all files must not exceed max_total_size_mb.
        - Every file extension must be in the allowed_extensions set.

        :param files: A list of dictionaries containing file metadata.
        :return: True if the batch is valid.
        :raises FileUploadValidationError: If any rule is broken.
        """
        if len(files) > self.max_files:
            raise FileUploadValidationError(f"Too many files. Maximum allowed is {self.max_files}.")

        total_size = 0.0
        for file_info in files:
            name = file_info.get("name", "")
            size = file_info.get("size_mb", 0.0)

            if not any(name.lower().endswith(ext) for ext in self.allowed_extensions):
                raise FileUploadValidationError(f"File '{name}' has an unallowed format.")

            total_size += size

        if total_size > self.max_total_size_mb:
            raise FileUploadValidationError(
                f"Total batch size ({total_size} MB) exceeds limit of {self.max_total_size_mb} MB.")

        return True


@pytest.fixture
def my_files():
    return [
        {"name": "document.pdf", "size_mb": 2.5},
        {"name": "document.txt", "size_mb": 3},
        {"name": "document.docx", "size_mb": 4.5}
    ]

@pytest.fixture
def too_many_files():
    return [
        {"name": "document.pdf", "size_mb": 2.5},
        {"name": "document.txt", "size_mb": 3},
        {"name": "document.docx", "size_mb": 4.5},
        {"name": "document1.pdf", "size_mb": 2},
        {"name": "document2.pdf", "size_mb": 5},
        {"name": "document1.txt", "size_mb": 6}
    ]

@pytest.fixture
def wrong_format_files():
    return [
        {"name": "picture.png", "size_mb": 2.5},
        {"name": "map.html", "size_mb": 3},
    ]

@pytest.fixture
def large_file():
    return [
        {"name": "document123.pdf", "size_mb": 20},
        {"name": "contract.docx", "size_mb": 3},
    ]

@pytest.fixture
def file_with_missing_key():
    return [
        {"name": "document123.pdf"},
        {"name": "contract.docx", "size_mb": 3},
    ]

class TestFileUploadValidator:

    def test_validate_file_upload_basic(self, my_files):
        validator = FileUploadValidator(max_files=3, max_total_size_mb=10.0)
        assert validator.validate_batch(my_files) is True

    def test_raising_exception_for_too_many_files(self, too_many_files):
        validator = FileUploadValidator(max_files=3, max_total_size_mb=10.0)
        with pytest.raises(FileUploadValidationError, match="Too many files. Maximum allowed is 3."):
            validator.validate_batch(too_many_files)

    def test_raising_exception_for_wrong_file_format(self, wrong_format_files):
        validator = FileUploadValidator(max_files=3, max_total_size_mb=10.0)
        with pytest.raises(FileUploadValidationError, match="File 'picture.png' has an unallowed format."):
            validator.validate_batch(wrong_format_files)

    def test_raising_exception_for_large_file(self, large_file):
        validator = FileUploadValidator(max_files=3, max_total_size_mb=10.0)
        with pytest.raises(FileUploadValidationError, match=re.escape("Total batch size (23.0 MB) exceeds limit of 10.0 MB.")):
            validator.validate_batch(large_file)

