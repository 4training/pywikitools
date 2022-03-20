"""
Test the different classes and functions of resourcesbot
Currently the different helper classes are tested well,
the ResourcesBot class itself isn't tested yet.

Run tests:
    python3 test_resourcesbot.py
"""
from base64 import decode
from datetime import datetime
from typing import Any, Dict
import unittest
import logging
import json
from pywikitools import fortraininglib
from pywikitools.resourcesbot.changes import ChangeType
from pywikitools.resourcesbot.data_structures import FileInfo, WorksheetInfo, LanguageInfo, WorksheetInfoEncoder, json_decode

# Currently in our json files it is stored as "2018-12-20T12:58:57Z"
# but datetime.fromisoformat() can't handle the "Z" in the end
# TEST_TIME = "2018-12-20T12:58:57Z".replace('Z', '+00:00')
TEST_TIME: str = "2018-12-20T12:58:57+00:00"

TEST_URL: str = "https://www.4training.net/mediawiki/images/7/70/Gottes_Reden_wahrnehmen.pdf"
# a different url
TEST_URL2: str = "https://www.4training.net/mediawiki/images/1/15/Gottes_Reden_wahrnehmen.pdf"

# An example translation progress (in the dict form returned by the mediawiki API)
TEST_PROGRESS: dict = {"total": 44, "translated": 44, "fuzzy": 0, "proofread": 0, "code": "de", "language": "de"}

TEST_EN_NAME: str = "Hearing from God"
TEST_LANG: str = "de"
TEST_TITLE: str = "Gottes Reden wahrnehmen"

class TestFileInfo(unittest.TestCase):
    def test_basic(self):
        file_info = FileInfo("pdf", TEST_URL, datetime.fromisoformat(TEST_TIME))
        self.assertEqual(str(file_info), f"pdf {TEST_URL} {TEST_TIME}")

    def test_with_invalid_timestamp(self):
        with self.assertLogs('pywikitools.resourcesbot.fileinfo', level='ERROR'):
            file_info = FileInfo("odg", TEST_URL, "2018-12-20-12-58-57")
        # the default timestamp should be old
        self.assertLess(file_info.timestamp, datetime.now())

    def test_serialization(self):
        # encode a FileInfo object to JSON and decode it again: Make sure the result is the same
        file_info = FileInfo("pdf", TEST_URL, datetime.fromisoformat(TEST_TIME))
        json_text = WorksheetInfoEncoder().encode(file_info)
        decoded_file_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsInstance(decoded_file_info, FileInfo)
        self.assertEqual(str(decoded_file_info), str(file_info))
        self.assertEqual(WorksheetInfoEncoder().encode(decoded_file_info), json_text)


class TestWorksheetInfo(unittest.TestCase):
    def setUp(self):
        progress = fortraininglib.TranslationProgress(**TEST_PROGRESS)
        self.worksheet_info = WorksheetInfo(TEST_EN_NAME, TEST_LANG, TEST_TITLE, progress)

    def test_add_file_info(self):
        self.worksheet_info.add_file_info(FileInfo("pdf", TEST_URL, TEST_TIME))
        self.assertTrue(self.worksheet_info.has_file_type("pdf"))
        self.assertFalse(self.worksheet_info.has_file_type("odt"))
        file_info = self.worksheet_info.get_file_type_info("pdf")
        self.assertIsNotNone(file_info)
        self.assertEqual(TEST_URL, file_info.url)
        self.assertEqual(TEST_TIME, file_info.timestamp.isoformat())
        self.assertEqual("pdf", file_info.file_type)

        # add_file_info() should accept "2018-12-20T12:58:57Z" as well
        test_time = TEST_TIME.replace('+00:00', 'Z')
        self.worksheet_info.add_file_info(FileInfo("odt", TEST_URL.replace(".pdf", ".odt"), test_time))
        self.assertTrue(self.worksheet_info.has_file_type("odt"))
        file_info = self.worksheet_info.get_file_type_info("odt")
        self.assertEqual(TEST_TIME, file_info.timestamp.isoformat())

        # subsequent calls should update the file information
        self.worksheet_info.add_file_info(FileInfo("pdf", TEST_URL2, test_time))
        file_info = self.worksheet_info.get_file_type_info("pdf")
        self.assertIsNotNone(file_info)
        self.assertEqual(TEST_URL2, file_info.url)
        self.assertEqual(len(self.worksheet_info.get_file_infos()), 2)

        # TODO add tests for call with from_pywikibot= (pywikibot.page.FileInfo)

    def test_add_file_info_errors(self):
        with self.assertLogs('pywikitools.resourcesbot.fileinfo', level='ERROR'):
            self.worksheet_info.add_file_info(FileInfo("odg", TEST_URL, "2018-12-20-12-58-57"))
        # TODO add tests for call with from_pywikibot= (pywikibot.page.FileInfo)

    def test_get_file_infos(self):
        expected_file_types = ["pdf", "odt"]
        self.test_add_file_info()
        self.assertEqual(list(self.worksheet_info.get_file_infos().keys()), expected_file_types)
        for file_type in expected_file_types:
            self.assertTrue(self.worksheet_info.has_file_type(file_type))

    def test_is_incomplete(self):
        self.assertFalse(self.worksheet_info.is_incomplete())

        # An incomplete translation (= almost finished)
        incomplete_raw_dict: dict = \
            {"total": 44, "translated": 40, "fuzzy": 2, "proofread": 0, "code": "ro", "language": "ro"}
        incomplete_progress = fortraininglib.TranslationProgress(**incomplete_raw_dict)
        incomplete_worksheet = WorksheetInfo(TEST_EN_NAME, "ro", "random", incomplete_progress)
        self.assertTrue(incomplete_worksheet.is_incomplete())

        # An unfinished translation: does not even count as incomplete and will be ignored by resourcesbot
        unfinished_raw_dict: dict = \
            {"total": 44, "translated": 20, "fuzzy": 2, "proofread": 0, "code": "ru", "language": "ru"}
        unfinished_progress = fortraininglib.TranslationProgress(**unfinished_raw_dict)
        unfinished_worksheet = WorksheetInfo(TEST_EN_NAME, "ru", "random", unfinished_progress)
        self.assertFalse(unfinished_worksheet.is_incomplete())

    def test_serialization(self):
        # encode a WorksheetInfo object to JSON and decode it again: Make sure the result is the same
        progress = fortraininglib.TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Prayer", TEST_LANG, "Gebet", progress)
        json_text = WorksheetInfoEncoder().encode(worksheet_info)
        decoded_worksheet_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsInstance(decoded_worksheet_info, WorksheetInfo)
        self.assertEqual(WorksheetInfoEncoder().encode(decoded_worksheet_info), json_text)

        # Now let's add two files and make sure serialization is still working correctly
        worksheet_info.add_file_info(FileInfo("pdf", TEST_URL, TEST_TIME))
        worksheet_info.add_file_info(FileInfo("odt", TEST_URL.replace(".pdf", ".odt"), TEST_TIME))
        json_text = WorksheetInfoEncoder().encode(worksheet_info)
        decoded_worksheet_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsInstance(decoded_worksheet_info, WorksheetInfo)
        self.assertEqual(len(decoded_worksheet_info.get_file_infos()), 2)
        self.assertEqual(WorksheetInfoEncoder().encode(decoded_worksheet_info), json_text)


