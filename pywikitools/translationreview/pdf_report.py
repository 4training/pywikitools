import os
import re
from dataclasses import dataclass
from typing import Dict, List

from fpdf import FPDF

SECTION_REVIEW = "### Review"
SECTION_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)
BEST_UNIT_PATTERN = re.compile(
    r"^=== (.+?) ===\s*\n(.*?)(?=^=== |\Z)", re.MULTILINE | re.DOTALL
)


@dataclass
class UnitReport:
    identifier: str
    english: str
    reference: str
    current_translation: str
    review: str
    best_translation: str


@dataclass
class ReviewSection:
    english: str
    reference: str
    current_translation: str
    review: str


SECTION_ENGLISH = re.compile(r"### English\n\n(.*?)(?=\n### |\Z)", re.DOTALL)
SECTION_REFERENCE = re.compile(r"### [A-Z]+ reference\n\n(.*?)(?=\n### |\Z)", re.DOTALL)
SECTION_CURRENT_TRANSLATION = re.compile(
    r"### Current \w+ translation\n\n(.*?)(?=\n### |\Z)",
    re.DOTALL,
)


def slug_to_model_name(slug: str) -> str:
    """Turn a directory slug like openai-gpt-4o into openai/gpt-4o."""
    if "/" in slug:
        return slug
    provider, _, rest = slug.partition("-")
    if rest:
        return f"{provider}/{rest}"
    return slug


def parse_review_report(content: str) -> Dict[str, ReviewSection]:
    """Return a mapping of unit identifier to review section data."""
    sections: Dict[str, ReviewSection] = {}
    for section in re.split(r"(?=^## )", content, flags=re.MULTILINE):
        match = SECTION_PATTERN.search(section)
        if not match:
            continue
        identifier = match.group(1).strip()

        english = ""
        english_match = SECTION_ENGLISH.search(section)
        if english_match:
            english = english_match.group(1).strip()

        reference = ""
        reference_match = SECTION_REFERENCE.search(section)
        if reference_match:
            reference = reference_match.group(1).strip()

        current_translation = ""
        current_match = SECTION_CURRENT_TRANSLATION.search(section)
        if current_match:
            current_translation = current_match.group(1).strip()

        review = ""
        review_index = section.find(SECTION_REVIEW)
        if review_index != -1:
            review_text = section[review_index + len(SECTION_REVIEW) :].strip()
            review = re.sub(r"^#+\s.*$", "", review_text, flags=re.MULTILINE).strip()

        sections[identifier] = ReviewSection(
            english=english,
            reference=reference,
            current_translation=current_translation,
            review=review,
        )
    return sections


def parse_best_translations(content: str) -> Dict[str, str]:
    """Return a mapping of unit identifier to suggested translation."""
    return {
        match.group(1).strip(): match.group(2).strip()
        for match in BEST_UNIT_PATTERN.finditer(content)
    }


def load_unit_reports(output_dir: str) -> List[UnitReport]:
    review_path = os.path.join(output_dir, "review_report.md")
    best_path = os.path.join(output_dir, "best_translations.wiki")

    review_sections: Dict[str, ReviewSection] = {}
    if os.path.isfile(review_path):
        with open(review_path, encoding="utf-8") as handle:
            review_sections = parse_review_report(handle.read())
    with open(best_path, encoding="utf-8") as handle:
        best_translations = parse_best_translations(handle.read())

    identifiers = list(review_sections.keys())
    for identifier in best_translations:
        if identifier not in identifiers:
            identifiers.append(identifier)

    units: List[UnitReport] = []
    for identifier in identifiers:
        section = review_sections.get(identifier, ReviewSection("", "", "", ""))
        units.append(
            UnitReport(
                identifier=identifier,
                english=section.english,
                reference=section.reference,
                current_translation=section.current_translation,
                review=section.review,
                best_translation=best_translations.get(identifier, ""),
            )
        )
    return units


def _dejavu_font_path(filename: str) -> str:
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/{filename}",
        f"/usr/share/fonts/TTF/{filename}",
        f"/usr/share/fonts/dejavu/{filename}",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        f"Could not find {filename}. Install the DejaVu fonts package."
    )


def _markdown_to_plain(text: str) -> str:
    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    plain = re.sub(r"`(.+?)`", r"\1", plain)
    return plain.strip()


def _normalize_heading(heading: str) -> str:
    normalized = re.sub(r"^#+\s*", "", heading.strip())
    normalized = normalized.strip("*: ")
    normalized = re.sub(r"^\d+\.\s*", "", normalized)
    return normalized.lower()


