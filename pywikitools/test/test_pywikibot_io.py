import unittest
from unittest.mock import Mock, patch

from pywikitools.pywikibot_io import save_page


class TestSavePage(unittest.TestCase):
    @patch("pywikibot.showDiff")
    def test_shows_diff_in_simulate_mode(self, mock_show_diff):
        page = Mock()
        page.text = "old"
        page.title.return_value = "German"

        save_page(page, "new", "summary", simulate=True)

        mock_show_diff.assert_called_once_with("old", "new")
        self.assertEqual(page.text, "old")
        page.save.assert_not_called()

    @patch("pywikibot.showDiff")
    def test_no_diff_when_not_simulating(self, mock_show_diff):
        page = Mock()
        page.text = "old"
        page.title.return_value = "German"

        save_page(page, "new", "summary", simulate=False)

        mock_show_diff.assert_not_called()
        page.save.assert_called_once_with("summary")


if __name__ == "__main__":
    unittest.main()
