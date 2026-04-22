import re

with open("timesketch/lib/analyzers/hashr_lookup.py", "r") as f:
    content = f.read()

bad_snippet1 = """            for h in unique_hashes:
                # Some hashes might not be exactly 64 chars in ES, we can filter them out here
                if len(h) != 64:"""

good_snippet1 = """            for h in unique_hashes:
                # Some hashes might not be exactly 64 chars in OpenSearch, we can filter them out here
                if len(h) != 64:"""

content = content.replace(bad_snippet1, good_snippet1)


bad_snippet2 = """                        if val and len(val) == 64:
                            unique_hashes.add(val)
                            break"""

good_snippet2 = """                        if val:
                            unique_hashes.add(val)
                            break"""

content = content.replace(bad_snippet2, good_snippet2)


with open("timesketch/lib/analyzers/hashr_lookup.py", "w") as f:
    f.write(content)
