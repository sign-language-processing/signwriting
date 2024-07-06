import json
from pathlib import Path

# Define file paths
json_path = Path(__file__).parent / "mouthing.json"
readme_path = Path(__file__).parent / "README.md"

if __name__ == "__main__":
    # Load the JSON data
    with json_path.open() as f:
        data = json.load(f)

    # Generate the markdown table
    table_header = "| IPA | SpeechWriting | SignWriting | Grapheme | Example | Description | Instruction | \n"
    table_divider = "| --- | ------- | ------- | -------- | ------- | ----------- | ----------- | \n"
    table_rows = []

    for ipa, details in data.items():
        standard = f"![{ipa}](standard/{ipa}.png)"
        writing = details.get("writing", "")
        if writing != "":
            image = f"https://www.signbank.org/signpuddle2.0/glyphogram.php?text={writing}&pad=10&size=2"
            writing = f"![{writing}]({image})"
        grapheme = details.get("grapheme", "")
        example = details.get("example", "")
        description = details.get("description", "")
        instruction = details.get("instruction", "")
        all_ipa = " / ".join([ipa] + details.get("alternatives", []))
        row = f"| {all_ipa} | {standard} | {writing} | {grapheme} | {example} | {description} | {instruction} |\n"
        table_rows.append(row)

    # Read the current README.md content
    with readme_path.open() as f:
        readme_content = f.read()

    # Find the position of "## Table" and insert the table after it
    table_section = "## Table"
    text_before_table = readme_content[:readme_content.find(table_section)]

    table = table_header + table_divider + "".join(table_rows)
    new_readme_content = text_before_table + table_section + "\n\n" + table

    # Write the new content back to README.md
    with readme_path.open("w") as f:
        f.write(new_readme_content)

    print("Table added to README.md successfully.")
