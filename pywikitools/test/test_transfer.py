from configparser import ConfigParser
import unittest
from unittest.mock import patch
import sys
from transfer import TransferTool
sys.path.append('../../')   # Is there a better way to do it?


class TestTransferTool(unittest.TestCase):
    @patch('pywikibot.Site', autospec=True)
    def setUp(self, mock_pywikibot_site):
        mock_pywikibot_site.return_value.logged_in.return_value = True
        config = ConfigParser()
        config.read_dict({"transfer": {"source_username": "User1",
                                       "source_site": "test",
                                       "destination_username": "User2",
                                       "destination_site": "local"}})
        self.transfer_tool = TransferTool(config)

    @patch('pywikibot.Page')
    def test_upload(self, mock_page):
        self.transfer_tool.upload("Test_Page/1/fr", "Test transfer")
        mock_page.return_value.save.assert_called_once_with(
            summary="Transfer of 'Test_Page/1/fr' from 'test' to 'local'")

    @patch('pywikibot.Page')
    def test_transfer(self, mock_page):
        self.transfer_tool.transfer("A_Daily_Prayer", "fr")
        mock_page.return_value.save.assert_called_with(
            summary="Transfer of 'A_Daily_Prayer/21/fr' from 'test' to 'local'")


if __name__ == "__main__":
    unittest.main()
