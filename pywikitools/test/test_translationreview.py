import logging
import os
import tempfile
import unittest
from configparser import ConfigParser
from unittest.mock import MagicMock, patch

from pywikitools.lang.translated_page import TranslatedPage, TranslationUnit
from pywikitools.translationreview.bot import (
    TranslationReviewBot,
    should_review_unit,
)
from pywikitools.translationreview.openai_client import TIMEOUT_SENTINEL
from pywikitools.translationreview.prompts import (
    build_best_translation_prompt,
    build_review_prompt,
    language_name,
)


def make_config(temp_dir: str) -> ConfigParser:
    config = ConfigParser()
    config.read_dict(
        {
            "Paths": {"temp": temp_dir},
            "translationreview": {
                "site": "4training",
                "openai_api_key": "test-key",
                "model": "gpt-4o",
                "reference_language": "de",
                "request_delay": "0",
            },
        }
    )
    return config


class TestShouldReviewUnit(unittest.TestCase):
    def test_skips_empty_translation(self):
        unit = TranslationUnit("Prayer/1", "tr", "Hello", "")
        self.assertFalse(should_review_unit(unit))

    def test_skips_title(self):
        unit = TranslationUnit("Test/Page_display_title", "tr", "My Title", "Başlık")
        self.assertFalse(should_review_unit(unit))

    def test_skips_filename(self):
        unit = TranslationUnit("Test/1", "tr", "worksheet.odt", "worksheet.odt")
        self.assertFalse(should_review_unit(unit))

    def test_skips_version_number(self):
        unit = TranslationUnit("Test/1", "tr", "1.0", "1.0")
        self.assertFalse(should_review_unit(unit))

    def test_includes_normal_unit(self):
        unit = TranslationUnit(
            "Prayer/1", "tr", "Pray for others", "Başkaları için dua et"
        )
        self.assertTrue(should_review_unit(unit))


class TestPromptBuilding(unittest.TestCase):
    def test_review_prompt_contains_all_texts(self):
        prompt = build_review_prompt(
            language_code="tr",
            english="Pray for others",
            reference="Betet für andere",
            target="Başkaları için dua et",
        )
        self.assertIn("Turkish", prompt)
        self.assertIn("Pray for others", prompt)
        self.assertIn("Betet für andere", prompt)
        self.assertIn("Başkaları için dua et", prompt)
        self.assertIn("teyze", prompt)
        self.assertIn("do NOT provide a final improved translation", prompt)

    def test_best_translation_prompt_includes_review(self):
        prompt = build_best_translation_prompt(
            language_code="tr",
            english="Pray for others",
            reference="Betet für andere",
            target="Başkaları için dua et",
            review="The translation is good but could be more natural.",
        )
        self.assertIn("ONLY the best improved translation", prompt)
        self.assertIn("The translation is good but could be more natural.", prompt)

    def test_default_guidelines_for_unknown_language(self):
        prompt = build_review_prompt(
            language_code="xx",
            english="Hello",
            reference="Hallo",
            target="Hola",
        )
        self.assertIn("speaks to your heart", prompt)
        self.assertIn("Preserve all MediaWiki markup exactly", prompt)
        self.assertNotIn("teyze", prompt)

    def test_language_name_fallback(self):
        self.assertEqual(language_name("tr"), "Turkish")
        self.assertEqual(language_name("unknown"), "unknown")


