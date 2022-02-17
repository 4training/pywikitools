"""
Base classes for all functionality doing useful stuff with the data gathered previously.

If the functionality looks only at one language at a time, implement LanguagePostProcessor.
If the functionality needs to look at everything, implement GlobalPostProcessor.
The resourcesbot will first call any LanguagePostProcessors for each language and
afterwards call any GlobalPostProcessor
"""
from abc import ABC, abstractmethod
from typing import Dict
from pywikitools.ResourcesBot.changes import ChangeLog
from pywikitools.ResourcesBot.data_structures import LanguageInfo


class LanguagePostProcessor(ABC):
    """Base class for all functionality doing useful stuff with the data on one language"""

    @abstractmethod
    def run(self, language_info: LanguageInfo, change_log: ChangeLog):
        """Entry point"""
        pass

class GlobalPostProcessor(ABC):
    """Base class for all functionality doing useful stuff with the data on all languages"""

    @abstractmethod
    def run(self, language_data: Dict[str, LanguageInfo], changes: Dict[str, ChangeLog]):
        """Entry point"""
        pass