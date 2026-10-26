# main.py
# Download 200,000 products from the Tiki API (EXTRACT step of the pipeline).
#
#   input/products-0-200000.xlsx -> Tiki API -> output/raw/products_NNN.json
#                                               output/errors/errors_NNN.json
#
# Run from the project folder:   python main.py
#
# CHECKPOINT: the ids are split into chunks of 1000 (200 files).
# A chunk is finished when its products file exists. When the script starts,
# it skips every finished chunk. So if the script stops (Ctrl+C, power cut,
# lost internet), just run it again: it continues from the first unfinished chunk.

import json, time
from pathlib import Path
import pandas as pd
from curl_cffi import requests

API = "https://api.tiki.vn/product-detail/api/v1/products/{}"
CHUNK = 1000          # 1000 ids per file
SLEEP = 1             # rest 1 second between 2 requests (no rest = blocked after ~10 requests)

INPUT = Path("input/products-0-200000.xlsx")
OUT = Path("output/raw")
ERR = Path("output/errors")
LOG = Path("output/crawl.log")
OUT.mkdir(parents=True, exist_ok=True)
ERR.mkdir(parents=True, exist_ok=True)


def log(message):
    """Print a message AND add it to output/crawl.log with the time,
    so after a 3 day run we can read what happened."""
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " | " + message
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def extract(p):
    """From the 59 fields of the API answer, keep the 6 needed fields."""
    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "url_key": p.get("url_key"),
        "price": p.get("price"),
        "description": p.get("description"),  # keep the original HTML, cleaned later
        "images_url": [img.get("base_url") for img in (p.get("images") or [])],
    }


def fetch(session, pid, max_tries=5):
    """Return (product, None) if successful, or (None, error_reason).

    - 404             -> product does not exist: no retry
    - 200 + JSON      -> success
    - 200 + HTML      -> Tiki is blocking us: wait and retry
    - other / timeout -> wait and retry
    The wait gets longer each time: 30s, 60s, 90s...
    """
    reason = "unknown"
    for attempt in range(1, max_tries + 1):
        try:
            r = session.get(API.format(pid), timeout=30)
            if r.status_code == 404:
                return None, "404 not found"          # product does not exist
            ctype = r.headers.get("content-type", "")
            if r.status_code == 200 and "json" in ctype:
                return extract(r.json()), None         # success
            reason = f"http {r.status_code}, {ctype[:30]}"   # e.g. 200 + text/html = blocked
        except Exception as e:
            reason = f"exception: {type(e).__name__}"        # timeout, lost internet...
        log(f"  id {pid} try {attempt}: {reason} -> wait {30 * attempt}s")
        time.sleep(30 * attempt)               # wait longer each time
    return None, reason                         # still failing after all tries


def save_json(path, obj):
    """Write to a .tmp file first, then rename it.
    If the computer stops while writing, the real file is never half written."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)   # rename happens completely or not at all


def main():
    ids = pd.read_excel(INPUT)["id"].tolist()
    session = requests.Session(impersonate="chrome")   # look like Chrome (TLS fingerprint)
    n_chunks = (len(ids) + CHUNK - 1) // CHUNK          # 200 parts

    for i in range(n_chunks):
        out_file = OUT / f"products_{i+1:03d}.json"
        err_file = ERR / f"errors_{i+1:03d}.json"
        if out_file.exists():                  # CHECKPOINT: chunk already done -> skip
            continue

        products, errors = [], []
        start = time.time()
        for pid in ids[i * CHUNK:(i + 1) * CHUNK]:
            data, err = fetch(session, pid)
            if data is not None:
                products.append(data)
            else:
                errors.append({"id": pid, "reason": err})
            time.sleep(SLEEP)

        # Errors file first, products file last:
        # the products file exists = this chunk is completely finished
        save_json(err_file, errors)
        save_json(out_file, products)
        log(f"Chunk {i+1}/{n_chunks}: {len(products)} ok, {len(errors)} errors, "
            f"{(time.time() - start) / 60:.1f} min")


if __name__ == "__main__":
    main()