# check_data.py
# Check the data BEFORE and AFTER the pipeline. It only reads files.
#
# Part 1 - input:  can the id list be used? (empty ids, duplicate ids)
# Part 2 - output: is every input id in the output exactly once?
#         (as a product in output/raw OR as an error in output/errors)
# Part 3 - clean:  are the clean files complete and really clean?
#
# Run from the project folder:   python check_data.py

import json
from pathlib import Path
import pandas as pd


def load(path):
    """Read one JSON file and return its content (a list of dicts)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------- Part 1: input ----------------
print("=== Part 1: input ===")
df = pd.read_excel("input/products-0-200000.xlsx")
print("Ids:", len(df))
print("Empty ids:", df["id"].isna().sum())
print("Duplicate ids:", len(df) - df["id"].nunique())


# ---------------- Part 2: output (raw + errors) ----------------
print()
print("=== Part 2: output ===")
raw_ids = []
error_ids = []
reasons = {}      # error reason -> how many times

for i in range(1, 201):
    for p in load(f"output/raw/products_{i:03d}.json"):
        raw_ids.append(p["id"])

    for e in load(f"output/errors/errors_{i:03d}.json"):
        error_ids.append(e["id"])
        if e["reason"] in reasons:
            reasons[e["reason"]] = reasons[e["reason"]] + 1
        else:
            reasons[e["reason"]] = 1

input_ids = set(df["id"])
output_ids = raw_ids + error_ids

print("Products:", len(raw_ids))
print("Errors:", len(error_ids))
print("Products + errors:", len(output_ids))
print("Error reasons:", reasons)
print("Duplicate ids:", len(output_ids) - len(set(output_ids)))
print("Missing ids (in input, not in output):", len(input_ids - set(output_ids)))
print("Extra ids (in output, not in input):", len(set(output_ids) - input_ids))

# A .tmp file left = a write was stopped in the middle (see save_json in main.py)
print("Leftover .tmp files:", len(list(Path("output").rglob("*.tmp"))))


# ---------------- Part 3: clean ----------------
print()
print("=== Part 3: clean ===")
clean_ids = []
count_tax = 0
count_empty = 0

for i in range(1, 201):
    for p in load(f"output/clean/products_{i:03d}.json"):
        clean_ids.append(p["id"])
        if "Giá sản phẩm trên Tiki" in p["description"]:
            count_tax = count_tax + 1
        if p["description"] == "":
            count_empty = count_empty + 1

print("Clean products:", len(clean_ids))
print("Same ids, same order as raw:", clean_ids == raw_ids)
print("Still has Tiki tax line:", count_tax)
print("Empty description after cleaning:", count_empty)
