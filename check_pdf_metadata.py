#!/usr/bin/env python3
"""
Check a local PDF against pywikitools PDF metadata rules (same logic as resourcesbot).

Usage (from repository root):
  ./env/bin/python check_pdf_metadata.py WORKSHEET_NAME LANGUAGE_CODE PATH_TO_PDF

Title and expected version are read from the wiki unless you pass --title and/or --version.
For languages other than English, the wiki API is used for language names (subject line check).

Examples:
  ./env/bin/python check_pdf_metadata.py Hearing_from_God de ~/Gottes_Reden_wahrnehmen.pdf
  ./env/bin/python check_pdf_metadata.py Dealing_with_Money de ./Umgang_mit_Geld.pdf \\
      --title "Umgang mit Geld" --version 1.0
"""

import argparse
import logging
import os
import sys
from typing import List, Optional

from pywikitools.family import Family
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.pdftools.metadata import check_metadata
from pywikitools.resourcesbot.data_structures import TranslationProgress, WorksheetInfo

_DEFAULT_SITE = "4training"
_family = Family()
DEFAULT_BASE_URL = _family.base_url(_DEFAULT_SITE, "")
DEFAULT_SCRIPT_PATH = _family.scriptpath(_DEFAULT_SITE)


def build_worksheet_info(
    lib: ForTrainingLib,
    worksheet_name: str,
    language_code: str,
    title: Optional[str],
    version: Optional[str],
) -> WorksheetInfo:
    """Resolve title/version from API when omitted."""
    resolved_title = title
    if resolved_title is None:
        fetched = lib.get_translated_title(worksheet_name, language_code)
        if fetched is None:
            raise ValueError(
                f"Could not fetch translated title for {worksheet_name}/{language_code}. "
                "Use --title or check the worksheet name and language code."
            )
        resolved_title = fetched.strip()

    resolved_version = version
    if resolved_version is None:
        fetched = lib.get_version(worksheet_name, language_code)
        if fetched is None:
            raise ValueError(
                f"Could not fetch version for {worksheet_name}/{language_code}. Use --version."
            )
        resolved_version = fetched.strip()

    progress = TranslationProgress(translated=1, fuzzy=0, total=1)
    return WorksheetInfo(
        worksheet_name, language_code, resolved_title, progress, resolved_version
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check PDF metadata against 4training standards (same checks as resourcesbot)."
    )
    parser.add_argument(
        "worksheet_name",
        help="English worksheet page name, e.g. Hearing_from_God",
    )
    parser.add_argument("language_code", help="Language code, e.g. de or en")
    parser.add_argument("pdf_path", help="Path to the local PDF file")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"MediaWiki site base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--script-path",
        default=DEFAULT_SCRIPT_PATH,
        help=f"MediaWiki $wgScriptPath (default: {DEFAULT_SCRIPT_PATH!r})",
    )
    parser.add_argument(
        "--title",
        help="Translated worksheet title (if omitted, fetched from the wiki)",
    )
    parser.add_argument(
        "--version",
        help="Expected worksheet version string (if omitted, fetched from the wiki)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING)

    pdf_path = os.path.abspath(args.pdf_path)
    if not os.path.isfile(pdf_path):
        print(f"Error: not a file: {pdf_path}", file=sys.stderr)
        return 2

    lib = ForTrainingLib(args.base_url, args.script_path)
    try:
        info = build_worksheet_info(
            lib,
            args.worksheet_name,
            args.language_code,
            args.title,
            args.version,
        )
    except ValueError as err:
        print(str(err), file=sys.stderr)
        return 2

    result = check_metadata(lib, pdf_path, info)
    print(result.to_string(include_version=True))
    return 0 if result.correct else 1


if __name__ == "__main__":
    sys.exit(main())