class TestLanguageInfo(unittest.TestCase):
    def setUp(self):
        self.language_info: LanguageInfo = LanguageInfo(TEST_LANG)

    def test_basic_functionality(self):
        progress = fortraininglib.TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo(TEST_EN_NAME, TEST_LANG, TEST_TITLE, progress)
        self.assertEqual(self.language_info.language_code, TEST_LANG)
        self.language_info.add_worksheet_info(TEST_EN_NAME, worksheet_info)
        self.assertTrue(self.language_info.has_worksheet(TEST_EN_NAME))
        self.assertIsNotNone(self.language_info.get_worksheet(TEST_EN_NAME))

    def test_worksheet_has_type(self):
        self.test_basic_functionality()
        self.language_info.get_worksheet(TEST_EN_NAME).add_file_info(FileInfo("pdf", TEST_URL, TEST_TIME))
        self.assertTrue(self.language_info.worksheet_has_type(TEST_EN_NAME, 'pdf'))
        self.assertFalse(self.language_info.worksheet_has_type(TEST_EN_NAME, 'odt'))

    def test_serialization(self):
        """Testing the import/export functionality into JSON representation
        First encode LanguageInfo object into JSON,
        then decode from this JSON representation and check that the result is the same again
        """
        self.test_basic_functionality()
        self.language_info.get_worksheet(TEST_EN_NAME).add_file_info(FileInfo("pdf", TEST_URL, TEST_TIME))
        self.language_info.get_worksheet(TEST_EN_NAME).add_file_info(FileInfo("odt", TEST_URL2, TEST_TIME))
        progress = fortraininglib.TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Prayer", TEST_LANG, "Gebet", progress)
        self.language_info.add_worksheet_info("Prayer", worksheet_info)
        json_text = WorksheetInfoEncoder().encode(self.language_info)

        # Now decode again and check results
        decoded_language_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsNotNone(decoded_language_info)
        self.assertIsInstance(decoded_language_info, LanguageInfo)
        self.assertEqual(WorksheetInfoEncoder().encode(decoded_language_info), json_text)
        self.assertTrue(decoded_language_info.has_worksheet(TEST_EN_NAME))
        self.assertTrue(decoded_language_info.worksheet_has_type(TEST_EN_NAME, "odt"))

    def test_compare(self):
        # TODO: Have 2-3 real (more complex) examples that should cover all cases and test with them
        self.test_basic_functionality()
        basic_json = WorksheetInfoEncoder().encode(self.language_info)
        self.assertTrue(self.language_info.compare(self.language_info).is_empty())
        old_language_info = json.loads(WorksheetInfoEncoder().encode(self.language_info), object_hook=json_decode)
        self.assertTrue(self.language_info.compare(old_language_info).is_empty())

        # Add an ODT file
        self.language_info.worksheets[TEST_EN_NAME].add_file_info(FileInfo('odt', TEST_URL2, TEST_TIME))
        comparison = self.language_info.compare(old_language_info)
        self.assertFalse(comparison.is_empty())
        self.assertEqual(len(comparison.get_all_changes()), 1)
        self.assertEqual(comparison.get_all_changes().pop().change_type, ChangeType.NEW_ODT)

        # Add a worksheet
        self.language_info = json.loads(basic_json, object_hook=json_decode)
        progress = fortraininglib.TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Prayer", TEST_LANG, "Gebet", progress)
        self.language_info.add_worksheet_info("Prayer", worksheet_info)
        comparison = self.language_info.compare(old_language_info)
        self.assertEqual(len(comparison.get_all_changes()), 1)
        self.assertEqual(comparison.get_all_changes().pop().change_type, ChangeType.NEW_WORKSHEET)

    # TODO: Add tests for list_worksheets_with_missing_pdf(), list_incomplete_translations()
    # and count_finished_translations()
    # For meaningful tests we would need more complex examples as well (see compare())
    # TODO: add several json files with complex examples to repo and decode them here to run tests

class TestResourcesBot(unittest.TestCase):
    # use this to see logging messages (can be increased to logging.DEBUG)
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    unittest.main()
