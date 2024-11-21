"""
Base classes for all functionality doing useful stuff with the data gathered previously.

If the functionality looks only at one language at a time, implement LanguagePostProcessor.
If the functionality needs to look at everything, implement GlobalPostProcessor.
The resourcesbot will first call any LanguagePostProcessors for each language and
afterwards call any GlobalPostProcessor
"""
from abc import ABC, abstractmethod
from configparser import ConfigParser
from typing import Dict, Final, Optional

import pywikibot

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo


class LanguagePostProcessor(ABC):
    """Base class for all functionality doing useful stuff with the data on one language.

    We include information on English as well because several post-processors need it as reference
    """

    @classmethod
    @abstractmethod
    def help_summary(cls) -> str:
        """Used for the resourcesbot.py -h help command"""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def abbreviation(cls) -> str:
        """Abbreviation to be used for this module with the -m and --rewrite options"""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def can_be_rewritten(cls) -> bool:
        """Is the force_rewrite flag available for this module?"""
        raise NotImplementedError

    def __init__(
        self,
        fortraininglib: ForTrainingLib,
        config: ConfigParser = None,
        site: pywikibot.site.APISite = None
    ):
        self.fortraininglib: Final[ForTrainingLib] = fortraininglib
        self._config: Final[ConfigParser] = config
        self._site: Final[Optional[pywikibot.site.APISite]] = site

    @abstractmethod
    def run(self, language_info: LanguageInfo, english_info: LanguageInfo,
            changes: ChangeLog, english_changes: ChangeLog,
            *, force_rewrite: bool = False):
        """Entry point"""
        raise NotImplementedError()


class GlobalPostProcessor(ABC):
    """Base class for all functionality doing useful stuff with the data on all languages"""

    @abstractmethod
    def run(self, language_data: Dict[str, LanguageInfo], changes: Dict[str, ChangeLog]):
        """Entry point"""
        raise NotImplementedError()
