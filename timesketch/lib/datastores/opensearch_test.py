# Copyright 2024 Google Inc. All rights reserved.
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
"""Tests for OpenSearchDataStore."""

import unittest
from unittest import mock

from opensearchpy import OpenSearch # Added for autospec
from opensearchpy.exceptions import ConnectionTimeout
from opensearchpy.exceptions import TransportError
from urllib3.exceptions import ReadTimeoutError as Urllib3ReadTimeoutError

from timesketch.lib.datastores.opensearch import OpenSearchDataStore
from timesketch.lib.testlib import BaseTest


class TestOpenSearchDataStore(BaseTest):
    """Tests for the OpenSearchDataStore."""

    @mock.patch("opensearchpy.OpenSearch")
    def test_search_read_timeout_error(self, mock_opensearch_client_constructor):
        """
        Tests that OpenSearchDataStore.search handles a ReadTimeoutError
        correctly, as wrapped by opensearchpy's ConnectionTimeout.
        """
        # Mock the OpenSearch client instance
        mock_os_client = mock.create_autospec(OpenSearch, instance=True)
        mock_opensearch_client_constructor.return_value = mock_os_client

        # Mock the return value of transport.perform_request, which info() calls
        mock_os_client.transport.perform_request.return_value = {
            "name": "mock_opensearch_node",
            "cluster_name": "mock_cluster",
            "cluster_uuid": "mock_uuid",
            "version": {
                "number": "7.0.0", # This is what OpenSearchDataStore uses
                "build_flavor": "default",
                "build_type": "tar",
                "build_hash": "mock_hash",
                "build_date": "2023-01-01T00:00:00.000Z",
                "build_snapshot": False,
                "lucene_version": "8.0.0",
                "minimum_wire_compatibility_version": "6.8.0",
                "minimum_index_compatibility_version": "6.0.0-beta1"
            },
            "tagline": "The Open Source Search Engine"
        }

        # Configure the client.search mock to raise ConnectionTimeout
        # with info attribute being a ReadTimeoutError instance
        read_timeout_msg = "Read timed out."
        mock_os_client.search.side_effect = ConnectionTimeout(
            "http://mockhost:1234",  # Dummy URL for the 'url' positional argument
            "TIMEOUT",               # Message for the 'message' positional argument
            info=Urllib3ReadTimeoutError(read_timeout_msg)
        )

        # Instantiate OpenSearchDataStore
        # The app context is needed for config values.
        with self.app.app_context():
            datastore = OpenSearchDataStore(host="test_host", port=1234)

        # Call the search method that should trigger the error
        with self.assertRaisesRegex(ValueError, read_timeout_msg):
            datastore.search(
                sketch_id=1,
                indices=["test_index"],
                query_string="test_query"
            )

        # Verify that client.search was called
        mock_os_client.search.assert_called_once()
        
    @mock.patch("opensearchpy.OpenSearch")
    def test_search_transport_error_with_dict_info(self, mock_opensearch_client_constructor):
        """
        Tests that OpenSearchDataStore.search handles a TransportError
        with a dictionary in the info attribute correctly.
        """
        mock_os_client = mock.create_autospec(OpenSearch, instance=True)
        mock_opensearch_client_constructor.return_value = mock_os_client

        # Mock the return value of transport.perform_request, which info() calls
        mock_os_client.transport.perform_request.return_value = {
            "name": "mock_opensearch_node",
            "cluster_name": "mock_cluster",
            "cluster_uuid": "mock_uuid",
            "version": {
                "number": "7.0.0", # This is what OpenSearchDataStore uses
                "build_flavor": "default",
                "build_type": "tar",
                "build_hash": "mock_hash",
                "build_date": "2023-01-01T00:00:00.000Z",
                "build_snapshot": False,
                "lucene_version": "8.0.0",
                "minimum_wire_compatibility_version": "6.8.0",
                "minimum_index_compatibility_version": "6.0.0-beta1"
            },
            "tagline": "The Open Source Search Engine"
        }

        error_info = {
            "error": {
                "root_cause": [
                    {"type": "query_shard_exception", "reason": "Failed to parse query"}
                ],
                "type": "search_phase_execution_exception",
                "reason": "all shards failed",
            },
            "status": 400,
        }
        
        mock_os_client.search.side_effect = TransportError(
            400, "search_phase_execution_exception", error_info
        )
        
        with self.app.app_context():
            datastore = OpenSearchDataStore(host="test_host", port=1234)

        expected_error_msg = "[query_shard_exception] Failed to parse query"
        with self.assertRaisesRegex(ValueError, expected_error_msg):
            datastore.search(
                sketch_id=1,
                indices=["test_index"],
                query_string="test_query"
            )
        mock_os_client.search.assert_called_once()

    @mock.patch("opensearchpy.OpenSearch")
    def test_search_transport_error_non_dict_info(self, mock_opensearch_client_constructor):
        """
        Tests that OpenSearchDataStore.search handles a TransportError
        with a non-dictionary (e.g. string) in the info attribute correctly.
        """
        mock_os_client = mock.create_autospec(OpenSearch, instance=True)
        mock_opensearch_client_constructor.return_value = mock_os_client

        # Mock the return value of transport.perform_request, which info() calls
        mock_os_client.transport.perform_request.return_value = {
            "name": "mock_opensearch_node",
            "cluster_name": "mock_cluster",
            "cluster_uuid": "mock_uuid",
            "version": {
                "number": "7.0.0", # This is what OpenSearchDataStore uses
                "build_flavor": "default",
                "build_type": "tar",
                "build_hash": "mock_hash",
                "build_date": "2023-01-01T00:00:00.000Z",
                "build_snapshot": False,
                "lucene_version": "8.0.0",
                "minimum_wire_compatibility_version": "6.8.0",
                "minimum_index_compatibility_version": "6.0.0-beta1"
            },
            "tagline": "The Open Source Search Engine"
        }

        error_info_str = "A generic transport error occurred"
        
        mock_os_client.search.side_effect = TransportError(
            500, "generic_transport_error", error_info_str
        )
        
        with self.app.app_context():
            datastore = OpenSearchDataStore(host="test_host", port=1234)

        with self.assertRaisesRegex(ValueError, error_info_str):
            datastore.search(
                sketch_id=1,
                indices=["test_index"],
                query_string="test_query"
            )
        mock_os_client.search.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
