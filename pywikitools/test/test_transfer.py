from configparser import ConfigParser
import unittest
from unittest.mock import patch
import sys
from transfer import TransferTool

sys.path.append("../../")  # Is there a better way to do it?


class TestTransferTool(unittest.TestCase):
    @patch("pywikibot.Site", autospec=True)
    def setUp(self, mock_pywikibot_site):
        mock_pywikibot_site.return_value.logged_in.return_value = True
        config = ConfigParser()
        config.read_dict(
            {
                "transfer": {
                    "source_site": "test",
                    "destination_username": "User2",
                    "destination_site": "local",
                }
            }
        )
        self.transfer_tool = TransferTool(config)

    @patch("pywikibot.Page")
    def test_upload(self, mock_page):
        self.transfer_tool.upload("Test_Page/1/fr", "Test transfer")
        mock_page.return_value.save.assert_called_once()

    @patch("pywikibot.Page")
    def test_upload_with_message(self, mock_page):
        self.transfer_tool.upload("Test_Page/1/fr", "Test transfer", "Test")
        mock_page.return_value.save.assert_called_once_with(summary="Test")

    @patch("pywikibot.Page")
    def test_transfer(self, mock_page):
        self.transfer_tool.transfer("A_Daily_Prayer", "fr")
        mock_page.return_value.save.assert_called()

    @patch("pywikibot.Page")
    def test_upload_created(self, mock_page):
        mock_page.return_value.exists.return_value = False
        self.transfer_tool.upload("Test_Page/2/it", "Test transfer", "v1")
        self.assertEqual(self.transfer_tool.created, 1)
        self.assertEqual(self.transfer_tool.modified, 0)
        self.assertEqual(self.transfer_tool.unchanged, 0)

    @patch("pywikibot.Page")
    def test_upload_modified(self, mock_page):
        mock_page.return_value.exists.return_value = True
        mock_page.return_value.text.return_value = "Old entry"
        self.transfer_tool.upload("Test_Page/2/it", "New entry", "v4")
        self.assertEqual(self.transfer_tool.created, 0)
        self.assertEqual(self.transfer_tool.modified, 1)
        self.assertEqual(self.transfer_tool.unchanged, 0)


if __name__ == "__main__":
    unittest.main()
