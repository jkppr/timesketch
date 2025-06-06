# Copyright 2019 Google Inc. All rights reserved.
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
"""This file contains a class for managing charts."""


class ChartManager:
    """The chart manager."""

    _class_registry = {}

    @classmethod
    def get_charts(cls):
        """Retrieves the registered charts.

        Yields:
            tuple: containing:
                unicode: the uniquely identifying name of the chart
                type: the chart class.
        """
        yield from iter(cls._class_registry.items())

    @classmethod
    def get_chart(cls, chart_name):
        """Retrieves a class object of a specific chart.

        Args:
            chart_name (unicode): name of the chart to retrieve.

        Returns:
            Chart class object or None if not existing.
        """
        try:
            chart_class = cls._class_registry[chart_name.lower()]
        except KeyError as e:
            raise KeyError(f"No such chart type: {chart_name.lower():s}") from e
        return chart_class

    @classmethod
    def register_chart(cls, chart_class):
        """Registers a chart class.

        The chart classes are identified by their lower case name.

        Args:
            chart_class (type): the chart class to register.

        Raises:
            KeyError: if class is already set for the corresponding name.
        """
        chart_name = chart_class.NAME.lower()
        if chart_name in cls._class_registry:
            raise KeyError(f"Class already set for name: {chart_class.NAME:s}.")
        cls._class_registry[chart_name] = chart_class

    @classmethod
    def clear_registration(cls):
        """Clears all chart registrations."""
        cls._class_registry = {}
