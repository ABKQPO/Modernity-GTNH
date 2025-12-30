import json
import os
import sys

INDENT = 2
ENCODING = "utf-8"
EXTENSIONS = (".json", ".mcmeta")

def format_file(path):
    try:
        with open(path, "r", encoding=ENCODING) as f:
            data = json.load(f)

        with open(path, "w", encoding=ENCODING, newline="\n") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=INDENT,
                separators=(",", ": ")
            )
            f.write("\n")

        print(f"✔ formatted: {path}")

    except Exception as e:
        print(f"✘ failed: {path} ({e})")

def walk(root):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(EXTENSIONS):
                format_file(os.path.join(dirpath, name))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python format_json_like_dir.py <directory>")
        sys.exit(1)

    walk(sys.argv[1])
