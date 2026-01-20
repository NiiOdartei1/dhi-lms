import os
import re

# Root directory of your project
root_dir = "./templates"

# Pattern to find wrong static paths
pattern = re.compile(r"url_for\(\s*'static'\s*,\s*filename\s*=\s*'static/(.*?)'\s*\)")

for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".html"):
            filepath = os.path.join(subdir, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace all occurrences
            new_content, count = pattern.subn(r"url_for('static', filename='\1')", content)
            
            if count > 0:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Fixed {count} instance(s) in: {filepath}")
