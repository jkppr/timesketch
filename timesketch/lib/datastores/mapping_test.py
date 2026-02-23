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

from timesketch.api.v1.resources.sketch import SketchResource
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

        # Check for dynamic_templates
        self.assertIn("dynamic_templates", mappings)
        templates = mappings["dynamic_templates"]
        found_template = False
        for template in templates:
            if "strings_as_wildcard" in template:
                mapping = template["strings_as_wildcard"]["mapping"]
                self.assertIn("wildcard", mapping["fields"])
                self.assertEqual(mapping["fields"]["wildcard"]["type"], "wildcard")
                found_template = True
                break
        self.assertTrue(
            found_template, "Wildcard dynamic template not found in plaso.mappings"
        )

        # Check explicit properties
        properties = mappings["properties"]
        # Check "message_type" as a representative field
        self.assertIn("message_type", properties)
        self.assertIn("wildcard", properties["message_type"]["fields"])
        self.assertEqual(
            properties["message_type"]["fields"]["wildcard"]["type"], "wildcard"
        )

    @mock.patch("timesketch.lib.datastores.opensearch.OpenSearch")
    def test_build_query_wildcard_mode(self, mock_client):  # pylint: disable=unused-argument
        """Test build_query with wildcard_mode enabled."""
        # Mock client to avoid connection attempts
        ds = OpenSearchDataStore(host="127.0.0.1", port=9200)

        # Case 1: Wildcard Mode Enabled
        query = ds.build_query(
            sketch_id=1,
            query_string="foo",
            query_filter={},
            query_dsl=None,
            aggregations=None,
            wildcard_mode=True,
        )

        # Check that query_string has default_field = "*.wildcard"
        self.assertIn("query", query)
        self.assertIn("bool", query["query"])
        self.assertIn("must", query["query"]["bool"])
        must_clause = query["query"]["bool"]["must"]

        found_qs = False
        for clause in must_clause:
            if "query_string" in clause:
                qs = clause["query_string"]
                if qs.get("default_field") == "*.wildcard":
                    found_qs = True
        self.assertTrue(
            found_qs, "Did not find expected default_field='*.wildcard' in query_string"
        )

        # Case 2: Wildcard Mode Disabled (Default)
        query = ds.build_query(
            sketch_id=1,
            query_string="foo",
            query_filter={},
            query_dsl=None,
            aggregations=None,
            wildcard_mode=False,
        )
        must_clause = query["query"]["bool"]["must"]
        found_qs_legacy = False
        for clause in must_clause:
            if "query_string" in clause:
                qs = clause["query_string"]
                if "default_field" not in qs:
                    found_qs_legacy = True
        self.assertTrue(
            found_qs_legacy, "Found unexpected default_field in legacy query mode"
        )

    def test_sketch_resource_check_wildcard_support(self):
        """Test _check_wildcard_search_support logic."""
        # Case 1: No indices
        self.assertFalse(SketchResource._check_wildcard_search_support([], {}))

        # Case 2: Legacy index present
        indices_meta = {"legacy_idx": {"is_legacy": True}}
        self.assertFalse(
            SketchResource._check_wildcard_search_support(
                ["legacy_idx"], indices_meta
            )
        )

        # Case 3: Mixed legacy and new
        indices_meta = {
            "legacy_idx": {"is_legacy": True},
            "new_idx": {"is_legacy": False},
        }
        self.assertFalse(
            SketchResource._check_wildcard_search_support(
                ["legacy_idx", "new_idx"], indices_meta
            )
        )

        # Case 4: Only new indices
        indices_meta = {"new_idx": {"is_legacy": False}}
        self.assertTrue(
            SketchResource._check_wildcard_search_support(["new_idx"], indices_meta)
        )
