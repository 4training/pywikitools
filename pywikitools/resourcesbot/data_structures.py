import datetime
import json
import logging
from typing import Dict, List, Optional

import pywikibot
import urllib
from pywikitools import fortraininglib
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType

from pywikitools.fortraininglib import TranslationProgress


class FileInfo:
    """
    Holds information on one file that is available on the website
    This shouldn't be modified after creation (is there a way to enforce that?)
    """
    __slots__ = ['file_type', 'url', 'timestamp']
    def __init__(self, file_type: str, url: str, timestamp: datetime.datetime):
        self.file_type = file_type
        self.url: str = url
        self.timestamp: datetime.datetime = timestamp

    def __str__(self):
        return f"{self.file_type} {self.url} {self.timestamp.isoformat()}"

class WorksheetInfo:
    """Holds information on one worksheet in one specific language
    Only for worksheets that are at least partially translated
    """
    __slots__ = ['_name', '_language', '_files', 'title', 'progress']

    def __init__(self, en_name: str, language: str, title: str, progress: TranslationProgress):
        """
        @param en_name: English name of the worksheet
        @param language: language code
        @param title: translated worksheet title
        @param progress: how much is already translated"""
#        self._en_name: str = en_name
#        self._language: str = language
        self._files: Dict[str, FileInfo] = {}
        self.title: str = title
        self.progress: TranslationProgress = progress

    def add_file_info(self, file_type: str, url: str = None, timestamp: str = None,
                      file_info: pywikibot.page.FileInfo = None) -> Optional[FileInfo]:
        """Add information about another file associated with this worksheet
        Either give url and timestamp or file_info
        This will log on errors but shouldn't raise exceptions
        @return FileInfo or None if it wasn't successful
        """
        new_file_info = None
        logger = logging.getLogger('pywikitools.resourcesbot.worksheetinfo')
        if url is not None and timestamp is not None:
            if isinstance(timestamp, str):
                try:
                    timestamp = timestamp.replace('Z', '+00:00')    # we want to support this format as well
                    new_file_info = FileInfo(file_type, url, datetime.datetime.fromisoformat(timestamp))
                except (ValueError, TypeError):
                    logger.warning("Couldn't parse timestamp {timestamp}. add_file_info() failed.")
            else:
                logger.warning("add_file_info() failed: timestamp is not of type str.")
        elif file_info is not None:
            new_file_info = FileInfo(file_type, urllib.parse.unquote(file_info.url), file_info.timestamp)
        if new_file_info is not None:
            self._files[file_type] = new_file_info
        return new_file_info

    def get_file_infos(self) -> Dict[str, FileInfo]:
        """Returns all available files associated with this worksheet"""
        return self._files

    def has_file_type(self, file_type: str) -> bool:
        """Does the worksheet have a file for download (e.g. "pdf")?"""
        return file_type in self._files

    def get_file_type_info(self, file_type: str) -> Optional[FileInfo]:
        """Returns FileInfo of specified type (e.g. "pdf"), None if not existing"""
        if file_type in self._files:
            return self._files[file_type]
        return None

    def is_incomplete(self) -> bool:
        """A translation is incomplete if most units are translated but at least one is not translated or fuzzy"""
        return self.progress.is_incomplete()


