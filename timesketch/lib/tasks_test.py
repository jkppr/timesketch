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
"""Tests for tasks."""

import sys
from unittest import mock

# Mock timesketch.app.create_celery_app before importing timesketch.lib.tasks
# because timesketch.lib.tasks calls create_celery_app() at module level.
import timesketch.app

mock_celery = mock.MagicMock()
def task_decorator(*args, **kwargs):
    def decorator(f):
        return f
    return decorator
mock_celery.task = task_decorator
# Mock celery.Task so SqlAlchemyTask can inherit from it
mock_celery.Task = object

timesketch.app.create_celery_app = mock.Mock(return_value=mock_celery)

from timesketch.lib.testlib import BaseTest
from timesketch.lib import tasks

class TestTasks(BaseTest):
    """Tests for the tasks."""

    def setUp(self):
        super().setUp()
        # Inject pinfo_tool into tasks module if it doesn't exist (because plaso missing)
        if not hasattr(tasks, "pinfo_tool"):
            tasks.pinfo_tool = mock.MagicMock()

    @mock.patch("timesketch.lib.tasks.db_session")
    @mock.patch("timesketch.lib.tasks.plaso")
    @mock.patch("timesketch.lib.tasks.subprocess.check_output")
    @mock.patch("timesketch.lib.tasks.OpenSearchDataStore")
    @mock.patch("timesketch.lib.tasks.SearchIndex")
    @mock.patch("timesketch.lib.tasks._set_datasource_status")
    @mock.patch("timesketch.lib.tasks._set_datasource_total_events")
    def test_run_plaso_with_filter(
        self,
        mock_set_total_events,
        mock_set_status,
        mock_search_index,
        mock_datastore,
        mock_subprocess,
        mock_plaso,
        mock_db_session,
    ):
        """Test run_plaso task with a filter."""
        # Setup mocks
        mock_plaso.__version__ = "20220101"

        # Configure pinfo_tool mock
        mock_pinfo_instance = tasks.pinfo_tool.PinfoTool.return_value
        mock_storage_reader = mock.Mock()
        mock_pinfo_instance._GetStorageReader.return_value = mock_storage_reader
        mock_pinfo_instance._CalculateStorageCounters.return_value = {
            "parsers": {"total": 100}
        }

        # Configure SearchIndex mock
        mock_index_obj = mock.MagicMock()
        mock_search_index.query.filter_by.return_value.first.return_value = mock_index_obj

        # Configure OpenSearchDataStore mock
        mock_datastore_instance = mock_datastore.return_value
        mock_datastore_instance.client.indices.exists.return_value = True
        mock_datastore_instance.create_index.return_value = "test_index"

        mock_connection = mock.Mock()
        mock_connection.host = "http://localhost:9200"
        mock_connection.port = 9200
        mock_datastore_instance.client.transport.get_connection.return_value = mock_connection

        # Run the task
        tasks.run_plaso(
            file_path="/tmp/test.plaso",
            events="",
            timeline_name="test_timeline",
            index_name="test_index",
            source_type="plaso",
            timeline_id=1,
            plaso_event_filter="parser:syslog",
        )

        # Verify that subprocess was called with the filter
        self.assertTrue(mock_subprocess.called, "subprocess.check_output was not called")
        args, _ = mock_subprocess.call_args
        cmd_list = args[0]

        self.assertIn("parser:syslog", cmd_list)
        self.assertEqual(cmd_list[-1], "parser:syslog")

    @mock.patch("timesketch.lib.tasks.db_session")
    @mock.patch("timesketch.lib.tasks.plaso")
    @mock.patch("timesketch.lib.tasks.subprocess.check_output")
    @mock.patch("timesketch.lib.tasks.OpenSearchDataStore")
    @mock.patch("timesketch.lib.tasks.SearchIndex")
    @mock.patch("timesketch.lib.tasks._set_datasource_status")
    @mock.patch("timesketch.lib.tasks._set_datasource_total_events")
    def test_run_plaso_without_filter(
        self,
        mock_set_total_events,
        mock_set_status,
        mock_search_index,
        mock_datastore,
        mock_subprocess,
        mock_plaso,
        mock_db_session,
    ):
        """Test run_plaso task without a filter."""
        # Setup mocks
        mock_plaso.__version__ = "20220101"

        # Configure pinfo_tool mock
        mock_pinfo_instance = tasks.pinfo_tool.PinfoTool.return_value
        mock_storage_reader = mock.Mock()
        mock_pinfo_instance._GetStorageReader.return_value = mock_storage_reader
        mock_pinfo_instance._CalculateStorageCounters.return_value = {
            "parsers": {"total": 100}
        }

        # Configure SearchIndex mock
        mock_index_obj = mock.MagicMock()
        mock_search_index.query.filter_by.return_value.first.return_value = mock_index_obj

        # Configure OpenSearchDataStore mock
        mock_datastore_instance = mock_datastore.return_value
        mock_datastore_instance.client.indices.exists.return_value = True
        mock_datastore_instance.create_index.return_value = "test_index"

        mock_connection = mock.Mock()
        mock_connection.host = "http://localhost:9200"
        mock_connection.port = 9200
        mock_datastore_instance.client.transport.get_connection.return_value = mock_connection

        # Run the task
        tasks.run_plaso(
            file_path="/tmp/test.plaso",
            events="",
            timeline_name="test_timeline",
            index_name="test_index",
            source_type="plaso",
            timeline_id=1,
        )

        # Verify that subprocess was called without the filter
        self.assertTrue(mock_subprocess.called, "subprocess.check_output was not called")
        args, _ = mock_subprocess.call_args
        cmd_list = args[0]

        self.assertNotIn("parser:syslog", cmd_list)
