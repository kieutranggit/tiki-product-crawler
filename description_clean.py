# clean_description.py
# Normalize the description of every product (TRANSFORM + LOAD steps).
#
# output/raw/products_NNN.json -> clean_description() -> output/clean/products_NNN.json
#
# Run from the project folder (after main.py):   python clean_description.py
#
# The raw files are not changed. If a cleaning rule changes, we run this
# script again (about 1.5 minutes) instead of downloading again (3 days).

import json
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup


def clean_description(html):
    # 1. No description -> return an empty string
    if html is None:
        return ""

    # 2. Parse the HTML (this also turns &amp; into &)
    soup = BeautifulSoup(html, "html.parser")

    # 3. Remove non-text tags completely: CSS and videos
    for tag in soup.find_all(["style", "iframe"]):
        tag.decompose()

    # 4. Extract the text, one piece of text per line
    text = soup.get_text("\n")

    # 5. Replace special characters (non-breaking space, zero-width space, BOM, carriage return)
    text = text.replace("\xa0", " ")
    text = text.replace(chr(8203), "")
    text = text.replace(chr(65279), "")
    text = text.replace("\r", "")

    # 6. Normalize Vietnamese characters to one Unicode form (NFC)
    text = unicodedata.normalize("NFC", text)

    # 7. Check each line: skip empty lines and the Tiki tax line
    result = []
    for line in text.split("\n"):
        line = line.strip()
        if line == "":
            continue
        if "Giá sản phẩm trên Tiki" in line:
            continue
        result.append(line)

    return "\n".join(result)


def main():
    Path("output/clean").mkdir(exist_ok=True)

    for i in range(1, 201):
        name = f"products_{i:03d}.json"

        # read the raw file
        products = json.load(open("output/raw/" + name, encoding="utf-8"))

        # clean the description of every product
        for p in products:
            p["description"] = clean_description(p["description"])

        # write to the clean folder (same file name)
        with open("output/clean/" + name, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False)

        print("Done", name)


# This line lets test_clean.py import clean_description()
# without running main() (without cleaning all 200 files).
if __name__ == "__main__":
    main()
