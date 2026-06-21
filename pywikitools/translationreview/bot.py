from dataclasses import dataclass, field
from configparser import ConfigParser
from datetime import datetime, timezone
import logging
import os
import re
from typing import Dict, List, Optional, Set

from pywikitools.family import Family
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.lang.translated_page import TranslationUnit
from pywikitools.translationreview.openai_client import (
    DEFAULT_TIMEOUT_SECONDS,
    TIMEOUT_SENTINEL,
    OpenAIClient,
)
from pywikitools.translationreview.prompts import (
    build_review_prompt,
    build_translate_prompt,
)


@dataclass
class UnitReviewResult:
    identifier: str
    english: str
    reference: str
    target: str
    review: str
    best_translation: str


@dataclass
class ReviewRunSummary:
    page: str
    language_code: str
    reference_language: str
    processed: int
    skipped: int
    failed: int
    output_dir: str
    skipped_units: List[str]
    failed_units: List[str]
    with_review: bool = False
    run_options: Dict[str, str] = field(default_factory=dict)


def should_review_unit(unit: TranslationUnit) -> bool:
    """Return True if this translation unit should be sent to the AI reviewer."""
    if unit.get_translation() == "":
        return False
    if unit.is_title():
        return False
    if re.search(r"\.(odt|pdf|odg|png)$", unit.get_definition()):
        return False
    if re.search(r"^\d\.\d[a-zA-Z]?$", unit.get_definition()):
        return False
    return True


