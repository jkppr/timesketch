# Copyright 2023 Google Inc. All rights reserved.
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
"""Tests for mapping files and wildcard support."""

import json
import os
from unittest import mock

from timesketch.lib.datastores.opensearch import OpenSearchDataStore
from timesketch.lib.testlib import BaseTest


class MappingTest(BaseTest):
    """Tests for mapping files and wildcard support."""

    def test_generic_mappings(self):
        """Test that generic.mappings contains the wildcard dynamic template."""
        # Relative path from repo root
        mapping_path = "data/generic.mappings"
        if not os.path.exists(mapping_path):
            self.skipTest(f"Could not find {mapping_path}")

        with open(mapping_path, "r", encoding="utf-8") as f:
            mappings = json.load(f)

        self.assertIn("dynamic_templates", mappings)
        templates = mappings["dynamic_templates"]
        found = False
        for template in templates:
            if "strings_as_wildcard" in template:
                mapping = template["strings_as_wildcard"]["mapping"]
                self.assertIn("wildcard", mapping["fields"])
                self.assertEqual(mapping["fields"]["wildcard"]["type"], "wildcard")
                found = True
                break
        self.assertTrue(
            found, "Wildcard dynamic template not found in generic.mappings"
        )

    def test_plaso_mappings(self):
        """Test that plaso.mappings contains wildcard fields."""
        mapping_path = "data/plaso.mappings"
        if not os.path.exists(mapping_path):
            self.skipTest(f"Could not find {mapping_path}")

        with open(mapping_path, "r", encoding="utf-8") as f:
            mappings = json.load(f)

        properties = mappings["properties"]
        # Check "message_type" as a representative field
        self.assertIn("message_type", properties)
        self.assertIn("wildcard", properties["message_type"]["fields"])
        self.assertEqual(
            properties["message_type"]["fields"]["wildcard"]["type"], "wildcard"
        )

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_build_query_wildcard(self, mock_client):  # pylint: disable=unused-argument
        """Test build_query with wildcard field."""
        # Mock client to avoid connection attempts
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)

        # Case 1: Special chars in value, but field is .wildcard
        # Should NOT append .keyword
        query = ds.build_query(
            sketch_id=1,
            query_string="field.wildcard:???",
            query_filter={},
            query_dsl=None,
            aggregations=None,
        )

        # We expect a query_string query
        self.assertIn("query", query)
        self.assertIn("bool", query["query"])
        self.assertIn("must", query["query"]["bool"])
        must_clause = query["query"]["bool"]["must"]

        # Check if query_string clause is present with our query
        found_qs = False
        for clause in must_clause:
            if "query_string" in clause:
                if clause["query_string"]["query"] == "field.wildcard:???":
                    found_qs = True
        self.assertTrue(
            found_qs, "Did not find expected query_string query for wildcard field"
        )

        # Case 2: Special chars in value, and field is NOT .wildcard
        # Should append .keyword (existing behavior)
        query = ds.build_query(
            sketch_id=1,
            query_string="field:???",
            query_filter={},
            query_dsl=None,
            aggregations=None,
        )
        must_clause = query["query"]["bool"]["must"]
        found_term = False
        for clause in must_clause:
            if "term" in clause:
                if (
                    "field.keyword" in clause["term"]
                    and clause["term"]["field.keyword"] == "???"
                ):
                    found_term = True
        self.assertTrue(
            found_term,
            "Did not find expected term query on .keyword field for normal field",
        )