class LanguageInfo:
    """Holds information on all available worksheets in one specific language"""
    __slots__ = '_language_code', 'worksheets'

    def __init__(self, language_code: str):
        self._language_code: str = language_code
        self.worksheets: Dict[str, WorksheetInfo] = {}

    def deserialize(self, obj):
        """Reads a JSON object of a data structure into this LanguageInfo object.
        Any previously stored data is discarded.

        This is a top-down approach
        TODO: The JSON data structure isn't very good - improve it to make bottom-up approach possible
        Then we could use json.JSONDecoder() which would be a bit more elegant
        For that WorksheetInfo and FileInfo should also be well serializable / deserializable
        """
        self.worksheets = {}
        logger = logging.getLogger('pywikitools.resourcesbot.languageinfo')
        if isinstance(obj, Dict):
            for worksheet, details in obj.items():
                if isinstance(worksheet, str) and isinstance(details, Dict):
                    if "title" in details:
                        worksheet_info = WorksheetInfo(worksheet, self._language_code, details['title'], None)
                        for file_type in fortraininglib.get_file_types():
                            if file_type in details:
                                worksheet_info.add_file_info(file_type, url=details[file_type],
                                    timestamp=(details[file_type + '-timestamp']))

                        self.add_worksheet_info(worksheet, worksheet_info)
                    else:
                         logger.warning(f"No title attribute in {worksheet} object, skipping.")
                else:
                    logger.warning("Unexpected data structure while trying to deserialize LanguageInfo object.")
        else:
            logger.warning("Unexpected data structure. Couldn't deserialize LanguageInfo object.")

    def get_language_code(self) -> str:
        return self._language_code

    def add_worksheet_info(self, name: str, worksheet_info: WorksheetInfo):
        self.worksheets[name] = worksheet_info

    def has_worksheet(self, name: str) -> bool:
        return name in self.worksheets

    def get_worksheet(self, name: str) -> Optional[WorksheetInfo]:
        if name in self.worksheets:
            return self.worksheets[name]
        return None

    def worksheet_has_type(self, name: str, file_type: str) -> bool:
        """Convienence method combining LanguageInfo.has_worksheet() and WorksheetInfo.has_file_type()"""
        if name in self.worksheets:
            return self.worksheets[name].has_file_type(file_type)
        return False

    def compare(self, old) -> ChangeLog:
        """
        Compare ourselves to another (older) LanguageInfo object: have there been changes / updates?

        @return data structure with all changes
        """
        change_log = ChangeLog()
        logger = logging.getLogger('pywikitools.resourcesbot.languageinfo')
        if not isinstance(old, LanguageInfo):
            logger.warning("Comparison failed: expected LanguageInfo object.")
            return change_log
        for title, info in self.worksheets.items():
            if title in old.worksheets:
                if info.has_file_type('pdf'):
                    if not old.worksheets[title].has_file_type('pdf'):
                        change_log.add_change(title, ChangeType.NEW_PDF)
                    # TODO resolve TypeError: can't compare offset-naive and offset-aware datetimes
#                    elif old.worksheets[title].get_file_type_info('pdf').timestamp < info.get_file_type_info('pdf').timestamp:
#                        change_log.add_change(title, ChangeType.UPDATED_PDF)
                elif old.worksheets[title].has_file_type('pdf'):
                    change_log.add_change(title, ChangeType.DELETED_PDF)

                if info.has_file_type('odt'):
                    if not old.worksheets[title].has_file_type('odt'):
                        change_log.add_change(title, ChangeType.NEW_ODT)
                    # TODO resolve TypeError: can't compare offset-naive and offset-aware datetimes
#                    elif old.worksheets[title].get_file_type_info('odt').timestamp < info.get_file_type_info('odt').timestamp:
#                        change_log.add_change(title, ChangeType.UPDATED_ODT)
                elif old.worksheets[title].has_file_type('odt'):
                    change_log.add_change(title, ChangeType.DELETED_ODT)
            else:
                change_log.add_change(title, ChangeType.NEW_WORKSHEET)
        for worksheet in old.worksheets:
            if worksheet not in self.worksheets:
                change_log.add_change(worksheet, ChangeType.DELETED_WORKSHEET)

        # TODO Emit also ChangeType.UPDATED_WORKSHEET by saving and comparing version number
        return change_log

    def list_worksheets_with_missing_pdf(self) -> List[str]:
        """ Returns a list of worksheets which are translated but are missing the PDF
        """
        return [worksheet for worksheet in self.worksheets if not self.worksheets[worksheet].has_file_type('pdf')]

    def list_incomplete_translations(self) -> List[WorksheetInfo]:
        return [worksheet for worksheet in self.worksheets if self.worksheets[worksheet].is_incomplete()]

    def count_finished_translations(self) -> int:
        count: int = 0
        for worksheet_info in self.worksheets.values():
            if worksheet_info.has_file_type('pdf'):
                count += 1
        return count


class LanguageInfoEncoder(json.JSONEncoder):
    """serialize the data structure stored in ResourcesBot._result
    TODO: This currently uses the legacy dictionary data structure that was stored in global_result before,
    think about it and define a better structure?
    """
    def default(self, obj):
        if isinstance(obj, LanguageInfo):
            return obj.worksheets
        if isinstance(obj, WorksheetInfo):
            worksheet_map = {}
            worksheet_map['title'] = obj.title
            for file_type, file_info in obj.get_file_infos().items():
                worksheet_map[f"{file_type}-timestamp"] = file_info.timestamp.isoformat()
                worksheet_map[file_type] = file_info.url
            return worksheet_map
        if isinstance(obj, pywikibot.Timestamp):
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
