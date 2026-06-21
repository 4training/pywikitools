import os
from configparser import ConfigParser
from typing import Dict, List, Optional

from pywikitools.translateodt import TranslateODT
from pywikitools.translationreview.bot import UnitReviewResult
from pywikitools.translationreview.openai_client import TIMEOUT_SENTINEL


def suggestions_from_results(
    results: List[UnitReviewResult],
) -> Dict[str, str]:
    """Build a mapping of unit identifier to suggested translation."""
    suggestions: Dict[str, str] = {}
    for result in results:
        if not result.best_translation or result.best_translation == TIMEOUT_SENTINEL:
            continue
        suggestions[result.identifier] = result.best_translation
    return suggestions


def export_suggested_odt(
    config: ConfigParser,
    *,
    page: str,
    language_code: str,
    results: List[UnitReviewResult],
    output_path: str,
) -> Optional[str]:
    """Fill an ODT with suggested translations via translateodt search-and-replace."""
    if not config.has_option("translationreview", "site"):
        raise RuntimeError("Missing translationreview.site in config.ini")

    site = config.get("translationreview", "site")
    translate_odt = TranslateODT(
        skip_correctbot=True,
        keep_english_file=False,
        config={"translateodt": {"site": site}},
    )
    return translate_odt.translate_worksheet(
        page,
        language_code,
        output_path=output_path,
        export_pdf=False,
        translation_overrides=suggestions_from_results(results),
    )


def suggested_odt_path(output_dir: str, model_slug: str) -> str:
    return os.path.join(output_dir, f"{model_slug}_suggested.odt")
