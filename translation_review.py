#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
AI-assisted translation review tool.

Fetches translation units from the MediaWiki API and sends each unit to an
OpenAI-compatible API twice:
  1. for a full review and discussion,
  2. for the best improved translation only.
Results are written to report files and logged to the console
(the full analysis at INFO, the best translation at WARNING).
Progress is also logged to the console.
This tool does not write anything back to the wiki.

Two API calls per unit — use --limit or --unit for testing to control cost.

Examples:
    python3 translation_review.py Forgiving_Step_by_Step tr
    python3 translation_review.py Forgiving_Step_by_Step tr \\
        --reference-lang de --limit 5
    python3 translation_review.py Forgiving_Step_by_Step tr --unit "Prayer/7"

Configuration: config.ini [translationreview] section (see config.example.ini).
"""

import argparse
from configparser import ConfigParser
import logging
from os.path import abspath, dirname, join
import sys
from typing import List

from pywikitools.translationreview.bot import TranslationReviewBot


def parse_arguments() -> argparse.Namespace:
    log_levels: List[str] = ["debug", "info", "warning", "error"]

    parser = argparse.ArgumentParser(
        description="Review translations with OpenAI assistance."
    )
    parser.add_argument("page", help="Name of the mediawiki page (worksheet)")
    parser.add_argument(
        "language_code",
        help="Target language code to review (e.g. tr)",
    )
    parser.add_argument(
        "--reference-lang",
        help="Reference translation language (default: from config or de)",
    )
    parser.add_argument(
        "--model",
        help="OpenAI model name (overrides config; required if translationreview.model is unset)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process at most N units (for testing / cost control)",
    )
    parser.add_argument(
        "--unit",
        help='Process only one translation unit key (e.g. "Prayer/7")',
    )
    parser.add_argument(
        "--output-dir",
        help="Override output directory for report files",
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        choices=log_levels,
        default="warning",
        help="set loglevel for the script",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    assert isinstance(numeric_level, int)
    sh.setLevel(numeric_level)
    root.addHandler(sh)

    config = ConfigParser()
    config.read(join(dirname(abspath(__file__)), "config.ini"))

    bot = TranslationReviewBot(config, model=args.model)
    summary = bot.run(
        args.page,
        args.language_code,
        reference_language=args.reference_lang,
        limit=args.limit,
        unit_id=args.unit,
        output_dir=args.output_dir,
    )

    if summary.failed > 0:
        sys.exit(1)
