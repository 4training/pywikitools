"""
Test the different classes and functions of resourcesbot
Currently the different helper classes are tested well,
the ResourcesBot class itself isn't tested yet.

Run tests:
    python3 test_resourcesbot.py
"""
from datetime import datetime
import unittest
import json
from os.path import abspath, dirname, join
from pywikitools.resourcesbot.changes import ChangeItem, ChangeType
from pywikitools.resourcesbot.data_structures import FileInfo, PdfMetadataSummary, TranslationProgress, WorksheetInfo, \
                                                     LanguageInfo, DataStructureEncoder, json_decode

# Currently in our json files it is stored as "2018-12-20T12:58:57Z"
# but datetime.fromisoformat() can't handle the "Z" in the end
# TEST_TIME = "2018-12-20T12:58:57Z".replace('Z', '+00:00')
TEST_TIME: str = "2018-12-20T12:58:57+00:00"

TEST_URL: str = "https://www.4training.net/mediawiki/images/7/70/Gottes_Reden_wahrnehmen.pdf"
# a different url
TEST_URL2: str = "https://www.4training.net/mediawiki/images/1/15/Gottes_Reden_wahrnehmen.pdf"

# Example translation progresses (in the dict form returned by the mediawiki API)
TEST_PROGRESS: dict = {"total": 44, "translated": 44, "fuzzy": 0, "proofread": 0, "code": "de", "language": "de"}
TEST_PROGRESS2: dict = {"total": 44, "translated": 10, "fuzzy": 5, "proofread": 0, "code": "de", "language": "de"}
TEST_PROGRESS3: dict = {"total": 44, "translated": 40, "fuzzy": 3, "proofread": 0, "code": "de", "language": "de"}

TEST_EN_NAME: str = "Hearing_from_God"
TEST_LANG: str = "de"
TEST_LANG_NAME: str = "German"
TEST_TITLE: str = "Gottes Reden wahrnehmen"
TEST_VERSION: str = "1.2"


class TestTranslationProgress(unittest.TestCase):
    def test_everything(self):
        is_incomplete = [False, False, True]
        is_unfinished = [False, True, False]
        for counter, progress_dict in enumerate([TEST_PROGRESS, TEST_PROGRESS2, TEST_PROGRESS3]):
            progress = TranslationProgress(**progress_dict)
            self.assertEqual(progress.fuzzy, progress_dict["fuzzy"])
            self.assertEqual(progress.total, progress_dict["total"])
            self.assertEqual(progress.translated, progress_dict["translated"])
            self.assertEqual(is_incomplete[counter], progress.is_incomplete())
            self.assertEqual(is_unfinished[counter], progress.is_unfinished())
            self.assertIn(str(progress.fuzzy), str(progress))
            self.assertIn(str(progress.translated), str(progress))
            self.assertIn(f"/{progress.total}", str(progress))


class TestPdfMetadataSummary(unittest.TestCase):
    def test_serialization(self):
        summary = PdfMetadataSummary("1.2", True, False, True, "Warnings")
        json_text = DataStructureEncoder().encode(summary)
        decoded_summary = json.loads(json_text, object_hook=json_decode)
        self.assertIsInstance(decoded_summary, PdfMetadataSummary)
        self.assertEqual(str(decoded_summary), str(summary))
        self.assertEqual(DataStructureEncoder().encode(decoded_summary), json_text)


