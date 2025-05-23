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
        mock_os_client = mock.Mock()
        mock_opensearch_client_constructor.return_value = mock_os_client

        # Configure the client.search mock to raise ConnectionTimeout
        # with info attribute being a ReadTimeoutError instance
        read_timeout_msg = "Read timed out."
        connection_timeout_msg = (
            f"ConnectionTimeout caused by - ReadTimeoutError({read_timeout_msg})"
        )
        
        # Simulate the nested error structure.
        # opensearchpy.exceptions.ConnectionTimeout wraps urllib3.exceptions.ReadTimeoutError.
        # The 'info' attribute of ConnectionTimeout in this scenario holds the ReadTimeoutError.
        mock_os_client.search.side_effect = ConnectionTimeout(
            message=connection_timeout_msg,
            error=connection_timeout_msg, # Often the same as message or more specific
            info=Urllib3ReadTimeoutError(read_timeout_msg) # This is the key part
        )
        
        # Mock OpenSearch client info() call used in constructor
        mock_os_client.info.return_value = {"version": {"number": "7.0.0"}}


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
        mock_os_client = mock.Mock()
        mock_opensearch_client_constructor.return_value = mock_os_client

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
        
        mock_os_client.info.return_value = {"version": {"number": "7.0.0"}}

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
        mock_os_client = mock.Mock()
        mock_opensearch_client_constructor.return_value = mock_os_client

        error_info_str = "A generic transport error occurred"
        
        mock_os_client.search.side_effect = TransportError(
            500, "generic_transport_error", error_info_str
        )
        
        mock_os_client.info.return_value = {"version": {"number": "7.0.0"}}

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