class TranslationReviewBot:
    """Fetch translation units and review them with OpenAI."""

    def __init__(
        self,
        config: ConfigParser,
        *,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        if not config.has_section("translationreview"):
            raise RuntimeError("Missing [translationreview] section in config.ini")
        if not config.has_option("translationreview", "site"):
            raise RuntimeError("Missing translationreview.site in config.ini")

        if api_key is None and config.has_option("translationreview", "api_key"):
            api_key = config.get("translationreview", "api_key")
        if not api_key:
            raise RuntimeError(
                "Missing API key: set translationreview.api_key in "
                "config.ini or pass --api-key"
            )

        self._config = config
        self.logger = logging.getLogger("pywikitools.translationreview")

        code = config.get("translationreview", "site")
        family = Family()
        self.fortraininglib = ForTrainingLib(
            family.base_url(code, ""), family.scriptpath(code)
        )

        if model is None and config.has_option("translationreview", "model"):
            model = config.get("translationreview", "model")
        if not model:
            raise RuntimeError(
                "Missing model: set translationreview.model in config.ini or pass --model"
            )
        self._model = model

        if base_url is None and config.has_option("translationreview", "base_url"):
            base_url = config.get("translationreview", "base_url")

        request_delay = 0.5
        if config.has_option("translationreview", "request_delay"):
            request_delay = config.getfloat("translationreview", "request_delay")

        timeout = DEFAULT_TIMEOUT_SECONDS
        if config.has_option("translationreview", "timeout"):
            timeout = config.getfloat("translationreview", "timeout")

        self.openai_client = OpenAIClient(
            api_key=api_key,
            model=model,
            base_url=base_url,
            request_delay=request_delay,
            timeout=timeout,
        )

    def _default_output_dir(self, page: str, language_code: str) -> str:
        if self._config.has_option("Paths", "temp"):
            base = self._config.get("Paths", "temp")
        else:
            base = "temp/"
        if not base.endswith("/"):
            base += "/"
        model_slug = self._model.replace("/", "-")
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        return (
            f"{base}translation_review/{page}_{language_code}_{model_slug}_{date_str}/"
        )

    def _build_reference_map(
        self, page: str, reference_language: str
    ) -> Dict[str, str]:
        reference_page = self.fortraininglib.get_translation_units(
            page, reference_language
        )
        if reference_page is None:
            raise RuntimeError(
                f"Couldn't fetch reference translations for {page}/{reference_language}"
            )
        return {
            unit.identifier: unit.get_translation()
            for unit in reference_page
            if unit.get_translation() != ""
        }

    def _process_unit(
        self,
        unit: TranslationUnit,
        reference_translation: str,
        *,
        with_review: bool,
    ) -> UnitReviewResult:
        english = unit.get_definition()
        target = unit.get_translation()

        review = ""
        if with_review:
            review = self._fetch_review(
                unit, reference_translation, english=english, target=target
            )
            if review == TIMEOUT_SENTINEL:
                return UnitReviewResult(
                    identifier=unit.identifier,
                    english=english,
                    reference=reference_translation,
                    target=target,
                    review=TIMEOUT_SENTINEL,
                    best_translation=TIMEOUT_SENTINEL,
                )

        best_translation = self._fetch_translation(
            unit,
            reference_translation,
            english=english,
            target=target,
            review=review,
        )

        return UnitReviewResult(
            identifier=unit.identifier,
            english=english,
            reference=reference_translation,
            target=target,
            review=review,
            best_translation=best_translation,
        )

    def _fetch_review(
        self,
        unit: TranslationUnit,
        reference_translation: str,
        *,
        english: str,
        target: str,
    ) -> str:
        prompt = build_review_prompt(
            language_code=unit.language_code,
            english=english,
            reference=reference_translation,
            target=target,
        )
        return self.openai_client.complete(prompt)

    def _fetch_translation(
        self,
        unit: TranslationUnit,
        reference_translation: str,
        *,
        english: str,
        target: str,
        review: str,
    ) -> str:
        prompt = build_translate_prompt(
            language_code=unit.language_code,
            english=english,
            reference=reference_translation,
            target=target,
            review=review,
        )
        return self.openai_client.complete(prompt)

    @staticmethod
    def _unit_timed_out(result: UnitReviewResult) -> bool:
        return result.best_translation == TIMEOUT_SENTINEL

    def _log_unit_result(
        self,
        result: UnitReviewResult,
        *,
        language_code: str,
        reference_language: str,
    ) -> None:
        if result.review:
            self.logger.info(
                "=== %s ===\n"
                "English:\n%s\n\n"
                "%s reference:\n%s\n\n"
                "Current %s translation:\n%s\n\n"
                "Review:\n%s",
                result.identifier,
                result.english,
                reference_language.upper(),
                result.reference,
                language_code,
                result.target,
                result.review,
            )
        self.logger.warning(
            "=== %s — best translation ===\n%s",
            result.identifier,
            result.best_translation,
        )

    def run(
        self,
        page: str,
        language_code: str,
        *,
        reference_language: Optional[str] = None,
        limit: Optional[int] = None,
        unit_id: Optional[str] = None,
        output_dir: Optional[str] = None,
        generate: Optional[Set[str]] = None,
        with_review: bool = False,
        run_options: Optional[Dict[str, str]] = None,
    ) -> ReviewRunSummary:
        if reference_language is None:
            if self._config.has_option("translationreview", "reference_language"):
                reference_language = self._config.get(
                    "translationreview", "reference_language"
                )
            else:
                reference_language = "de"

        target_page = self.fortraininglib.get_translation_units(page, language_code)
        if target_page is None:
            raise RuntimeError(
                f"Couldn't fetch translation units for {page}/{language_code}"
            )

        reference_map = self._build_reference_map(page, reference_language)
        out_dir = output_dir or self._default_output_dir(page, language_code)
        os.makedirs(out_dir, exist_ok=True)

        units_to_process: List[TranslationUnit] = []
        skipped_units: List[str] = []

        for unit in target_page:
            if unit_id is not None and unit.identifier != unit_id:
                continue
            if not should_review_unit(unit):
                continue
            if unit.identifier not in reference_map:
                self.logger.warning(
                    "Skipping %s: no %s reference translation",
                    unit.identifier,
                    reference_language,
                )
                skipped_units.append(unit.identifier)
                continue
            units_to_process.append(unit)

        if limit is not None:
            units_to_process = units_to_process[:limit]

        total = len(units_to_process)
        results: List[UnitReviewResult] = []
        failed_units: List[str] = []
        processed_count = 0

        for index, unit in enumerate(units_to_process, start=1):
            if with_review:
                progress = f"[{index}/{total}] {unit.identifier} — requesting review..."
            else:
                progress = (
                    f"[{index}/{total}] {unit.identifier} — requesting translation..."
                )
            print(progress)
            try:
                result = self._process_unit(
                    unit,
                    reference_map[unit.identifier],
                    with_review=with_review,
                )
                results.append(result)
                self._log_unit_result(
                    result,
                    language_code=language_code,
                    reference_language=reference_language,
                )
                if self._unit_timed_out(result):
                    failed_units.append(unit.identifier)
                    print(f"[{index}/{total}] {unit.identifier} — TIMEOUT")
                else:
                    processed_count += 1
                    if with_review:
                        print(
                            f"[{index}/{total}] {unit.identifier} — review done, "
                            "fetching best translation..."
                        )
                    print(f"[{index}/{total}] {unit.identifier} — done.")
            except Exception as err:
                self.logger.error("Failed to review %s: %s", unit.identifier, err)
                failed_units.append(unit.identifier)
                print(f"[{index}/{total}] {unit.identifier} — FAILED: {err}")

        effective_options = dict(run_options or {})
        effective_options.setdefault("model", self._model)
        effective_options.setdefault("with_review", "yes" if with_review else "no")

        summary = ReviewRunSummary(
            page=page,
            language_code=language_code,
            reference_language=reference_language,
            processed=processed_count,
            skipped=len(skipped_units),
            failed=len(failed_units),
            output_dir=out_dir,
            skipped_units=skipped_units,
            failed_units=failed_units,
            with_review=with_review,
            run_options=effective_options,
        )
        self._write_reports(results, summary, generate=generate or set())
        return summary

    def _write_reports(
        self,
        results: List[UnitReviewResult],
        summary: ReviewRunSummary,
        *,
        generate: Set[str],
    ) -> None:
        best_path = os.path.join(summary.output_dir, "best_translations.wiki")
        summary_path = os.path.join(summary.output_dir, "summary.txt")

        if summary.with_review:
            review_path = os.path.join(summary.output_dir, "review_report.md")
            with open(review_path, "w", encoding="utf-8") as review_file:
                review_file.write(
                    f"# Translation review: {summary.page} ({summary.language_code})\n\n"
                )
                review_file.write(
                    f"Reference language: {summary.reference_language}\n\n"
                )
                for result in results:
                    review_file.write(f"## {result.identifier}\n\n")
                    review_file.write("### English\n\n")
                    review_file.write(f"{result.english}\n\n")
                    review_file.write(
                        f"### {summary.reference_language.upper()} reference\n\n"
                    )
                    review_file.write(f"{result.reference}\n\n")
                    review_file.write(
                        f"### Current {summary.language_code} translation\n\n"
                    )
                    review_file.write(f"{result.target}\n\n")
                    review_file.write("### Review\n\n")
                    review_file.write(f"{result.review}\n\n")

        with open(best_path, "w", encoding="utf-8") as best_file:
            for result in results:
                best_file.write(f"=== {result.identifier} ===\n")
                best_file.write(f"{result.best_translation}\n\n")

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with open(summary_path, "w", encoding="utf-8") as summary_file:
            summary_file.write(f"Timestamp: {timestamp}\n")
            summary_file.write(f"Page: {summary.page}\n")
            summary_file.write(f"Target language: {summary.language_code}\n")
            summary_file.write(f"Reference language: {summary.reference_language}\n")
            for key in sorted(summary.run_options):
                summary_file.write(f"{key}: {summary.run_options[key]}\n")
            summary_file.write(f"Processed: {summary.processed}\n")
            summary_file.write(f"Skipped: {summary.skipped}\n")
            summary_file.write(f"Failed: {summary.failed}\n")
            if summary.skipped_units:
                summary_file.write(
                    f"Skipped units: {', '.join(summary.skipped_units)}\n"
                )
            if summary.failed_units:
                summary_file.write(f"Failed units: {', '.join(summary.failed_units)}\n")

        if summary.with_review:
            print(f"\nWrote review report: {review_path}")
        print(f"Wrote best translations: {best_path}")
        print(f"Wrote summary: {summary_path}")
        if generate:
            self._write_optional_outputs(results, summary, generate)
        print(
            f"\nDone: {summary.processed} processed, "
            f"{summary.skipped} skipped, {summary.failed} failed."
        )

    def _write_optional_outputs(
        self,
        results: List[UnitReviewResult],
        summary: ReviewRunSummary,
        generate: Set[str],
    ) -> None:
        model_slug = self._model.replace("/", "-")

        if "pdf" in generate:
            from pywikitools.translationreview.pdf_report import (
                UnitReport,
                build_pdf_report,
            )

            units = [
                UnitReport(
                    identifier=result.identifier,
                    english=result.english,
                    reference=result.reference,
                    current_translation=result.target,
                    review=result.review,
                    best_translation=result.best_translation,
                )
                for result in results
            ]
            pdf_path = os.path.join(summary.output_dir, f"{model_slug}_report.pdf")
            build_pdf_report(
                model_name=self._model,
                page=summary.page,
                language_code=summary.language_code,
                reference_language=summary.reference_language,
                units=units,
                output_path=pdf_path,
                include_review=summary.with_review,
            )
            print(f"Wrote PDF report: {pdf_path}")

        if "odt" in generate:
            from pywikitools.translationreview.odt_export import (
                export_suggested_odt,
                suggested_odt_path,
            )

            odt_path = suggested_odt_path(summary.output_dir, model_slug)
            try:
                exported_path = export_suggested_odt(
                    self._config,
                    page=summary.page,
                    language_code=summary.language_code,
                    results=results,
                    output_path=odt_path,
                )
            except Exception as err:
                self.logger.error("Failed to export ODT: %s", err)
                print(f"Failed to export ODT: {err}")
            else:
                if exported_path:
                    print(f"Wrote suggested ODT: {exported_path}")
                else:
                    print("ODT export failed; see log for details.")
