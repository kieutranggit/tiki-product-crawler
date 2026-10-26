# check_api.py
# Call the Tiki API for ONE product before the long run of main.py (about 3 days).
# If this fails, there is no need to start main.py.
#
# Run from the project folder:   python check_api.py

from curl_cffi import requests

URL = "https://api.tiki.vn/product-detail/api/v1/products/"

# impersonate="chrome": look like the Chrome browser.
# With the normal "requests" library, Tiki answers 403 (forbidden).
r = requests.get(URL + "1391347", impersonate="chrome", timeout=30)
print("Status:", r.status_code)
print("Content-Type:", r.headers.get("content-type"))

# Real data = status 200 AND JSON.
# When Tiki blocks us, it also answers 200, but with an HTML page.
if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
    data = r.json()
    print("Number of fields:", len(data))

    # Look at the 6 fields we need
    print("id:", data["id"])
    print("name:", data["name"])
    print("url_key:", data["url_key"])
    print("price:", data["price"])
    print("description:", data["description"][:300])
    print("images[0]:", data["images"][0])
    print("RESULT: OK, the API works. You can run main.py")
else:
    print("RESULT: PROBLEM. Maybe blocked: wait a few minutes and try again.")
