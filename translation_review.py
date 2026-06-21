#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
AI-assisted translation review tool.

Fetches translation units from the MediaWiki API and sends each unit to an
OpenAI-compatible API for an improved translation. By default this is one API
call per unit. With --with-review, each unit gets two calls: a full review and
discussion, then the best improved translation.
Results are written to report files and logged to the console
(the full analysis at INFO when --with-review is used, the best translation at
WARNING). Optional PDF and ODT exports are available with --generate.
Progress is also logged to the console.
This tool does not write anything back to the wiki.

Use --limit or --unit for testing to control cost.

Examples:
    python3 translation_review.py Forgiving_Step_by_Step tr
    python3 translation_review.py Forgiving_Step_by_Step tr \\
        --reference-lang de --limit 5
    python3 translation_review.py Forgiving_Step_by_Step tr --unit "Prayer/7"
    python3 translation_review.py Forgiving_Step_by_Step tr --with-review
    python3 translation_review.py Forgiving_Step_by_Step tr \\
        --generate pdf,odt

Configuration: config.ini [translationreview] section (see config.example.ini).
"""

import argparse
from configparser import ConfigParser
import logging
from os.path import abspath, dirname, join
import sys
from typing import Dict, List

from pywikitools.translationreview.bot import TranslationReviewBot


VALID_GENERATE_FORMATS = frozenset({"pdf", "odt"})


def parse_generate(value: str) -> set[str]:
    if not value.strip():
        return set()
    formats = {part.strip().lower() for part in value.split(",") if part.strip()}
    unknown = formats - VALID_GENERATE_FORMATS
    if unknown:
        raise argparse.ArgumentTypeError(
            f"Unknown output format(s): {', '.join(sorted(unknown))}. "
            f"Choose from: {', '.join(sorted(VALID_GENERATE_FORMATS))}"
        )
    return formats


def build_run_options(args: argparse.Namespace) -> Dict[str, str]:
    options: Dict[str, str] = {
        "with_review": "yes" if args.with_review else "no",
        "loglevel": args.loglevel,
    }
    if args.model:
        options["model"] = args.model
    if args.api_key:
        options["api_key"] = "(from --api-key)"
    if args.base_url:
        options["base_url"] = args.base_url
    if args.reference_lang:
        options["reference_lang"] = args.reference_lang
    if args.limit is not None:
        options["limit"] = str(args.limit)
    if args.unit:
        options["unit"] = args.unit
    if args.output_dir:
        options["output_dir"] = args.output_dir
    if args.generate:
        options["generate"] = ",".join(sorted(args.generate))
    return options


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
        "--api-key",
        help="OpenAI-compatible API key (overrides translationreview.api_key in config)",
    )
    parser.add_argument(
        "--base-url",
        help="OpenAI-compatible API base URL (overrides translationreview.base_url in config)",
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
        "--with-review",
        action="store_true",
        help="Also generate a per-unit review (two API calls per unit; "
        "writes review_report.md)",
    )
    parser.add_argument(
        "--generate",
        type=parse_generate,
        default=set(),
        metavar="FORMATS",
        help="Comma-separated optional outputs: pdf, odt "
        "(best_translations.wiki and summary.txt are always created; "
        "review_report.md only with --with-review)",
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

    bot = TranslationReviewBot(
        config,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
    )
    summary = bot.run(
        args.page,
        args.language_code,
        reference_language=args.reference_lang,
        limit=args.limit,
        unit_id=args.unit,
        output_dir=args.output_dir,
        generate=args.generate,
        with_review=args.with_review,
        run_options=build_run_options(args),
    )

    if summary.failed > 0:
        sys.exit(1)
