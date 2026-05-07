"""
Wrap lines of user code that match the reference in <mark> tags (HTML).
"""

from __future__ import annotations

import html
from difflib import SequenceMatcher


def highlight_matching_lines(user_code: str, reference_code: str) -> str:
    """
    Compare user code with reference; wrap lines that match (or closely match) reference lines.
    Returns HTML safe string with newlines preserved for display in <pre> or whitespace-pre.
    """
    if not user_code:
        return ""
    ref_lines = [ln.rstrip("\r") for ln in (reference_code or "").splitlines()]
    ref_set = set(ln for ln in ref_lines if ln.strip())
    user_lines = user_code.splitlines(keepends=True)
    out: list[str] = []
    for raw in user_lines:
        if raw.endswith("\n"):
            line = raw[:-1].rstrip("\r")
            ending = "\n"
        else:
            line = raw.rstrip("\r")
            ending = ""
        stripped = line.strip()
        if not stripped:
            out.append(html.escape(raw))
            continue
        matched = False
        if line in ref_set or stripped in ref_set:
            matched = True
        else:
            for ref in ref_lines:
                if not ref.strip():
                    continue
                ratio = SequenceMatcher(None, stripped, ref.strip()).ratio()
                if ratio >= 0.92:
                    matched = True
                    break
        esc = html.escape(line)
        if matched:
            out.append(
                f'<mark class="bg-yellow-300 px-1 rounded">{esc}</mark>{ending}'
            )
        else:
            out.append(f"{esc}{ending}")
    return "".join(out)
