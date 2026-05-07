from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Iterable
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

_PALETTE = {
    "green": "#16a34a",
    "yellow": "#eab308",
    "red": "#dc2626",
    "dark_red": "#7f1d1d",
}


def _score_to_color(score: float) -> str:
    if score <= 30:
        return _PALETTE["green"]
    if score <= 60:
        return _PALETTE["yellow"]
    if score <= 80:
        return _PALETTE["red"]
    return _PALETTE["dark_red"]


def _split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [p.strip() for p in parts if p.strip()]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def _coerce_score(value: Any) -> float:
    try:
        score = float(value)
    except Exception:
        return 0.0
    if 0 <= score <= 1:
        return round(score * 100, 1)
    return round(score, 1)


def _label_to_score(label: str) -> float:
    l = (label or "").lower().strip()
    if l == "ai":
        return 75.0
    if l == "mixed":
        return 45.0
    if l == "human":
        return 15.0
    return 0.0


def _build_sentence_scores(text: str, similarity_results: Iterable[Any]) -> list[tuple[str, float]]:
    sentences = _split_sentences(text)
    results = list(similarity_results or [])

    parsed: list[tuple[str, float]] = []
    for item in results:
        if isinstance(item, dict):
            sentence = str(item.get("sentence") or item.get("text") or "").strip()
            score = item.get("similarity")
            if score is None:
                score = item.get("score")
            if score is None:
                score = _label_to_score(str(item.get("label") or ""))
            if sentence:
                parsed.append((sentence, _coerce_score(score)))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            sentence = str(item[0] or "").strip()
            if sentence:
                parsed.append((sentence, _coerce_score(item[1])))

    if parsed:
        return parsed

    return [(s, 0.0) for s in sentences]


def generate_report_pdf(payload: dict[str, Any]) -> bytes:
    input_text = str(payload.get("input_text") or "")
    similarity_results = payload.get("similarity_results") or []

    ai_label = str(payload.get("ai_label") or "Unknown")
    ai_probability = _coerce_score(payload.get("ai_probability"))
    final_score = _coerce_score(payload.get("final_score"))

    top_sources = payload.get("top_sources") or []
    sources = []
    for src in top_sources:
        if isinstance(src, dict):
            url = str(src.get("url") or "").strip()
            score = _coerce_score(src.get("score"))
            if url:
                sources.append({"url": url, "score": score})
    sources.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    sources = sources[:3]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
        title="Plagiarism & AI Detection Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        spaceAfter=4,
    )
    sentence_style = ParagraphStyle(
        "Sentence",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        spaceAfter=3,
    )

    story: list[Any] = []
    story.append(Paragraph("Plagiarism & AI Detection Report", title_style))
    story.append(Paragraph(f"We predict this text is: <b>{escape(ai_label)}</b>", body_style))
    story.append(Paragraph(f"AI Probability: <b>{ai_probability:.1f}%</b>", body_style))
    score_color = _score_to_color(final_score)
    story.append(
        Paragraph(
            f'Plagiarism Score: <font color="{score_color}"><b>{final_score:.1f}%</b></font>',
            body_style,
        )
    )
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("User Input Summary", section_style))
    story.append(Paragraph(f"Input length: <b>{len(input_text)}</b> characters", body_style))
    story.append(Paragraph(f"Words count: <b>{_word_count(input_text)}</b>", body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Color-Coded Text", section_style))
    sentence_scores = _build_sentence_scores(input_text, similarity_results)
    if sentence_scores:
        for sentence, score in sentence_scores:
            color = _score_to_color(score)
            decorated = escape(sentence)
            if score > 80:
                decorated = f"<u>{decorated}</u>"
            if score > 60:
                decorated = f"<b>{decorated}</b>"
            decorated = f'<font color="{color}">{decorated}</font>'
            story.append(Paragraph(decorated, sentence_style))
    else:
        story.append(Paragraph("No input text available for sentence highlighting.", body_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Matched Sources (Top 3)", section_style))
    if sources:
        for src in sources:
            color = _score_to_color(float(src.get("score", 0.0)))
            url = escape(src.get("url", ""))
            score = float(src.get("score", 0.0))
            line = f'<font color="{color}">{url} ({score:.1f}%)</font>'
            story.append(Paragraph(line, body_style))
    else:
        story.append(Paragraph("No sources available.", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _line_score_map(lines: list[str], similarity_results: Iterable[Any]) -> list[float]:
    results = list(similarity_results or [])
    if not lines:
        return []
    scores = [0.0 for _ in lines]
    if not results:
        return scores

    if len(results) == len(lines):
        for i, item in enumerate(results):
            if isinstance(item, dict):
                score = item.get("similarity")
                if score is None:
                    score = item.get("score")
                scores[i] = _coerce_score(score)
            elif isinstance(item, (int, float)):
                scores[i] = _coerce_score(item)
        return scores

    for item in results:
        if isinstance(item, dict):
            idx = item.get("line_number")
            if idx is None:
                idx = item.get("line")
            if idx is None:
                idx = item.get("index")
            try:
                i = int(idx) - 1
            except Exception:
                continue
            if 0 <= i < len(scores):
                score = item.get("similarity")
                if score is None:
                    score = item.get("score")
                scores[i] = _coerce_score(score)
    return scores


def generate_code_report(payload: dict[str, Any]) -> bytes:
    input_content = str(payload.get("input_content") or "")
    similarity_results = payload.get("similarity_results") or []
    final_score = _coerce_score(payload.get("final_score"))

    top_sources = payload.get("top_sources") or []
    sources = []
    for src in top_sources:
        if isinstance(src, dict):
            url = str(src.get("url") or "").strip()
            score = _coerce_score(src.get("score"))
            if url:
                sources.append({"url": url, "score": score})
    sources.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    sources = sources[:3]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
        title="Code Plagiarism Detection Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CodeTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "CodeSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "CodeBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "CodeLine",
        parent=styles["BodyText"],
        fontName="Courier",
        fontSize=9.5,
        leading=12,
        spaceAfter=2,
    )

    story: list[Any] = []
    story.append(Paragraph("Code Plagiarism Detection Report", title_style))
    score_color = _score_to_color(final_score)
    story.append(
        Paragraph(
            f'Plagiarism Score: <font color="{score_color}"><b>{final_score:.1f}%</b></font>',
            body_style,
        )
    )
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Code Listing", section_style))

    def get_color(score: float) -> str:
        if score <= 30:
            return "#16a34a"
        if score <= 60:
            return "#eab308"
        if score <= 80:
            return "#dc2626"
        return "#7f1d1d"

    lines = (input_content or "").splitlines()
    if lines:
        for i, line in enumerate(lines):
            if i < len(similarity_results) and isinstance(similarity_results[i], dict) and "score" in similarity_results[i]:
                score = similarity_results[i]["score"]
            else:
                score = final_score
            score = _coerce_score(score)
            color = get_color(score)
            safe_line = line.replace("<", "&lt;").replace(">", "&gt;")
            if score > 80:
                styled_line = f'<font color="{color}"><b>{safe_line}</b></font>'
            else:
                styled_line = f'<font color="{color}">{safe_line}</font>'
            story.append(Paragraph(styled_line, code_style))
    else:
        story.append(Paragraph("No code content provided.", body_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Matched Sources (Top 3)", section_style))
    if sources:
        for src in sources:
            score = float(src.get("score", 0.0))
            color = get_color(score)
            url = escape(src.get("url", ""))
            line = f'<font color="{color}">{url} ({score:.1f}%)</font>'
            story.append(Paragraph(line, body_style))
    else:
        story.append(Paragraph("No sources available.", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
