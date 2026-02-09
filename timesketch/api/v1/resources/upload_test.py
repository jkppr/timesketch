
import os
import shutil
import tempfile
import json
import unittest
from unittest import mock
from flask import Flask

from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.api.v1.resources import upload

class UploadFileResourceTest(BaseTest):
    """Test UploadFileResource."""

    def setUp(self):
        super().setUp()
        self.upload_folder = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.upload_folder
        self.app.config['UPLOAD_ENABLED'] = True

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.upload_folder):
            shutil.rmtree(self.upload_folder)

    @mock.patch('timesketch.api.v1.resources.upload.utils.format_upload_path')
    @mock.patch('timesketch.api.v1.resources.upload.current_app')
    def test_chunked_upload_ab_mode_failure(self, mock_current_app, mock_format_upload_path):
        """Test that demonstrates failure of 'ab' mode with out-of-order chunks."""
        mock_current_app.config = self.app.config

        # Setup mock behavior
        chunk_index_name = "00000000000000000000000000000001"
        file_path = os.path.join(self.upload_folder, chunk_index_name)
        mock_format_upload_path.return_value = file_path

        # Simulate two chunks of a file: "Hello" and "World"
        # Total size = 10 bytes
        chunk1 = b"Hello"
        chunk2 = b"World"
        total_file_size = len(chunk1) + len(chunk2)

        # Create resource instance
        resource = upload.UploadFileResource()

        # Mock request file storage
        file_storage_mock = mock.MagicMock()

        # 1. Upload chunk 2 (World) first - offset 5
        # With 'ab', this will be written at offset 0 because file is empty/new
        file_storage_mock.read.return_value = chunk2
        form_data = {
            "chunk_index": "1",
            "chunk_byte_offset": "5",
            "chunk_total_chunks": "2",
            "total_file_size": str(total_file_size),
            "chunk_index_name": chunk_index_name,
            "name": "test_timeline",
            "sketch_id": "1"
        }

        # We need to mock request.files and request.form
        with mock.patch('timesketch.api.v1.resources.upload.request') as mock_request:
             mock_request.files = {'file': file_storage_mock}
             mock_request.form = form_data

             # Call the internal method directly or via post()
             # calling internal _upload_file to avoid permission checks in post()
             # and simplify the test focus on file writing
             sketch_mock = mock.MagicMock()
             sketch_mock.id = 1

             # Call _upload_file
             # We mock _upload_and_index because size check might pass now with r+b
             with mock.patch.object(resource, '_upload_and_index') as mock_process:
                 resource._upload_file(
                     file_storage=file_storage_mock,
                     form=form_data,
                     sketch=sketch_mock,
                     index_name="",
                     chunk_index_name=chunk_index_name
                 )

        # Verify file content after first chunk (out of order)
        with open(file_path, 'rb') as f:
            content = f.read()

        # With 'ab', it wrote "World" at the beginning
        # Expected if it worked correctly (with seek): 5 null bytes then "World"
        # Actual with 'ab': "World"
        # So size is 5, content is "World"

        # 2. Upload chunk 1 (Hello) second - offset 0
        # With 'ab', this will append "Hello" at the end (offset 5)
        file_storage_mock.read.return_value = chunk1
        form_data['chunk_index'] = "0"
        form_data['chunk_byte_offset'] = "0"

        # Mock successful upload of last chunk triggers processing
        # We want to fail before processing if size is wrong

        # We need to handle the recursive call in _upload_file when done
        # But here we just want to verify file content on disk

        # Mock _upload_and_index to avoid actual processing
        with mock.patch.object(resource, '_upload_and_index') as mock_process:
             resource._upload_file(
                 file_storage=file_storage_mock,
                 form=form_data,
                 sketch=sketch_mock,
                 index_name="",
                 chunk_index_name=chunk_index_name
             )

        # Verify final file content
        with open(file_path, 'rb') as f:
            content = f.read()

        # Expected: "HelloWorld"
        # Actual with 'ab': "WorldHello"

        print(f"Final content: {content}")

        # This assertion simulates the check we want to enforce
        # If the code was correct (using r+b and seek), content should be b"HelloWorld"
        # But current code produces b"WorldHello"
        self.assertEqual(content, b"HelloWorld", "Content mismatch due to 'ab' mode not respecting offsets")

    @mock.patch('timesketch.api.v1.resources.upload.utils.format_upload_path')
    @mock.patch('timesketch.api.v1.resources.upload.current_app')
    def test_chunked_upload_retry_failure(self, mock_current_app, mock_format_upload_path):
        """Test that demonstrates failure of 'ab' mode with retried chunks."""
        mock_current_app.config = self.app.config

        # Setup mock behavior
        chunk_index_name = "00000000000000000000000000000002"
        file_path = os.path.join(self.upload_folder, chunk_index_name)
        mock_format_upload_path.return_value = file_path

        chunk1 = b"Hello"
        total_file_size = len(chunk1)

        resource = upload.UploadFileResource()
        file_storage_mock = mock.MagicMock()
        sketch_mock = mock.MagicMock()
        sketch_mock.id = 1

        # 1. Upload chunk 0
        file_storage_mock.read.return_value = chunk1
        form_data = {
            "chunk_index": "0",
            "chunk_byte_offset": "0",
            "chunk_total_chunks": "1",
            "total_file_size": str(total_file_size),
            "chunk_index_name": chunk_index_name,
            "name": "test_timeline",
            "sketch_id": "1"
        }

        # Mock _upload_and_index
        with mock.patch.object(resource, '_upload_and_index') as mock_process:
             # First upload
             resource._upload_file(
                 file_storage=file_storage_mock,
                 form=form_data,
                 sketch=sketch_mock,
                 index_name="",
                 chunk_index_name=chunk_index_name
             )

        # 2. Retry upload chunk 0 (simulate client retry)
        file_storage_mock.read.return_value = chunk1

        # It triggers file size check at the end of _upload_file because chunk_index + 1 == total
        # We expect it to FAIL because size will be 2x

        # However, _upload_file raises BAD_REQUEST if size is wrong
        # We capture that

        # We need to ensure we don't crash on the first call which succeeds

        # Retry upload
        try:
             with mock.patch.object(resource, '_upload_and_index') as mock_process:
                 resource._upload_file(
                     file_storage=file_storage_mock,
                     form=form_data,
                     sketch=sketch_mock,
                     index_name="",
                     chunk_index_name=chunk_index_name
                 )
        except Exception as e:
            # We expect an abort(400) here usually, but let's check file size first
            pass

        # Verify file size
        final_size = os.path.getsize(file_path)
        print(f"Final size: {final_size}")

        # Expected: 5 (idempotent retry)
        # Actual with 'ab': 10 (appended)
        self.assertEqual(final_size, 5, "File size mismatch due to 'ab' mode appending on retry")
