from datetime import datetime
import json
import logging
from typing import Any, Dict, Final, List, Optional, Union

import pywikibot
from urllib.parse import unquote
from pywikitools.lang.native_numerals import native_to_standard_numeral
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType


class TranslationProgress:
    __slots__ = ["translated", "fuzzy", "total"]

    def __init__(self, translated, fuzzy, total, **kwargs):
        """
        The constructor can take a dictionary as returned when doing a translation progress query:
        { "total": 44, "translated": 44, "fuzzy": 0, "proofread": 0, "code": "de", "language": "de" },
        from https://www.4training.net/mediawiki/api.php?action=query&meta=messagegroupstats&mgsgroup=page-Church
        """
        self.translated: Final[int] = int(translated)
        self.fuzzy: Final[int] = int(fuzzy)
        self.total: Final[int] = int(total)

    def is_unfinished(self) -> bool:
        """
        Definition: a translation is unfinished if more than 4 units are neither translated nor fuzzy
        Unfinished translations are not shown on language information pages
        """
        if (self.total - self.fuzzy - self.translated) > 4:
            return True
        return False

    def is_incomplete(self) -> bool:
        """
        A translation is incomplete if it is not unfinished (!) but still there is at least
        one translation unit which is neither translated nor fuzzy
        """
        if self.is_unfinished():    # We don't consider unfinished translations as incomplete!
            return False
        if self.translated + self.fuzzy < self.total:
            return True
        return False

    def __str__(self) -> str:
        """
        Print the translation progress
        e.g. "13+1/14" is short for 13 translated units and one outdated (fuzzy) translation unit,
        out of 14 translation units total
        """
        return f"{self.translated}+{self.fuzzy}/{self.total}"


class FileInfo:
    """
    Holds information on one file that is available on the website
    This shouldn't be modified after creation
    """
    __slots__ = ['file_type', 'url', 'timestamp', 'translation_unit']

    def __init__(self, file_type: str, url: str, timestamp: Union[datetime, str],
                 translation_unit: Optional[int] = None):
        """
            file_type: e.g. "pdf" (one of fortraininglib.get_file_types())
        """
        """
        @param file_type: e.g. "pdf" (one of fortraininglib.get_file_types())
        @param url: full URL where the file can be downloaded
        @param timestamp: Last modification date of the file
        @param translation_unit: Number of the translation unit where the file name is stored in
               Example: for worksheet "My_Story_with_God" this is 28
               -> English file name can be found in Translations:My_Story_with_God/28/en
               -> German file name can be found in Translations:My_Story_with_God/28/de
               We only store this information for English worksheets
        """
        self.file_type: Final[str] = file_type
        self.url: Final[str] = url
        self.translation_unit: Final[Optional[int]] = translation_unit
        if isinstance(timestamp, pywikibot.Timestamp):
            # This is tricky: pywikibot.Timestamp derives from datetime
            # but its isoformat() method formats the output with "Z" instead of "+00:00"
            # That can lead to unexpected behavior during JSON export (sometimes using this style, sometimes the other)
            # To avoid confusion we want to make sure that self.timestamp always holds a "normal" datetime object
            # (never a pywikibot.Timestamp) - we'll always export the +00:00 format.
            timestamp = timestamp.isoformat()

        if isinstance(timestamp, datetime):
            self.timestamp: datetime = timestamp
        else:   # timestamp is str
            try:
                timestamp = timestamp.replace('Z', '+00:00')        # fromisoformat() wouldn't understand the Z format
                self.timestamp = datetime.fromisoformat(timestamp)  # But we want to be able to read that format also
            except (ValueError, TypeError):
                logger = logging.getLogger('pywikitools.resourcesbot.fileinfo')
                logger.error("Invalid timestamp {timestamp}. {file_type}: {url}.")
                self.timestamp = datetime(1970, 1, 1)

    def get_file_name(self) -> str:
        """Return file name out of url"""
        pos = self.url.rfind('/')
        if pos > -1:
            return self.url[pos+1:]
        return self.url

    def __str__(self):
        return f"{self.file_type} {self.url} {self.timestamp.isoformat()}"


