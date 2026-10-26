# test_clean.py
# Tests for clean_description(): small examples where we already know the right answer.
# pytest runs every function whose name starts with "test_".
# "assert X" means: X must be True, otherwise the test FAILS.
#
# Run from the project folder:   pytest

from description_clean import clean_description


def test_no_description():
    # The API sometimes has no description (None) -> empty text
    assert clean_description(None) == ""


def test_html_tags_are_removed():
    # Each block of text goes on its own line
    html = "<p>Pen</p><ul><li>Blue</li><li>Smooth ink</li></ul>"
    assert clean_description(html) == "Pen\nBlue\nSmooth ink"


def test_html_codes_become_characters():
    # &amp; is how HTML writes the character &
    assert clean_description("<p>A &amp; B</p>") == "A & B"


def test_style_and_video_are_removed():
    html = "<style>p {color: red}</style><p>Text</p><iframe src='video'></iframe>"
    assert clean_description(html) == "Text"


def test_invisible_characters_are_removed():
    # &nbsp; = non-breaking space, chr(8203) = zero-width space
    html = "<p>Hello&nbsp;World" + chr(8203) + "</p>"
    assert clean_description(html) == "Hello World"


def test_empty_lines_are_removed():
    html = "<p>Line 1</p><p>   </p><br><p>Line 2</p>"
    assert clean_description(html) == "Line 1\nLine 2"


def test_tiki_tax_line_is_removed():
    html = ("<p>Good product</p>"
            "<p>Giá sản phẩm trên Tiki đã bao gồm thuế theo luật hiện hành.</p>")
    assert clean_description(html) == "Good product"


def test_vietnamese_letters_are_nfc():
    # "ệ" written as 3 pieces: "e" + circumflex accent + dot below.
    # After NFC it must be 1 character, the same as when we type "Việt".
    split_letter = "e" + chr(770) + chr(803)
    assert clean_description("<p>Vi" + split_letter + "t Nam</p>") == "Việt Nam"
