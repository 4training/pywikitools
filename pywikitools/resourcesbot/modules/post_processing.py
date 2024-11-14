"""
Base classes for all functionality doing useful stuff with the data gathered previously.

If the functionality looks only at one language at a time, implement LanguagePostProcessor.
If the functionality needs to look at everything, implement GlobalPostProcessor.
The resourcesbot will first call any LanguagePostProcessors for each language and
afterwards call any GlobalPostProcessor
"""
from abc import ABC, abstractmethod
from typing import Dict
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo


class LanguagePostProcessor(ABC):
    """Base class for all functionality doing useful stuff with the data on one language.

    We include information on English as well because several post-processors need it as reference
    """

    def __init__(
        self,
        fortraininglib: ForTrainingLib,
        config: ConfigParser = None,
        site: pywikibot.site.APISite = None,
        *,
        force_rewrite: bool = False,
):
        self.fortraininglib = fortraininglib
        self._config = config
        self._site = site
        self._force_rewrite: Final[bool] = force_rewrite


    @abstractmethod
    def run(self, language_info: LanguageInfo, english_info: LanguageInfo,
            changes: ChangeLog, english_changes: ChangeLog):
        """Entry point"""
        pass


class GlobalPostProcessor(ABC):
    """Base class for all functionality doing useful stuff with the data on all languages"""

    @abstractmethod
    def run(self, language_data: Dict[str, LanguageInfo], changes: Dict[str, ChangeLog]):
        """Entry point"""
        pass
