"""
Contains the data-structures and main methods for the reporting.
Through reporting, the ressources-bot keeps track of what it did.
This information can then be made available to people who need to know what is going on.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from datetime import datetime

import pywikibot


class LanguageReport(ABC):
    """
    Basic data structure for the report of one module running once for one language.
    """

    def __init__(self, language_code: str):
        self.language = language_code
        self.summary_text = ""

    def was_anything_to_report(self) -> bool:
        return self.summary_text != ""

    @abstractmethod
    def get_summary(self) -> str:
        return self.summary_text

    @classmethod
    @abstractmethod
    def get_module_name(cls) -> str:
        return ""

    @classmethod
    @abstractmethod
    def get_module_summary(cls, lang_reports: list) -> str:
        if len(lang_reports) == 0:
            return ""
        else:
            return f"Ran module {cls.get_module_name()} for {len(lang_reports)} languages"


def print_summaries(module_reports: Dict[str, List[LanguageReport]]):
    print(make_summaries(module_reports))


def make_summaries(module_reports: Dict[str, List[LanguageReport]]):
    summary = ""
    for key, value in module_reports.items():
        if len(value) == 0:
            summary = f"Module {key}: Empty Report"
        else:
            summary += f"Module {key}'s report: {type(value[0]).get_module_summary(value)}\n"
    return summary


def generate_mediawiki_overview(module_reports: Dict[str, List[LanguageReport]]):
    mediawiki = "===Overview===\n\n"
    for key, value in module_reports.items():
        if len(value) == 0:
            mediawiki = f"*Module '''{key}''': Empty Report\n\n"
        else:
            mediawiki += f"*Module '''{key}''''s report: {type(value[0]).get_module_summary(value)}\n\n"
    return mediawiki


def generate_mediawiki(module_reports: Dict[str, List[LanguageReport]]):
    timestamp_str = datetime.now().strftime("%Y-%m-%d--%H:%M")
    head = f"==Resourcesbot-run at {timestamp_str}==\n\n"
    overview = generate_mediawiki_overview(module_reports)
    details = "===Detailed Reports per Module===\n\n"
    for key, value in module_reports.items():
        if len(value) == 0:
            pass
        else:
            details += f"===={key}====\n\n"
            for lang_report in value:
                details += f"*{lang_report.get_summary()}\n\n"
    return head + overview + details


def save_report(site, module_reports: Dict[str, List[LanguageReport]]):
    page_url = "4training:Resourcesbot.report"
    page = pywikibot.Page(site, page_url)
    if page.exists():
        page.text = generate_mediawiki(module_reports) + page.text
    else:
        page.text = generate_mediawiki(module_reports)
    page.save("Created summary for Resourcesbot run")
