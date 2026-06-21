import os
import tempfile
import unittest

from pywikitools.translationreview.pdf_report import (
    load_unit_reports,
    parse_best_translations,
    parse_review_report,
    slug_to_model_name,
    strip_meta_sections,
)


SAMPLE_REVIEW = """# Translation review: Test (tr)

Reference language: de

## Prayer/1

### English

Pray for others

### DE reference

Betet für andere

### Current tr translation

Başkaları için dua et

### Review

**Evaluation:**

The translation is understandable but could be warmer.

## Prayer/2

### English

Trust God

### DE reference

Vertraut Gott

### Current tr translation

Tanrı'ya güven

### Review

Good and natural.
"""

SAMPLE_BEST = """=== Prayer/1 ===
Başkaları için dua edin

=== Prayer/2 ===
Tanrı'ya güvenin
"""


class TestPdfReportParsing(unittest.TestCase):
    def test_slug_to_model_name(self):
        self.assertEqual(slug_to_model_name("openai-gpt-4o"), "openai/gpt-4o")
        self.assertEqual(
            slug_to_model_name("anthropic-claude-sonnet-4"),
            "anthropic/claude-sonnet-4",
        )

    def test_parse_review_report(self):
        sections = parse_review_report(SAMPLE_REVIEW)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections["Prayer/1"].english, "Pray for others")
        self.assertEqual(sections["Prayer/1"].reference, "Betet für andere")
        self.assertEqual(
            sections["Prayer/1"].current_translation, "Başkaları için dua et"
        )
        self.assertIn("understandable", sections["Prayer/1"].review)
        self.assertEqual(sections["Prayer/2"].review, "Good and natural.")

    def test_strip_meta_sections(self):
        review = """Excellent. Here is my analysis.

### Overall Assessment
This is mostly fine.

### Sentence-by-Sentence Analysis and Alternatives
**1. First sentence**
The opening is natural.

### Conclusions
It works well.

### Alternatives to consider
Try another wording.
"""
        cleaned = strip_meta_sections(review)
        self.assertNotIn("Overall Assessment", cleaned)
        self.assertNotIn("Conclusions", cleaned)
        self.assertNotIn("Alternatives", cleaned)
        self.assertNotIn("The opening is natural.", cleaned)
        self.assertEqual(cleaned, "")

    def test_parse_best_translations(self):
        best = parse_best_translations(SAMPLE_BEST)
        self.assertEqual(best["Prayer/1"], "Başkaları için dua edin")
        self.assertEqual(best["Prayer/2"], "Tanrı'ya güvenin")

    def test_load_unit_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(
                os.path.join(temp_dir, "review_report.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write(SAMPLE_REVIEW)
            with open(
                os.path.join(temp_dir, "best_translations.wiki"), "w", encoding="utf-8"
            ) as handle:
                handle.write(SAMPLE_BEST)

            units = load_unit_reports(temp_dir)
            self.assertEqual(len(units), 2)
            self.assertEqual(units[0].identifier, "Prayer/1")
            self.assertEqual(units[0].english, "Pray for others")
            self.assertEqual(units[0].reference, "Betet für andere")
            self.assertEqual(units[0].current_translation, "Başkaları için dua et")
            self.assertIn("understandable", units[0].review)
            self.assertEqual(units[0].best_translation, "Başkaları için dua edin")

    def test_load_unit_reports_without_review_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(
                os.path.join(temp_dir, "best_translations.wiki"), "w", encoding="utf-8"
            ) as handle:
                handle.write(SAMPLE_BEST)

            units = load_unit_reports(temp_dir)
            self.assertEqual(len(units), 2)
            self.assertEqual(units[0].best_translation, "Başkaları için dua edin")
            self.assertEqual(units[0].review, "")


if __name__ == "__main__":
    unittest.main()