class TestFileInfo(unittest.TestCase):
    def test_basic(self):
        file_info = FileInfo("pdf", TEST_URL, datetime.fromisoformat(TEST_TIME))
        self.assertEqual(str(file_info), f"pdf {TEST_URL} {TEST_TIME}")

    def test_get_file_name(self):
        file_info = FileInfo("pdf", TEST_URL, datetime.fromisoformat(TEST_TIME))
        self.assertEqual(file_info.get_file_name(), "Gottes_Reden_wahrnehmen.pdf")

    def test_with_invalid_timestamp(self):
        with self.assertLogs('pywikitools.resourcesbot.fileinfo', level='ERROR'):
            file_info = FileInfo("odg", TEST_URL, "2018-12-20-12-58-57")
        # the default timestamp should be old
        self.assertLess(file_info.timestamp, datetime.now())

    def test_serialization(self):
        # encode a FileInfo object to JSON and decode it again: Make sure the result is the same
        file_info = FileInfo("pdf", TEST_URL, datetime.fromisoformat(TEST_TIME))
        json_text = DataStructureEncoder().encode(file_info)
        decoded_file_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsInstance(decoded_file_info, FileInfo)
        self.assertEqual(str(decoded_file_info), str(file_info))
        self.assertEqual(DataStructureEncoder().encode(decoded_file_info), json_text)

        # encode a FileInfo object with translation_unit and metadata information
        summary = PdfMetadataSummary("1.2", True, False, True, "Warnings")
        file_info = FileInfo("pdf", TEST_URL, datetime.fromisoformat(TEST_TIME),
                             translation_unit=5, metadata=summary)
        json_text = DataStructureEncoder().encode(file_info)
        decoded_file_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsInstance(decoded_file_info, FileInfo)
        self.assertEqual(decoded_file_info.translation_unit, 5)
        self.assertTrue(decoded_file_info.metadata.correct)
        self.assertFalse(decoded_file_info.metadata.pdf1a)
        self.assertTrue(decoded_file_info.metadata.only_docinfo)
        self.assertEqual(decoded_file_info.metadata.version, "1.2")
        self.assertEqual(decoded_file_info.metadata.warnings, "Warnings")
        self.assertEqual(DataStructureEncoder().encode(decoded_file_info), json_text)

    def test_str(self):
        file_info = FileInfo("pdf", TEST_URL, datetime.fromisoformat(TEST_TIME))
        self.assertIn("pdf", str(file_info))
        self.assertIn(TEST_URL, str(file_info))
        self.assertIn(TEST_TIME, str(file_info))
        self.assertNotIn("(", str(file_info))
        self.assertNotIn(",", str(file_info))
        summary = PdfMetadataSummary("1.2", True, False, True, "Warnings")
        file_info2 = FileInfo("pdf", TEST_URL, datetime.fromisoformat(TEST_TIME), translation_unit=4, metadata=summary)
        self.assertTrue(str(file_info2).startswith(str(file_info)))
        self.assertIn("in translation unit: 4", str(file_info2))
        self.assertIn("metadata:", str(file_info2))


class TestWorksheetInfo(unittest.TestCase):
    def setUp(self):
        self.progress = TranslationProgress(**TEST_PROGRESS)
        self.worksheet_info = WorksheetInfo(TEST_EN_NAME, TEST_LANG, TEST_TITLE, self.progress, TEST_VERSION)

    def test_add_file_info(self):
        self.worksheet_info.add_file_info(FileInfo("pdf", TEST_URL, TEST_TIME))
        self.assertTrue(self.worksheet_info.has_file_type("pdf"))
        self.assertFalse(self.worksheet_info.has_file_type("odt"))
        self.assertEqual(self.worksheet_info.get_file_type_name("odt"), "")
        file_info = self.worksheet_info.get_file_type_info("pdf")
        self.assertIsNotNone(file_info)
        self.assertEqual(TEST_URL, file_info.url)
        self.assertEqual(TEST_TIME, file_info.timestamp.isoformat())
        self.assertEqual("pdf", file_info.file_type)
        self.assertEqual(self.worksheet_info.get_file_type_name("pdf"), "Gottes_Reden_wahrnehmen.pdf")

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
        self.assertEqual(self.worksheet_info.get_file_type_name("pdf"), "Gottes_Reden_wahrnehmen.pdf")

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

    def test_show_in_list(self):
        self.assertFalse(self.worksheet_info.show_in_list())
        self.test_add_file_info()
        self.assertTrue(self.worksheet_info.show_in_list())
        self.worksheet_info.progress.translated = 0
        self.assertFalse(self.worksheet_info.show_in_list())

    def test_is_incomplete(self):
        self.assertFalse(self.worksheet_info.is_incomplete())

        # An incomplete translation (= almost finished)
        incomplete_progress = TranslationProgress(**TEST_PROGRESS3)
        incomplete_worksheet = WorksheetInfo(TEST_EN_NAME, "ro", "random", incomplete_progress, TEST_VERSION)
        self.assertTrue(incomplete_worksheet.is_incomplete())

        # An unfinished translation: does not even count as incomplete and will be ignored by resourcesbot
        unfinished_progress = TranslationProgress(**TEST_PROGRESS2)
        unfinished_worksheet = WorksheetInfo(TEST_EN_NAME, "ru", "random", unfinished_progress, TEST_VERSION)
        self.assertFalse(unfinished_worksheet.is_incomplete())

    def test_serialization(self):
        # encode a WorksheetInfo object to JSON and decode it again: Make sure the result is the same
        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Prayer", TEST_LANG, "Gebet", progress, "TEST_VERSION")
        json_text = DataStructureEncoder().encode(worksheet_info)
        decoded_worksheet_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsInstance(decoded_worksheet_info, WorksheetInfo)
        self.assertEqual(DataStructureEncoder().encode(decoded_worksheet_info), json_text)

        # Now let's add two files and make sure serialization is still working correctly
        worksheet_info.add_file_info(FileInfo("pdf", TEST_URL, TEST_TIME))
        worksheet_info.add_file_info(FileInfo("odt", TEST_URL.replace(".pdf", ".odt"), TEST_TIME))
        worksheet_info.add_file_info(FileInfo("printPdf", TEST_URL.replace(".pdf", "_print.pdf"), TEST_TIME))
        json_text = DataStructureEncoder().encode(worksheet_info)
        decoded_worksheet_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsInstance(decoded_worksheet_info, WorksheetInfo)
        self.assertEqual(len(decoded_worksheet_info.get_file_infos()), 3)
        self.assertEqual(DataStructureEncoder().encode(decoded_worksheet_info), json_text)

    def test_to_str(self):
        self.test_add_file_info()
        for file_type, file_info in self.worksheet_info.get_file_infos().items():
            self.assertIn(f"{file_type} {file_info.url}", str(self.worksheet_info))
        self.assertIn(self.worksheet_info.title, str(self.worksheet_info))
        self.assertNotIn("translation unit", str(self.worksheet_info))
        progress = TranslationProgress(**TEST_PROGRESS)
        with_unit = WorksheetInfo(TEST_EN_NAME, TEST_LANG, TEST_TITLE, progress, TEST_VERSION, "2")
        self.assertIn("translation unit", str(with_unit))

    def test_has_same_version(self):
        english_info = WorksheetInfo(TEST_EN_NAME, "en", TEST_EN_NAME, self.progress, TEST_VERSION)
        self.assertTrue(self.worksheet_info.has_same_version(english_info))
        self.worksheet_info.version = "1.2b"
        self.assertTrue(self.worksheet_info.has_same_version(english_info))
        self.worksheet_info.version = "1.3a"
        self.assertFalse(self.worksheet_info.has_same_version(english_info))
        tamil_info = WorksheetInfo(TEST_EN_NAME, "ta", "கர்த்தரிடமிருந்து கேட்பது", self.progress, "௧.௨")
        self.assertTrue(tamil_info.has_same_version(english_info))
        tamil_info.version = "௧.௦"
        self.assertFalse(tamil_info.has_same_version(english_info))
        kannada_info = WorksheetInfo(TEST_EN_NAME, "kn", "ದೇವರಿಂದ ಕೇಳುವುದು", self.progress, "೧.೨")
        self.assertTrue(kannada_info.has_same_version(english_info))
        kannada_info.version = "೧.೦"
        self.assertFalse(kannada_info.has_same_version(english_info))
        hindi_info = WorksheetInfo(TEST_EN_NAME, "hi", "परमेश्वर के साथ का समय", self.progress, "१.२")
        self.assertTrue(hindi_info.has_same_version(english_info))
        hindi_info.version = "१.०"
        self.assertFalse(hindi_info.has_same_version(english_info))


