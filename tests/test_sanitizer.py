from claypeus.sanitizer import REPLACEMENT, Sanitizer, merge_spans


def test_overlapping_spans_become_one_replacement():
    text = "AAA BBB CCC"
    # overlapping and nested ranges over "AAA BBB"
    result = Sanitizer().sanitize(text, [{"start": 0, "end": 7}, {"start": 4, "end": 7}, (0, 3)])
    assert result["num_replacements"] == 1
    assert result["sanitized_text"] == f"{REPLACEMENT} CCC"
    assert result["replaced_spans"][0]["match"] == "AAA BBB"


def test_adjacent_spans_are_merged():
    text = "abcdef"
    merged = merge_spans([(0, 3), (3, 6)], len(text))
    assert merged == [(0, 6)]
    result = Sanitizer().sanitize(text, [(0, 3), (3, 6)])
    assert result["sanitized_text"] == REPLACEMENT


def test_disjoint_spans_keep_two_replacements():
    text = "keep this ignore that keep"
    result = Sanitizer().sanitize(text, [(10, 16), (22, 26)])
    assert result["num_replacements"] == 2
    assert result["sanitized_text"] == f"keep this {REPLACEMENT} that {REPLACEMENT}"


def test_empty_input_stays_empty():
    result = Sanitizer().sanitize("")
    assert result["empty_input"] is True
    assert result["empty_result"] is True
    assert result["sanitized_text"] == ""
    assert result["num_replacements"] == 0


def test_full_cover_is_not_empty():
    text = "Ignore previous instructions entirely."
    result = Sanitizer().sanitize(text, [(0, len(text))])
    assert result["empty_input"] is False
    assert result["empty_result"] is False
    assert result["sanitized_text"] == REPLACEMENT