def _is_meta_heading(heading: str) -> bool:
    normalized = _normalize_heading(heading)
    if not normalized:
        return False
    meta_keywords = (
        "conclusion",
        "alternative",
        "strength",
        "weakness",
        "overall assessment",
        "overall impression",
        "overall evaluation",
        "analysis summary",
        "discussion of",
        "sentence-by-sentence",
        "review of the",
        "comparison to",
        "comparison with",
        "final thought",
        "final assessment",
        "final recommendation",
        "evaluation of the existing",
        "evaluation of the",
        "possible alternative",
        "other possible alternative",
        "alternatives to consider",
        "points to consider",
        "recommendation",
        "summary",
    )
    return any(keyword in normalized for keyword in meta_keywords)


def strip_meta_sections(text: str) -> str:
    """Remove boilerplate review headings and their content from analysis text."""
    if not text or text == "TIMEOUT":
        return text

    parts = re.split(r"(?=^###\s+)", text, flags=re.MULTILINE)
    kept: List[str] = []

    for part in parts:
        chunk = part.strip()
        if not chunk:
            continue

        if chunk.startswith("###"):
            title_line = chunk.split("\n", 1)[0]
            if _is_meta_heading(title_line):
                continue
            body = chunk.split("\n", 1)[1] if "\n" in chunk else ""
            body = _strip_bold_meta_blocks(body)
            if body.strip():
                kept.append(body.strip())
            continue

        if chunk.lower().startswith("excellent. here is my analysis"):
            continue
        if chunk.lower().startswith("excellent. i will now proceed"):
            continue

        cleaned = _strip_bold_meta_blocks(chunk)
        if cleaned.strip():
            kept.append(cleaned.strip())

    result = "\n\n".join(kept)
    return re.sub(r"\n{3,}", "\n\n", result).strip()


def _strip_bold_meta_blocks(text: str) -> str:
    parts = re.split(r"(?=^\*\*[^*]+\*\*)", text, flags=re.MULTILINE)
    kept: List[str] = []

    for part in parts:
        chunk = part.strip()
        if not chunk:
            continue

        if chunk.startswith("**"):
            title_line = chunk.split("\n", 1)[0]
            if _is_meta_heading(title_line):
                continue
            body = chunk.split("\n", 1)[1] if "\n" in chunk else ""
            if body.strip():
                kept.append(body.strip())
            continue

        kept.append(chunk)

    return "\n\n".join(kept)


def _pdf_text(text: str, *, is_analysis: bool = False) -> str:
    plain = _markdown_to_plain(text)
    if is_analysis:
        plain = strip_meta_sections(plain)
    return plain


def _join_unit_texts(unit_ids: List[str], texts_by_unit: Dict[str, str]) -> str:
    parts = [_pdf_text(texts_by_unit.get(unit_id, "")) for unit_id in unit_ids]
    return "\n\n".join(part for part in parts if part)


