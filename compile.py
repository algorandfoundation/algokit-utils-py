import os
from pathlib import Path

def remove_line_numbers(code: str) -> str:
    lines = code.splitlines()
    processed_lines = []
    for line in lines:
        if "|" in line:
            line_number, content = line.split("|", 1)
            if line_number.strip().isdigit():
                line = content.lstrip()
        processed_lines.append(line)
    return "\n".join(processed_lines)

def combine_algokit_utils(source_dir: Path, output_file: Path):
    combined_code = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                    code = remove_line_numbers(code)
                    relative_path = file_path.relative_to(source_dir.parent)
                    combined_code.append(f"# === File: {relative_path} ===\n{code}\n")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(combined_code))

if __name__ == "__main__":
    source_directory = Path("src/algokit_utils")
    output_file = Path("combined_algokit_utils.py")
    combine_algokit_utils(source_directory, output_file)
