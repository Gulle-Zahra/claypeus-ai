from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

REPLACEMENT = "[removed: suspicious instruction]"

Span = Union[Tuple[int, int], Dict[str, Any]]


def _as_interval(span: Span) -> Optional[Tuple[int, int]]:
    if isinstance(span, dict):
        start, end = span.get("start"), span.get("end")
    elif isinstance(span, (tuple, list)) and len(span) >= 2:
        start, end = span[0], span[1]
    else:
        return None
    try:
        start_i = int(start)
        end_i = int(end)
    except (TypeError, ValueError):
        return None
    if end_i <= start_i:
        return None
    return start_i, end_i


def merge_spans(spans: Iterable[Span], text_len: int) -> List[Tuple[int, int]]:
    """Clamp, drop invalid ranges, and merge overlapping or adjacent spans."""
    intervals: List[Tuple[int, int]] = []
    for span in spans or []:
        interval = _as_interval(span)
        if interval is None:
            continue
        start, end = interval
        start = max(0, min(start, text_len))
        end = max(0, min(end, text_len))
        if end > start:
            intervals.append((start, end))
    if not intervals:
        return []
    intervals.sort(key=lambda item: (item[0], item[1]))
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def apply_replacements(
    text: str,
    merged_spans: Sequence[Tuple[int, int]],
    replacement: str = REPLACEMENT,
) -> str:
    if not merged_spans:
        return text
    parts: List[str] = []
    cursor = 0
    for start, end in merged_spans:
        parts.append(text[cursor:start])
        parts.append(replacement)
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


class Sanitizer:
    """Replace flagged injection spans, merging overlaps and avoiding empty output."""

    def __init__(self, replacement: str = REPLACEMENT):
        self.replacement = replacement

    def sanitize(
        self,
        text: Any,
        spans: Optional[Sequence[Span]] = None,
    ) -> Dict[str, Any]:
        if text is None:
            original = ""
        elif isinstance(text, str):
            original = text
        else:
            original = str(text)

        if original == "":
            return {
                "text": original,
                "sanitized_text": "",
                "replaced_spans": [],
                "num_replacements": 0,
                "empty_input": True,
                "empty_result": True,
            }

        merged = merge_spans(spans or [], len(original))
        sanitized = apply_replacements(original, merged, self.replacement)

        if sanitized.strip() == "":
            sanitized = self.replacement

        return {
            "text": original,
            "sanitized_text": sanitized,
            "replaced_spans": [
                {"start": start, "end": end, "match": original[start:end]}
                for start, end in merged
            ],
            "num_replacements": len(merged),
            "empty_input": False,
            "empty_result": sanitized.strip() == "",
        }