class WorksheetInfo:
    """Holds information on one worksheet in one specific language
    Only for worksheets that are at least partially translated
    """
    __slots__ = ['page', 'language_code', 'title', 'progress', 'version', 'version_unit', '_files']

    def __init__(self, page: str, language_code: str, title: str, progress: TranslationProgress,
                 version: str, version_unit: Optional[int] = None):
        """
        @param page: English name of the worksheet
        @param title: translated worksheet title
        @param version: Version number of the worksheet
        @param version_unit: Number of the translation unit where version is to be found
                             We only store this for English worksheets
        @param progress: how much is already translated"""
        self.page: Final[str] = page
        self.language_code: Final[str] = language_code
        self.title: Final[str] = title
        self.progress: Final[TranslationProgress] = progress
        self.version: Final[str] = version
        self.version_unit: Final[Optional[int]] = version_unit
        self._files: Dict[str, FileInfo] = {}

    def add_file_info(self, file_info: Optional[FileInfo] = None,
                      file_type: Optional[str] = None,
                      from_pywikibot: Optional[pywikibot.page.FileInfo] = None,
                      unit: Optional[int] = None):
        """Add information about another file associated with this worksheet.
        You can call the function in two different ways:
        - providing file_info
        - providing file_type and from_pywikibot (and potentially unit)
        This will log on errors but shouldn't raise exceptions
        """
        if file_info is not None:
            self._files[file_info.file_type] = file_info
            return
        assert file_type is not None and from_pywikibot is not None
        self._files[file_type] = FileInfo(file_type, unquote(from_pywikibot.url), from_pywikibot.timestamp, unit)

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

    def get_file_type_name(self, file_type: str) -> str:
        """Returns name of the file of the specified type (e.g. "pdf")
        @return only name (not full URL)
        @return empty string if we don't have the specified file type"""
        if file_type in self._files:
            return self._files[file_type].get_file_name()
        return ""

    def is_incomplete(self) -> bool:
        """A translation is incomplete if most units are translated but at least one is not translated or fuzzy"""
        return self.progress.is_incomplete()

    def has_same_version(self, english_info) -> bool:
        """
        Compare our version string with the version string of the English original: is it the same?
        Native numerals will be converted to standard numerals.
        One additional character in our version will be ignored (e.g. "1.2b" is the same as "1.2")
        @param english_info: WorksheetInfo
        """
        if self.version == "":
            return False
        assert isinstance(english_info, WorksheetInfo)
        our_version = native_to_standard_numeral(self.language_code, self.version)
        # Ignore one trailing character in our version
        if our_version[-1:].isalpha():
            our_version = our_version[:-1]
        if our_version == english_info.version:
            return True
        return False

    def __str__(self) -> str:
        """For debugging purposes: Format all data as a human-readable string"""
        content: str = f"{self.page}/{self.language_code}: '{self.title}' with version {self.version}"
        if self.version_unit is not None:
            content += f" (in translation unit {self.version_unit})"
        content += f" and progress {self.progress} and {len(self._files)} files"
        if len(self._files) > 0:
            content += ":\n"
        for file_info in self._files.values():
            content += f"{file_info}\n"
        return content