class TestLanguageInfo(unittest.TestCase):
    def setUp(self):
        self.language_info: LanguageInfo = LanguageInfo(TEST_LANG, TEST_LANG_NAME)

    def test_basic_functionality(self):
        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo(TEST_EN_NAME, TEST_LANG, TEST_TITLE, progress, TEST_VERSION)
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
        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Prayer", TEST_LANG, "Gebet", progress, TEST_VERSION)
        self.language_info.add_worksheet_info("Prayer", worksheet_info)
        json_text = DataStructureEncoder().encode(self.language_info)

        # Now decode again and check results
        decoded_language_info = json.loads(json_text, object_hook=json_decode)
        self.assertIsNotNone(decoded_language_info)
        self.assertIsInstance(decoded_language_info, LanguageInfo)
        self.assertEqual(DataStructureEncoder().encode(decoded_language_info), json_text)
        self.assertEqual(decoded_language_info.language_code, TEST_LANG)
        self.assertEqual(decoded_language_info.english_name, TEST_LANG_NAME)
        self.assertTrue(decoded_language_info.has_worksheet(TEST_EN_NAME))
        self.assertTrue(decoded_language_info.worksheet_has_type(TEST_EN_NAME, "odt"))

    def test_basic_comparison(self):
        self.test_basic_functionality()
        basic_json = DataStructureEncoder().encode(self.language_info)
        self.assertTrue(self.language_info.compare(self.language_info).is_empty())
        old_language_info = json.loads(DataStructureEncoder().encode(self.language_info), object_hook=json_decode)
        self.assertTrue(self.language_info.compare(old_language_info).is_empty())

        # Add an ODT file
        self.language_info.worksheets[TEST_EN_NAME].add_file_info(FileInfo('odt', TEST_URL2, TEST_TIME))
        comparison = self.language_info.compare(old_language_info)
        self.assertFalse(comparison.is_empty())
        self.assertEqual(comparison.count_changes(), 1)
        self.assertEqual(next(iter(comparison)).change_type, ChangeType.NEW_ODT)

        # Add a worksheet
        self.language_info = json.loads(basic_json, object_hook=json_decode)
        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Prayer", TEST_LANG, "Gebet", progress, TEST_VERSION)
        self.language_info.add_worksheet_info("Prayer", worksheet_info)
        comparison = self.language_info.compare(old_language_info)
        self.assertEqual(comparison.count_changes(), 1)
        self.assertEqual(next(iter(comparison)).change_type, ChangeType.NEW_WORKSHEET)


