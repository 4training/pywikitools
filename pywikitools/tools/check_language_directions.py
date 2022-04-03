"""
Little script to check whether fortraininglib.get_language_direction()
is correct for all the languages in use. It does so by doing API calls like
https://www.4training.net/mediawiki/api.php?action=query&titles=Start/fa&prop=info
It doesn't matter which page is requested - the language direction is always returned,
also if the page doesn't exist.

Also we don't include this script in the test suite because it takes maybe a minute and increases
test run time too much - it's sufficient to run it once in a while to check correctness.
"""
import json
from pywikitools import fortraininglib

language_list = json.loads(fortraininglib.get_page_source("4training:languages.json"))
counter: int = 0
warning: int = 0
for lang in language_list:
    counter += 1
    json = fortraininglib._get({"action": "query", "titles": f"Start/{lang}", "prop": "info", "format": "json"})
    page_number = list(json["query"]["pages"])[0]
    direction_api = json["query"]["pages"][page_number]["pagelanguagedir"]
    direction_lib = fortraininglib.get_language_direction(lang)
    if direction_api != direction_lib:
        warning += 1
        print(f"WARNING: fortraininglib.get_language_direction({lang}) returns incorrect result.")

print(f"Checked {counter} languages, {warning} warnings.")
