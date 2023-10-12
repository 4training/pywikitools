from configparser import ConfigParser
import unittest
from unittest.mock import patch, Mock
from googletrans import Translator
import sys
sys.path.append('../../')   # Is there a better way to do it?
from autotranslate import TranslationTool   # noqa: E402


class TestTranslationTool(unittest.TestCase):
    @patch('pywikibot.Site', autospec=True)
    def setUp(self, mock_pywikibot_site):
        mock_pywikibot_site.return_value.logged_in.return_value = True
        config = ConfigParser()
        config.read_dict({"autotranslate": {"site": "test", "username": "Test",
                                            "deeplendpoint": "endpoint", "deeplapikey": "apikey"}})
        self.translator_tool = TranslationTool(config)

    @patch('requests.post')
    def test_translate_with_deepl_successful(self, mock_post):
        # Mock the response from the DEEPL_ENDPOINT
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'translations': [{'text': 'Bonjour'}]
        }
        mock_post.return_value = mock_response

        # Test
        result = self.translator_tool.translate_with_deepl_or_google("Hello", "fr")
        self.assertEqual(result, "Bonjour")

    @patch('requests.post')
    @patch.object(Translator, 'translate')
    def test_translate_with_google_fallback(self, mock_translate, mock_post):
        # Mock the response from the DEEPL_ENDPOINT to return an error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        # Mock the Google Translate call
        mock_translate.return_value = Mock(text="Bonjour")

        # Test
        with self.assertLogs('pywikitools.autotranslate', level='WARNING'):
            result = self.translator_tool.translate_with_deepl_or_google("Hello", "fr")
        self.assertEqual(result, "Bonjour")

    @patch('pywikibot.Page')
    def test_upload_translation(self, mock_page):
        self.translator_tool.upload_translation("Test_Page/1/fr", "Test translation")
        mock_page.return_value.save.assert_called_once_with(summary="Automated translation by DeepL")


if __name__ == "__main__":
    unittest.main()
