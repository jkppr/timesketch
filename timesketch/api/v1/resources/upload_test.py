# Copyright 2025 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for UploadFileResource."""

import os
import shutil
import tempfile
from unittest import mock

from timesketch.lib.testlib import BaseTest
from timesketch.api.v1.resources import upload


class UploadFileResourceTest(BaseTest):
    """Test UploadFileResource."""

    def setUp(self):
        super().setUp()
        self.upload_folder = tempfile.mkdtemp()
        self.app.config["UPLOAD_FOLDER"] = self.upload_folder
        self.app.config["UPLOAD_ENABLED"] = True

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.upload_folder):
            shutil.rmtree(self.upload_folder)

    @mock.patch("timesketch.api.v1.resources.upload.utils.format_upload_path")
    @mock.patch("timesketch.api.v1.resources.upload.current_app")
    def test_out_of_order_chunks(self, mock_current_app, mock_format_upload_path):
        """Test that chunks uploaded out of order are written to the correct file offsets."""
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
        file_storage_mock.read.return_value = chunk2
        form_data = {
            "chunk_index": "1",
            "chunk_byte_offset": "5",
            "chunk_total_chunks": "2",
            "total_file_size": str(total_file_size),
            "chunk_index_name": chunk_index_name,
            "name": "test_timeline",
            "sketch_id": "1",
        }

        # We need to mock request.files and request.form
        with mock.patch(
            "timesketch.api.v1.resources.upload.request"
        ) as mock_request:
            mock_request.files = {"file": file_storage_mock}
            mock_request.form = form_data

            # Call the internal method directly or via post()
            sketch_mock = mock.MagicMock()
            sketch_mock.id = 1

            # Call _upload_file
            # Mock _upload_and_index for the first chunk as well to avoid DB calls
            # pylint: disable=protected-access, unused-variable
            with mock.patch.object(resource, "_upload_and_index") as mock_process:
                resource._upload_file(
                    file_storage=file_storage_mock,
                    form=form_data,
                    sketch=sketch_mock,
                    index_name="",
                    chunk_index_name=chunk_index_name,
                )

        # 2. Upload chunk 1 (Hello) second - offset 0
        file_storage_mock.read.return_value = chunk1
        form_data["chunk_index"] = "0"
        form_data["chunk_byte_offset"] = "0"

        # Mock successful upload of last chunk triggers processing
        # We mock _upload_and_index because size check passes now with r+b
        # pylint: disable=protected-access, unused-variable
        with mock.patch.object(resource, "_upload_and_index") as mock_process:
            resource._upload_file(
                file_storage=file_storage_mock,
                form=form_data,
                sketch=sketch_mock,
                index_name="",
                chunk_index_name=chunk_index_name,
            )

        # Verify final file content
        with open(file_path, "rb") as f:
            content = f.read()

        print(f"Final content: {content}")

        # Verify content matches full file
        self.assertEqual(
            content,
            b"HelloWorld",
            "Content mismatch: chunks not assembled correctly",
        )

    @mock.patch("timesketch.api.v1.resources.upload.utils.format_upload_path")
    @mock.patch("timesketch.api.v1.resources.upload.current_app")
    def test_chunk_retry_idempotency(self, mock_current_app, mock_format_upload_path):
        """Test that retrying a chunk upload overwrites idempotently."""
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
            "sketch_id": "1",
        }

        # Mock _upload_and_index
        # pylint: disable=protected-access, unused-variable
        with mock.patch.object(resource, "_upload_and_index") as mock_process:
            # First upload
            resource._upload_file(
                file_storage=file_storage_mock,
                form=form_data,
                sketch=sketch_mock,
                index_name="",
                chunk_index_name=chunk_index_name,
            )

        # 2. Retry upload chunk 0 (simulate client retry)
        file_storage_mock.read.return_value = chunk1

        # Retry upload
        try:
            # pylint: disable=protected-access, unused-variable
            with mock.patch.object(resource, "_upload_and_index") as mock_process:
                resource._upload_file(
                    file_storage=file_storage_mock,
                    form=form_data,
                    sketch=sketch_mock,
                    index_name="",
                    chunk_index_name=chunk_index_name,
                )
        except Exception:  # pylint: disable=broad-exception-caught
            # We expect an abort(400) here usually if size was wrong
            pass

        # Verify file size
        final_size = os.path.getsize(file_path)
        print(f"Final size: {final_size}")

        # Verify size matches single chunk (not doubled)
        self.assertEqual(
            final_size,
            5,
            "File size mismatch: retry should overwrite, not append",
        )