class TestLanguageInfoComparison(unittest.TestCase):
    """Testing all the different possible outcomes of comparing two LanguageInfo objects"""
    def setUp(self):
        with open(join(dirname(abspath(__file__)), "data", "ru.json"), 'r') as f:
            self.language_info = json.load(f, object_hook=json_decode)
        self.assertIsInstance(self.language_info, LanguageInfo)

    def test_added_files(self):
        with open(join(dirname(abspath(__file__)), "data", "ru_added_files.json"), 'r') as f:
            language_info2 = json.load(f, object_hook=json_decode)
        self.assertIsInstance(language_info2, LanguageInfo)
        changes = set([change_item for change_item in language_info2.compare(self.language_info)])
        self.assertSetEqual(changes, set([ChangeItem("Church", ChangeType.NEW_PDF),
                                          ChangeItem("Healing", ChangeType.NEW_ODT),
                                          ChangeItem("Hearing_from_God", ChangeType.NEW_ODT),
                                          ChangeItem("Hearing_from_God", ChangeType.NEW_PDF)]))

    def test_deleted_files(self):
        with open(join(dirname(abspath(__file__)), "data", "ru_deleted_files.json"), 'r') as f:
            language_info2 = json.load(f, object_hook=json_decode)
        self.assertIsInstance(language_info2, LanguageInfo)
        changes = set([change_item for change_item in language_info2.compare(self.language_info)])
        self.assertSetEqual(changes, set([ChangeItem("Church", ChangeType.DELETED_ODT),
                                          ChangeItem("Healing", ChangeType.DELETED_PDF)]))

    def test_deleted_worksheet(self):
        with open(join(dirname(abspath(__file__)), "data", "ru_deleted_worksheet.json"), 'r') as f:
            language_info2 = json.load(f, object_hook=json_decode)
        self.assertIsInstance(language_info2, LanguageInfo)
        changes = set([change_item for change_item in language_info2.compare(self.language_info)])
        # If a worksheet with files gets deleted, only one DELETED_WORKSHEET change item should be emitted
        # (no DELETED_PDF and DELETED_ODT items as well)
        self.assertSetEqual(changes, set([ChangeItem("Prayer", ChangeType.DELETED_WORKSHEET),
                                          ChangeItem("My_Story_with_God", ChangeType.DELETED_WORKSHEET)]))

    def test_new_worksheet(self):
        with open(join(dirname(abspath(__file__)), "data", "ru_new_worksheet.json"), 'r') as f:
            language_info2 = json.load(f, object_hook=json_decode)
        self.assertIsInstance(language_info2, LanguageInfo)
        changes = set([change_item for change_item in language_info2.compare(self.language_info)])
        # If a new worksheet together with files get added, only one NEW_WORKSHEET change item should be emitted
        # (no NEW_PDF and NEW_ODT as well)
        self.assertSetEqual(changes, set([ChangeItem("Confessing_Sins_and_Repenting", ChangeType.NEW_WORKSHEET),
                                          ChangeItem("Forgiving_Step_by_Step", ChangeType.NEW_WORKSHEET)]))

    def test_updated_files(self):
        with open(join(dirname(abspath(__file__)), "data", "ru_updated_files.json"), 'r') as f:
            language_info2 = json.load(f, object_hook=json_decode)
        self.assertIsInstance(language_info2, LanguageInfo)
        changes = set([change_item for change_item in language_info2.compare(self.language_info)])
        self.assertSetEqual(changes, set([ChangeItem("Church", ChangeType.UPDATED_ODT),
                                          ChangeItem("Healing", ChangeType.UPDATED_PDF)]))

    def test_updated_worksheet(self):
        with open(join(dirname(abspath(__file__)), "data", "ru_updated_worksheet.json"), 'r') as f:
            language_info2 = json.load(f, object_hook=json_decode)
        self.assertIsInstance(language_info2, LanguageInfo)
        changes = set([change_item for change_item in language_info2.compare(self.language_info)])
        self.assertSetEqual(changes, set([ChangeItem("Hearing_from_God", ChangeType.UPDATED_WORKSHEET),
                                          ChangeItem("Church", ChangeType.UPDATED_WORKSHEET)]))

    # TODO: Add tests for list_worksheets_with_missing_pdf(), list_incomplete_translations()
    # and count_finished_translations()


if __name__ == '__main__':
    unittest.main()
