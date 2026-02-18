# Copyright 2026 Google Inc. All rights reserved.
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
"""Tests for the main application entry point."""

from unittest.mock import patch
from timesketch.app import create_app
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import TestConfig


class AppTest(BaseTest):
    """Test the main Flask app creation logic."""

    @patch("timesketch.app.db_session")
    def test_database_session_teardown(self, mock_db_session):
        """Test that the database session is removed on app context teardown."""
        app = create_app(config=TestConfig)

        # 1. Verify shutdown_session is registered
        teardown_funcs = app.teardown_appcontext_funcs
        shutdown_func = next(
            (func for func in teardown_funcs if func.__name__ == "shutdown_session"),
            None,
        )
        self.assertIsNotNone(
            shutdown_func, "shutdown_session not registered in teardown_appcontext"
        )

        # 2. Verify db_session.remove() is called when context exits
        with app.app_context():
            pass  # Just enter and exit the context

        # Assert that remove() was called exactly once
        mock_db_session.remove.assert_called_once()
