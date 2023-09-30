import unittest
from unittest.mock import patch, Mock

from googletrans import Translator

import pywikibot
from autotranslate import TranslationTool, BASE_URL, TEXT_ENDPOINT, DEEPL_ENDPOINT


class TestTranslationTool(unittest.TestCase):

    def setUp(self):
        self.translator_tool = TranslationTool(BASE_URL, TEXT_ENDPOINT, DEEPL_ENDPOINT)

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
        result = self.translator_tool.translate_with_deepl_or_google("Hello", "fr")
        self.assertEqual(result, "Bonjour")

    @patch.object(pywikibot.Page, 'save')
    def test_upload_translation(self, mock_save):
        self.translator_tool.upload_translation("test_key", "Test translation", "Test_Page", "fr")
        mock_save.assert_called_once_with(summary="Automated translation upload")


if __name__ == "__main__":
    unittest.main()