class TestTranslationReviewBot(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = make_config(self.temp_dir)

        print_patcher = patch("pywikitools.translationreview.bot.print")
        print_patcher.start()
        self.addCleanup(print_patcher.stop)

        self._review_logger = logging.getLogger("pywikitools.translationreview")
        self._saved_propagate = self._review_logger.propagate
        self._saved_level = self._review_logger.level
        self._review_logger.propagate = False
        self._review_logger.setLevel(logging.CRITICAL)
        self.addCleanup(
            setattr, self._review_logger, "propagate", self._saved_propagate
        )
        self.addCleanup(setattr, self._review_logger, "level", self._saved_level)

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_model_from_config(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        TranslationReviewBot(self.config)
        mock_openai_cls.assert_called_once()
        self.assertEqual(mock_openai_cls.call_args.kwargs["model"], "gpt-4o")

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_model_cli_override(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        TranslationReviewBot(self.config, model="gpt-4.1")
        mock_openai_cls.assert_called_once()
        self.assertEqual(mock_openai_cls.call_args.kwargs["model"], "gpt-4.1")

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_missing_model_raises(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        config = make_config(self.temp_dir)
        config.remove_option("translationreview", "model")
        with self.assertRaisesRegex(RuntimeError, "Missing model"):
            TranslationReviewBot(config)
        mock_openai_cls.assert_not_called()

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_default_output_dir_includes_model_and_date(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        bot = TranslationReviewBot(self.config, model="openai/gpt-4o")
        out_dir = bot._default_output_dir("Forgiving_Step_by_Step", "tr")
        self.assertIn(
            "translation_review/Forgiving_Step_by_Step_tr_openai-gpt-4o_",
            out_dir,
        )
        date_part = out_dir.rstrip("/").rsplit("_", 1)[-1]
        self.assertRegex(date_part, r"^\d{4}-\d{2}-\d{2}$")

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_run_processes_units_with_two_api_calls(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        target_units = [
            TranslationUnit(
                "Prayer/1", "tr", "Pray for others", "Başkaları için dua et"
            ),
            TranslationUnit("Prayer/2", "tr", "Trust God", "Tanrı'ya güven"),
        ]
        reference_units = [
            TranslationUnit("Prayer/1", "de", "Pray for others", "Betet für andere"),
            TranslationUnit("Prayer/2", "de", "Trust God", "Vertraut Gott"),
        ]

        mock_lib = MagicMock()
        mock_fortraininglib_cls.return_value = mock_lib
        mock_lib.get_translation_units.side_effect = [
            TranslatedPage("Test", "tr", target_units),
            TranslatedPage("Test", "de", reference_units),
        ]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.complete.side_effect = [
            "Review for unit 1",
            "Improved translation 1",
            "Review for unit 2",
            "Improved translation 2",
        ]

        bot = TranslationReviewBot(self.config)
        summary = bot.run("Test", "tr", output_dir=self.temp_dir)

        self.assertEqual(summary.processed, 2)
        self.assertEqual(summary.skipped, 0)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(mock_client.complete.call_count, 4)

        review_path = os.path.join(self.temp_dir, "review_report.md")
        best_path = os.path.join(self.temp_dir, "best_translations.wiki")
        summary_path = os.path.join(self.temp_dir, "summary.txt")

        with open(review_path, encoding="utf-8") as handle:
            review_content = handle.read()
        with open(best_path, encoding="utf-8") as handle:
            best_content = handle.read()
        with open(summary_path, encoding="utf-8") as handle:
            summary_content = handle.read()

        self.assertIn("## Prayer/1", review_content)
        self.assertIn("Review for unit 1", review_content)
        self.assertIn("=== Prayer/1 ===", best_content)
        self.assertIn("Improved translation 1", best_content)
        self.assertIn("Processed: 2", summary_content)

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_run_logs_analysis_and_best_translation(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        target_units = [
            TranslationUnit(
                "Prayer/1", "tr", "Pray for others", "Başkaları için dua et"
            ),
        ]
        reference_units = [
            TranslationUnit("Prayer/1", "de", "Pray for others", "Betet für andere"),
        ]

        mock_lib = MagicMock()
        mock_fortraininglib_cls.return_value = mock_lib
        mock_lib.get_translation_units.side_effect = [
            TranslatedPage("Test", "tr", target_units),
            TranslatedPage("Test", "de", reference_units),
        ]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.complete.side_effect = [
            "Review for unit 1",
            "Improved translation 1",
        ]

        bot = TranslationReviewBot(self.config)
        with self.assertLogs(
            "pywikitools.translationreview", level=logging.INFO
        ) as log_context:
            bot.run("Test", "tr", output_dir=self.temp_dir)

        messages = [record.getMessage() for record in log_context.records]
        info_messages = [
            message
            for record, message in zip(log_context.records, messages)
            if record.levelno == logging.INFO
        ]
        warning_messages = [
            message
            for record, message in zip(log_context.records, messages)
            if record.levelno == logging.WARNING
        ]

        self.assertTrue(
            any("Review for unit 1" in message for message in info_messages)
        )
        self.assertTrue(
            any("Improved translation 1" in message for message in warning_messages)
        )

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_skips_units_without_reference(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        target_units = [
            TranslationUnit(
                "Prayer/1", "tr", "Pray for others", "Başkaları için dua et"
            ),
            TranslationUnit("Prayer/2", "tr", "Trust God", "Tanrı'ya güven"),
        ]
        reference_units = [
            TranslationUnit("Prayer/1", "de", "Pray for others", "Betet für andere"),
        ]

        mock_lib = MagicMock()
        mock_fortraininglib_cls.return_value = mock_lib
        mock_lib.get_translation_units.side_effect = [
            TranslatedPage("Test", "tr", target_units),
            TranslatedPage("Test", "de", reference_units),
        ]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.complete.side_effect = [
            "Review for unit 1",
            "Improved translation 1",
        ]

        bot = TranslationReviewBot(self.config)
        summary = bot.run("Test", "tr", output_dir=self.temp_dir)

        self.assertEqual(summary.processed, 1)
        self.assertEqual(summary.skipped, 1)
        self.assertIn("Prayer/2", summary.skipped_units)
        self.assertEqual(mock_client.complete.call_count, 2)

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_limit_and_unit_filter(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        target_units = [
            TranslationUnit(
                "Prayer/1", "tr", "Pray for others", "Başkaları için dua et"
            ),
            TranslationUnit("Prayer/2", "tr", "Trust God", "Tanrı'ya güven"),
        ]
        reference_units = [
            TranslationUnit("Prayer/1", "de", "Pray for others", "Betet für andere"),
            TranslationUnit("Prayer/2", "de", "Trust God", "Vertraut Gott"),
        ]

        mock_lib = MagicMock()
        mock_fortraininglib_cls.return_value = mock_lib
        mock_lib.get_translation_units.side_effect = [
            TranslatedPage("Test", "tr", target_units),
            TranslatedPage("Test", "de", reference_units),
        ]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.complete.side_effect = ["Review", "Best"]

        bot = TranslationReviewBot(self.config)
        summary = bot.run("Test", "tr", unit_id="Prayer/2", output_dir=self.temp_dir)

        self.assertEqual(summary.processed, 1)
        self.assertEqual(mock_client.complete.call_count, 2)

        with open(
            os.path.join(self.temp_dir, "best_translations.wiki"), encoding="utf-8"
        ) as handle:
            content = handle.read()
            self.assertIn("=== Prayer/2 ===", content)
            self.assertNotIn("=== Prayer/1 ===", content)

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_run_marks_timeout_as_failed_and_writes_reports(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        target_units = [
            TranslationUnit(
                "Prayer/1", "tr", "Pray for others", "Başkaları için dua et"
            ),
        ]
        reference_units = [
            TranslationUnit("Prayer/1", "de", "Pray for others", "Betet für andere"),
        ]

        mock_lib = MagicMock()
        mock_fortraininglib_cls.return_value = mock_lib
        mock_lib.get_translation_units.side_effect = [
            TranslatedPage("Test", "tr", target_units),
            TranslatedPage("Test", "de", reference_units),
        ]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.complete.return_value = TIMEOUT_SENTINEL

        bot = TranslationReviewBot(self.config)
        summary = bot.run("Test", "tr", output_dir=self.temp_dir)

        self.assertEqual(summary.processed, 0)
        self.assertEqual(summary.failed, 1)
        self.assertEqual(summary.failed_units, ["Prayer/1"])
        mock_client.complete.assert_called_once()

        with open(
            os.path.join(self.temp_dir, "review_report.md"), encoding="utf-8"
        ) as handle:
            review_content = handle.read()
        with open(
            os.path.join(self.temp_dir, "best_translations.wiki"), encoding="utf-8"
        ) as handle:
            best_content = handle.read()

        self.assertIn("TIMEOUT", review_content)
        self.assertIn("=== Prayer/1 ===", best_content)
        self.assertIn("TIMEOUT", best_content)

    @patch("pywikitools.translationreview.bot.OpenAIClient")
    @patch("pywikitools.translationreview.bot.ForTrainingLib")
    @patch("pywikitools.translationreview.bot.Family")
    def test_run_marks_partial_timeout_as_failed(
        self, mock_family, mock_fortraininglib_cls, mock_openai_cls
    ):
        target_units = [
            TranslationUnit(
                "Prayer/1", "tr", "Pray for others", "Başkaları için dua et"
            ),
        ]
        reference_units = [
            TranslationUnit("Prayer/1", "de", "Pray for others", "Betet für andere"),
        ]

        mock_lib = MagicMock()
        mock_fortraininglib_cls.return_value = mock_lib
        mock_lib.get_translation_units.side_effect = [
            TranslatedPage("Test", "tr", target_units),
            TranslatedPage("Test", "de", reference_units),
        ]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.complete.side_effect = ["Review for unit 1", TIMEOUT_SENTINEL]

        bot = TranslationReviewBot(self.config)
        summary = bot.run("Test", "tr", output_dir=self.temp_dir)

        self.assertEqual(summary.processed, 0)
        self.assertEqual(summary.failed, 1)
        self.assertEqual(mock_client.complete.call_count, 2)


class TestOpenAIClient(unittest.TestCase):
    @patch("pywikitools.translationreview.openai_client.time.sleep")
    @patch("pywikitools.translationreview.openai_client.OpenAI")
    def test_complete_returns_stripped_content(self, mock_openai_cls, mock_sleep):
        from pywikitools.translationreview.openai_client import OpenAIClient

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  Review text  "
        mock_openai_cls.return_value.chat.completions.create.return_value = (
            mock_response
        )

        client = OpenAIClient(api_key="test", model="gpt-4o", request_delay=0)
        result = client.complete("prompt")

        self.assertEqual(result, "Review text")
        mock_openai_cls.return_value.chat.completions.create.assert_called_once()
        self.assertEqual(
            mock_openai_cls.call_args.kwargs["timeout"],
            60.0,
        )
        self.assertEqual(
            mock_openai_cls.return_value.chat.completions.create.call_args.kwargs[
                "timeout"
            ],
            60.0,
        )

    @patch("pywikitools.translationreview.openai_client.time.sleep")
    @patch("pywikitools.translationreview.openai_client.OpenAI")
    def test_complete_returns_timeout_after_retries(self, mock_openai_cls, mock_sleep):
        from openai import APITimeoutError

        from pywikitools.translationreview.openai_client import OpenAIClient

        mock_openai_cls.return_value.chat.completions.create.side_effect = (
            APITimeoutError("timed out")
        )

        client = OpenAIClient(api_key="test", model="gpt-4o", request_delay=0)
        result = client.complete("prompt")

        self.assertEqual(result, TIMEOUT_SENTINEL)
        self.assertEqual(
            mock_openai_cls.return_value.chat.completions.create.call_count, 3
        )
