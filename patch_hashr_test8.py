import re

with open("timesketch/lib/analyzers/hashr_lookup.py", "r") as f:
    content = f.read()

bad_snippet4 = """                        if val:
                            unique_hashes.add(val)
                            break"""

good_snippet4 = """                        if val and len(val) == 64:
                            unique_hashes.add(val)
                            break"""

content = content.replace(bad_snippet4, good_snippet4)

with open("timesketch/lib/analyzers/hashr_lookup.py", "w") as f:
    f.write(content)
