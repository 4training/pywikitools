"""
Contains the data-structures and main methods for the reporting.
Through reporting, the ressources-bot keeps track of what it did.
This information can then be made available to people who need to know what is going on.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from datetime import datetime

import pywikibot


class Report(ABC):
    """
    Basic data structure for the report of one module running once for one language.
    """

    def __init__(self, language_code: str):
        self.language = language_code
        self.summary_text = ""

    def was_anything_to_report(self) -> bool:
        return self.get_summary() != ""

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


class ReportSummary:

    def __init__(self):
        self.module_reports: Dict[str, List[Report]] = dict()

    def add_module(self, module_name: str):
        self.module_reports[module_name] = list()

    def add_language_report(self, module_name: str, language_report: Report):
        self.module_reports.setdefault(module_name, []).append(language_report)

    def print_summaries(self):
        print(self.make_summaries())

    def make_summaries(self):
        summary = ""
        for key, value in self.module_reports.items():
            if len(value) == 0:
                summary = f"Module {key}: Empty Report"
            else:
                summary += f"Module {key}'s report: {type(value[0]).get_module_summary(value)}\n"
        return summary

    def get_reports_by_languages(self):
        reports_by_language: Dict[str, List[Report]] = dict()
        for key, value in self.module_reports.items():
            if len(value) == 0:
                pass
            else:
                for lang_report in value:
                    reports_by_language.setdefault(lang_report.language, []).append(lang_report)
        return reports_by_language

    def generate_mediawiki_overview(self):
        mediawiki = "===Overview===\n\n"
        for key, value in self.module_reports.items():
            if len(value) == 0:
                mediawiki = f"*Module '''{key}''': Empty Report\n\n"
            else:
                mediawiki += f"*Module '''{key}''''s report: {type(value[0]).get_module_summary(value)}\n\n"
        return mediawiki

    def generate_mediawiki(self):
        timestamp_str = datetime.now().strftime("%Y-%m-%d--%H:%M")
        head = f"==Resourcesbot-run at {timestamp_str}==\n\n"
        overview = self.generate_mediawiki_overview()
        details = "===Detailed Reports per Language===\n\n"
        for key, value in self.get_reports_by_languages().items():
            if len(value) == 0:
                pass
            else:
                anything_to_report = False
                lang_summary = ""
                for lang_report in value:
                    if lang_report.was_anything_to_report():
                        anything_to_report = True
                        lang_summary += f"*{lang_report.get_summary()}\n\n"
                if anything_to_report:
                    details += f"===={key}====\n\n"
                    details += lang_summary
        return head + overview + details

    def save_report(self, site):
        page_url = "4training:Resourcesbot.report"
        page = pywikibot.Page(site, page_url)
        if page.exists():
            page.text = self.generate_mediawiki() + page.text
        else:
            page.text = self.generate_mediawiki()
        page.save("Created summary for Resourcesbot run")
