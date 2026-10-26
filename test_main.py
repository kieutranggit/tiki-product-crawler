# test_main.py
# Tests for main.py. They do NOT call the real Tiki API:
# a fake session gives a prepared answer, so the tests are fast
# and always give the same result (even without internet).
#
# Run from the project folder:   pytest

from main import extract, fetch


# ---------------- Fake API ----------------

class FakeResponse:
    """Looks like an answer from curl_cffi: status_code, headers and json()."""

    def __init__(self, status_code, content_type, data):
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        self.data = data

    def json(self):
        return self.data


class FakeSession:
    """Looks like a curl_cffi session: get() always returns the prepared answer.
    It also counts how many times get() was called."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def get(self, url, timeout):
        self.calls = self.calls + 1
        return self.answer


# A small product like the real API answer (the real one has 59 fields)
PRODUCT = {
    "id": 123,
    "name": "Pen",
    "url_key": "pen-p123",
    "price": 5000,
    "description": "<p>Nice pen</p>",
    "images": [{"base_url": "https://img/1.jpg"}, {"base_url": "https://img/2.jpg"}],
    "rating_average": 4.5,   # a field we do NOT keep
}


# ---------------- extract() ----------------

def test_extract_keeps_6_fields():
    result = extract(PRODUCT)
    assert list(result.keys()) == ["id", "name", "url_key", "price", "description", "images_url"]
    assert result["images_url"] == ["https://img/1.jpg", "https://img/2.jpg"]


def test_extract_product_without_images():
    result = extract({"id": 1, "images": None})
    assert result["images_url"] == []
    assert result["name"] is None   # missing field -> None, no crash


# ---------------- fetch() ----------------

def test_fetch_success():
    session = FakeSession(FakeResponse(200, "application/json", PRODUCT))
    product, reason = fetch(session, 123)
    assert product["id"] == 123
    assert reason is None


def test_fetch_404_is_not_retried():
    session = FakeSession(FakeResponse(404, "application/json", None))
    product, reason = fetch(session, 123)
    assert product is None
    assert reason == "404 not found"
    assert session.calls == 1   # only 1 call: retrying a 404 is useless