class LanguageInfo:
    """Holds information on all available worksheets in one specific language"""
    __slots__ = 'language_code', 'english_name', 'worksheets'

    def __init__(self, language_code: str, english_name: str):
        self.language_code: Final[str] = language_code
        self.english_name: Final[str] = english_name    # if there was an error before this could be ""
        self.worksheets: Dict[str, WorksheetInfo] = {}

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

        In case of NEW_WORKSHEET, no NEW_PDF / NEW_ODT will be emitted (even if files got added)
        In case of DELETED_WORKSHEET, no DELETED_PDF / DELETED_ODT will be emitted (even if files existed before)
        @return data structure with all changes
        """
        change_log = ChangeLog()
        logger = logging.getLogger('pywikitools.resourcesbot.languageinfo')
        if not isinstance(old, LanguageInfo):
            logger.warning("Comparison failed: expected LanguageInfo object.")
            return change_log
        for title, info in self.worksheets.items():
            if title in old.worksheets:
                pdf_info = info.get_file_type_info("pdf")
                if pdf_info is not None:
                    old_pdf_info = old.worksheets[title].get_file_type_info('pdf')
                    if old_pdf_info is None:
                        change_log.add_change(title, ChangeType.NEW_PDF)
                    elif old_pdf_info.timestamp < pdf_info.timestamp:
                        change_log.add_change(title, ChangeType.UPDATED_PDF)
                elif old.worksheets[title].has_file_type('pdf'):
                    change_log.add_change(title, ChangeType.DELETED_PDF)

                odt_info = info.get_file_type_info("odt")
                if odt_info is not None:
                    old_odt_info = old.worksheets[title].get_file_type_info('odt')
                    if old_odt_info is None:
                        change_log.add_change(title, ChangeType.NEW_ODT)
                    elif old_odt_info.timestamp < odt_info.timestamp:
                        change_log.add_change(title, ChangeType.UPDATED_ODT)
                elif old.worksheets[title].has_file_type('odt'):
                    change_log.add_change(title, ChangeType.DELETED_ODT)
                if info.version != old.worksheets[title].version:
                    # We don't check whether the new version is higher than the old one - maybe warn if not?
                    change_log.add_change(title, ChangeType.UPDATED_WORKSHEET)
            else:
                change_log.add_change(title, ChangeType.NEW_WORKSHEET)
        for worksheet in old.worksheets:
            if worksheet not in self.worksheets:
                change_log.add_change(worksheet, ChangeType.DELETED_WORKSHEET)

        return change_log

    def list_worksheets_with_missing_pdf(self) -> List[str]:
        """ Returns a list of worksheets which are translated but are missing the PDF"""
        return [worksheet for worksheet in self.worksheets if not self.worksheets[worksheet].has_file_type('pdf')]

    def list_incomplete_translations(self) -> List[WorksheetInfo]:
        return [info for _, info in self.worksheets.items() if info.is_incomplete()]

    def count_finished_translations(self) -> int:
        count: int = 0
        for worksheet_info in self.worksheets.values():
            if worksheet_info.has_file_type('pdf'):
                count += 1
        return count


def json_decode(data: Dict[str, Any]):
    """
    Deserializes a JSON-formatted string back into
    TranslationProgress / FileInfo / WorksheetInfo / LanguageInfo objects.
    @raises AssertionError if data is malformatted
    """
    if "file_type" in data:
        assert "url" in data and "timestamp" in data
        translation_unit: Optional[int] = int(data["translation_unit"]) if "translation_unit" in data else None
        return FileInfo(data["file_type"], data["url"], data["timestamp"], translation_unit)

    if "translated" in data:
        return TranslationProgress(**data)

    if "page" in data:
        assert "language_code" in data and "title" in data and "version" in data and "progress" in data
        assert isinstance(data["progress"], TranslationProgress)
        version_unit: Optional[int] = int(data["version_unit"]) if "version_unit" in data else None
        worksheet_info = WorksheetInfo(data["page"], data["language_code"], data["title"], data["progress"],
                                       data["version"], version_unit)
        if "files" in data:
            for file_info in data["files"]:
                assert isinstance(file_info, FileInfo)
                worksheet_info.add_file_info(file_info=file_info)
        return worksheet_info

    if "worksheets" in data:
        assert "language_code" in data
        assert "english_name" in data
        language_info = LanguageInfo(data["language_code"], data["english_name"])
        for worksheet in data["worksheets"]:
            assert isinstance(worksheet, WorksheetInfo)
            language_info.add_worksheet_info(worksheet.page, worksheet)
        return language_info

    return data


class DataStructureEncoder(json.JSONEncoder):
    """Serializes a LanguageInfo / WorksheetInfo / FileInfo / TranslationProgress object into a JSON string"""
    def default(self, obj):
        if isinstance(obj, LanguageInfo):
            return {
                "language_code": obj.language_code,
                "english_name": obj.english_name,
                "worksheets": list(obj.worksheets.values())
            }
        if isinstance(obj, WorksheetInfo):
            worksheet_json: Dict[str, Any] = {
                "page": obj.page,
                "language_code": obj.language_code,
                "title": obj.title,
                "version": obj.version,
                "progress": obj.progress
            }
            if obj.version_unit is not None:
                worksheet_json["version_unit"] = obj.version_unit
            file_infos: Dict[str, FileInfo] = obj.get_file_infos()
            if file_infos:
                worksheet_json["files"] = list(file_infos.values())
            return worksheet_json
        if isinstance(obj, FileInfo):
            file_json: Dict[str, Any] = {
                "file_type": obj.file_type,
                "url": obj.url,
                "timestamp": obj.timestamp.isoformat()
            }
            if obj.translation_unit is not None:
                file_json["translation_unit"] = obj.translation_unit
            return file_json
        if isinstance(obj, TranslationProgress):
            return {"translated": obj.translated, "fuzzy": obj.fuzzy, "total": obj.total}
        return super().default(obj)
