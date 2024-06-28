from pathlib import Path

from signwriting.fingerspelling.fingerspelling import FINGERSPELLING_DIR, get_chars

readme_path = Path(__file__).parent / "README.md"

def online_signwriting_image(sign):
    return f"![{sign}](https://www.signbank.org/signpuddle2.0/glyphogram.php?text={sign}&pad=10&size=2)"

if __name__ == "__main__":
    texts = []

    for language in sorted(FINGERSPELLING_DIR.glob("*")):
        chars = get_chars(language.stem)
        # convert to markdown table
        table = [
            "| " + " | ".join(char for char in chars.keys()) + " |",  # Table head
            "| " + " | ".join("---" for _ in chars.keys()) + " |"  # Table divider
        ]
        max_items = max(len(items) for items in chars.values())
        for i in range(max_items):
            row = "| " + " | ".join([online_signwriting_image(items[i]) if i < len(items) else ""
                                     for items in chars.values()]) + " |"
            table.append(row)

        texts.append(f"### {language.stem}\n\n" + "\n".join(table) + "\n")

    # Read the current README.md content
    with readme_path.open() as f:
        readme_content = f.read()

    # Find the position of "## Table" and insert the table after it
    table_section = "## Existing Characters"
    text_before_table = readme_content[:readme_content.find(table_section)]

    new_readme_content = text_before_table + table_section + "\n\n" + "\n\n".join(texts)

    # Write the new content back to README.md
    with readme_path.open("w") as f:
        f.write(new_readme_content)

    print("Information added to README.md successfully.")