class TranslationReviewPDF(FPDF):
    def __init__(self, *, title: str, subtitle: str):
        super().__init__()
        self._title = title
        self._subtitle = subtitle
        self._register_fonts()

    def _register_fonts(self) -> None:
        regular = _dejavu_font_path("DejaVuSans.ttf")
        bold = _dejavu_font_path("DejaVuSans-Bold.ttf")
        self.add_font("DejaVu", "", regular)
        self.add_font("DejaVu", "B", bold)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(90, 90, 90)
        self.cell(0, 8, self._title, align="L")
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def add_title_page(self) -> None:
        self.add_page()
        self.set_font("DejaVu", "B", 20)
        self.set_text_color(30, 60, 100)
        self.multi_cell(0, 12, self._title, align="C")
        self.ln(6)
        self.set_font("DejaVu", "", 12)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 8, self._subtitle, align="C")
        self.ln(20)

    def add_unit_section(
        self,
        unit: UnitReport,
        *,
        reference_language: str,
        language_code: str,
    ) -> None:
        self.add_unit_translation_comparison(
            unit,
            reference_language=reference_language,
            language_code=language_code,
        )

    def add_unit_translation_comparison(
        self,
        unit: UnitReport,
        *,
        reference_language: str,
        language_code: str,
    ) -> None:
        self.add_page()
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(30, 60, 100)
        self.multi_cell(0, 9, unit.identifier)
        self.ln(4)

        self._section_heading("English original")
        self._body_text(_pdf_text(unit.english) or "(no text)")

        self.ln(4)
        self._section_heading(f"{reference_language.upper()} reference translation")
        self._body_text(_pdf_text(unit.reference) or "(no text)")

        self.ln(4)
        self._section_heading(f"Suggested {language_code} translation")
        self._body_text(_pdf_text(unit.best_translation) or "(no translation)")

    def add_unit_review(
        self,
        unit: UnitReport,
        *,
        reference_language: str,
        language_code: str,
    ) -> None:
        self.add_page()
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(30, 60, 100)
        self.multi_cell(0, 9, unit.identifier)
        self.ln(4)

        self._section_heading("English original")
        self._body_text(_pdf_text(unit.english) or "(no text)")

        self.ln(4)
        self._section_heading(f"{reference_language.upper()} reference translation")
        self._body_text(_pdf_text(unit.reference) or "(no text)")

        self.ln(4)
        self._section_heading(f"Suggested {language_code} translation")
        self._body_text(_pdf_text(unit.best_translation) or "(no translation)")

        self.ln(4)
        self._section_heading("Review")
        review_text = _pdf_text(unit.review, is_analysis=True) or "(no review)"
        self._body_text(review_text)

    def add_complete_suggested_translation(
        self,
        *,
        unit_ids: List[str],
        best_by_unit: Dict[str, str],
    ) -> None:
        self.add_page()
        self.add_part_heading("Part 1: Complete suggested translation")
        self._body_text(_join_unit_texts(unit_ids, best_by_unit) or "(no translation)")

    def _section_heading(self, title: str) -> None:
        self.set_font("DejaVu", "B", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title)
        self.ln(7)
        self.set_draw_color(200, 210, 220)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

    def _body_text(self, text: str) -> None:
        self.set_font("DejaVu", "", 11)
        self.set_text_color(30, 30, 30)
        for paragraph in text.split("\n\n"):
            paragraph = paragraph.replace("\n", " ").strip()
            if not paragraph:
                continue
            if paragraph.startswith("- "):
                self._bullet_paragraph(paragraph)
            elif re.match(r"^\d+\.\s", paragraph):
                self._numbered_paragraph(paragraph)
            else:
                self.multi_cell(0, 6, paragraph)
                self.ln(2)

    def _bullet_paragraph(self, paragraph: str) -> None:
        items = re.split(r"\s*-\s+", paragraph)
        for item in items:
            item = item.strip()
            if not item:
                continue
            self.cell(5)
            self.multi_cell(0, 6, f"• {item}")
            self.ln(1)

    def _numbered_paragraph(self, paragraph: str) -> None:
        items = re.split(r"(?=\d+\.\s)", paragraph)
        for item in items:
            item = item.strip()
            if not item:
                continue
            self.multi_cell(0, 6, item)
            self.ln(1)

    def add_part_heading(self, title: str) -> None:
        self.ln(6)
        self.set_font("DejaVu", "B", 16)
        self.set_text_color(30, 60, 100)
        self.multi_cell(0, 10, title)
        self.ln(4)

    def add_subsection_heading(self, title: str) -> None:
        self.ln(3)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(70, 70, 70)
        self.multi_cell(0, 7, title)
        self.ln(2)


def build_pdf_report(
    *,
    model_name: str,
    page: str,
    language_code: str,
    reference_language: str,
    units: List[UnitReport],
    output_path: str,
    include_review: bool = True,
) -> None:
    page_title = page.replace("_", " ")
    subtitle = f"Translation review ({language_code}) — {page_title}"
    pdf = TranslationReviewPDF(title=model_name, subtitle=subtitle)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_title_page()

    unit_ids = [unit.identifier for unit in units]
    best_by_unit = {unit.identifier: unit.best_translation for unit in units}
    pdf.add_complete_suggested_translation(
        unit_ids=unit_ids,
        best_by_unit=best_by_unit,
    )

    pdf.add_page()
    pdf.add_part_heading("Part 2: Translation units")
    for unit in units:
        pdf.add_unit_translation_comparison(
            unit,
            reference_language=reference_language,
            language_code=language_code,
        )

    if include_review and any(unit.review for unit in units):
        pdf.add_page()
        pdf.add_part_heading("Part 3: Review")
        for unit in units:
            pdf.add_unit_review(
                unit,
                reference_language=reference_language,
                language_code=language_code,
            )

    pdf.output(output_path)
