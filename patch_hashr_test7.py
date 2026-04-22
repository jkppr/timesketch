import re

with open("timesketch/lib/analyzers/hashr_lookup.py", "r") as f:
    content = f.read()

bad_snippet3 = """        events = self.event_stream(query_string=query, return_fields=return_fields)
        events_list = list(events)"""

good_snippet3 = """        events = self.event_stream(query_string=query, return_fields=return_fields)
        events_list = list(events)"""

# I need to fix the test where "8bbd7976b2b86e1746494c98425e7830" is tested for warning, and I need to make sure that get_all_unique_hashes doesn't drop it.
# Actually, I changed the `get_all_unique_hashes` fallback to add `val` if it's there.

with open("timesketch/lib/analyzers/hashr_lookup.py", "w") as f:
    f.write(content)
