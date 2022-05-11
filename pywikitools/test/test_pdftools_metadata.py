from os.path import abspath, dirname, join
import unittest
from unittest.mock import patch, Mock, MagicMock

from pywikitools.pdftools.metadata import check_metadata
from pywikitools.resourcesbot.data_structures import TranslationProgress, WorksheetInfo
from pywikitools.test.test_data_structures import TEST_PROGRESS


class TestPdfMetadata(unittest.TestCase):
    @staticmethod
    def mock_get_language_name(language_code: str, target_language_code: str = None) -> str:
        """Mock fortraininglib.get_language_name() so that we don't have to do real API calls"""
        if language_code == "de":   # As we're testing with German examples we only need German currently
            if target_language_code == "en":
                return "German"
            return "Deutsch"
        return ""

    def setUp(self):
        progress = TranslationProgress(**TEST_PROGRESS)
        self.info_money = WorksheetInfo("Dealing_with_Money", "de", "Umgang mit Geld", progress, "1.0")
        self.info_hearing = WorksheetInfo("Hearing_from_God", "de", "Gottes Reden wahrnehmen", progress, "1.2")

    @patch("pywikitools.pdftools.metadata.pikepdf")
    def test_check_metadata(self, mock_pikepdf):
        fortraininglib = Mock()
        fortraininglib.get_language_name.side_effect = self.mock_get_language_name

        # A PDF document that has incorrect properties, stored only as DocInfo
        mock_meta = Mock()
        mock_meta.__bool__ = lambda x: False        # let our mock evaluate to False
        mock_meta.pdfa_status = ""
        mock_pikepdf.open.return_value.open_metadata.return_value = mock_meta
        mock_pikepdf.open.return_value.docinfo = {"/Title": "-", "/Subject": "-", "/Keywords": "-"}
        result = check_metadata(fortraininglib, "", self.info_money)
        self.assertEqual(result.version, "")
        self.assertFalse(result.correct)
        self.assertFalse(result.pdf1a)
        self.assertTrue(result.only_docinfo)
        self.assertEqual(len(result.warnings.split("\n")), 4)   # There should be four warnings

        # Same, but DocInfo properties are now correct
        mock_pikepdf.open.return_value.docinfo = {
            "/Title": self.info_money.title,
            # It would be nice if there two functions in our code give_me_subject() and give_me_keywords()
            "/Subject": f'{self.info_money.page.replace("_", " ")} German Deutsch',
            "/Keywords": "Copyright-free. More text. Version 1.2"
        }
        result = check_metadata(fortraininglib, "", self.info_money)
        self.assertTrue(result.correct)
        self.assertTrue(result.only_docinfo)

        # A PDF document that has correct properties stored as XMP and is PDF/1A
        mock_meta = MagicMock()
        mock_meta.pdfa_status = "1A"
        properties = {
            "dc:title": self.info_money.title,
            "dc:description": f'{self.info_money.page.replace("_", " ")} German Deutsch',
            "pdf:Keywords": "Copyright-free. More text. Version 1.2"
        }
        # This is all a bit tricky because our mocked object needs to support
        # both access by index: mock_meta["dc:title"] and access of a member: mock_meta.pdfa_status
        mock_meta.__getitem__.side_effect = properties.__getitem__
        mock_meta.__contains__.side_effect = properties.__contains__
        mock_pikepdf.open.return_value.open_metadata.return_value = mock_meta
        result = check_metadata(fortraininglib, "", self.info_money)
        self.assertEqual(result.version, "1.2")
        self.assertTrue(result.correct)
        self.assertTrue(result.pdf1a)
        self.assertFalse(result.only_docinfo)
        self.assertEqual(result.warnings, "")

    def test_real_examples(self):
        fortraininglib = Mock()
        fortraininglib.get_language_name.side_effect = self.mock_get_language_name

        # This PDF should meet all our standards
        file_path = join(dirname(abspath(__file__)), "data", "Umgang_mit_Geld.pdf")
        result = check_metadata(fortraininglib, file_path, self.info_money)
        self.assertTrue(result.pdf1a)
        self.assertTrue(result.correct)
        self.assertFalse(result.only_docinfo)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.warnings, "")

        # This PDF is a bit outdated: metadata is correct but it is stored in outdated docinfo
        file_path = join(dirname(abspath(__file__)), "data", "Gottes_Reden_wahrnehmen.pdf")
        result = check_metadata(fortraininglib, file_path, self.info_hearing)
        self.assertFalse(result.pdf1a)
        self.assertTrue(result.correct)
        self.assertTrue(result.only_docinfo)
        self.assertEqual(result.version, "1.2")
        self.assertEqual(result.warnings, "")


if __name__ == '__main__':
    unittest.main()
