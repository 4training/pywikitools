"""
4training.net library

Contains common functions, many of wrapping API calls
We didn't name this 4traininglib.py because starting a python file name with a number causes problems
"""
import logging
import re
from typing import List, Optional, Dict

import requests

BASEURL: str = "https://www.4training.net"
APIURL: str = BASEURL + "/mediawiki/api.php"
logger = logging.getLogger('4training.lib')
# Language codes of all right-to-left languages we currently have
RTL_LANGUAGES = ["ar", "fa", "ckb", "ar-urdun", "ps", "ur"]


class TranslationProgress:
    def __init__(self, translated, fuzzy, total, **kwargs):
        """
        The constructor can take a dictionary as returned when doing a translation progress query:
        { "total": 44, "translated": 44, "fuzzy": 0, "proofread": 0, "code": "de", "language": "de" },
        from https://www.4training.net/mediawiki/api.php?action=query&meta=messagegroupstats&mgsgroup=page-Church
        """
        self.translated = int(translated)
        self.fuzzy = int(fuzzy)
        self.total = int(total)

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
        A translation is incomplete if it is not unfinished but still there is at least
        one translation unit which is neither translated nor fuzzy
        """
        if self.is_unfinished():
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


def get_worksheet_list() -> List[str]:
    """
    Returns the list of all worksheets. For now hard-coded as this doesn't change very often. Could be changed to
    retrieve that information from the backend.
    @param: -
    @return: worksheet_list (list): List of all worksheets.
    """
    return [
        "God's_Story_(five_fingers)", "God's_Story_(first_and_last_sacrifice)",
        "Baptism", "Prayer", "Forgiving_Step_by_Step", "Confessing_Sins_and_Repenting",
        "Time_with_God", "Hearing_from_God", "Church", "Healing",
        "My_Story_with_God", "Bible_Reading_Hints",
        "Bible_Reading_Hints_(Seven_Stories_full_of_Hope)",
        "Bible_Reading_Hints_(Starting_with_the_Creation)",
        "The_Three-Thirds_Process", "Training_Meeting_Outline", "A_Daily_Prayer",
        "Overcoming_Fear_and_Anger", "Getting_Rid_of_Colored_Lenses", "Family_and_our_Relationship_with_God",
        "Overcoming_Negative_Inheritance",
        "Forgiving_Step_by_Step:_Training_Notes", "Leading_Others_Through_Forgiveness",
        "The_Role_of_a_Helper_in_Prayer", "Leading_a_Prayer_Time",
        "How_to_Continue_After_a_Prayer_Time", "Four_Kinds_of_Disciples"]


def get_file_types() -> List[str]:
    """
    Returns the supported file types.
    @param: -
    @return: file_types (list): list of supported file types
    """
    return ['pdf', 'odt', 'odg']


def get_language_direction(languagecode: str) -> str:
    """ Returns language direction 'rtl' or 'ltr'
    This is hard-coded here.
    It is possible to request this from the mediawiki API e.g. with
    https://www.4training.net/mediawiki/api.php?action=query&titles=Prayer/ckb&prop=info
    but this has the cost of an extra API call...
    """
    if languagecode in RTL_LANGUAGES:
        return "rtl"
    return "ltr"


def get_language_name(language_code: str, translate_to: Optional[str] = None) -> Optional[str]:
    """ Returns the name of a language as either the autonym or translated into another language
    This function is calling the mediawiki {{#language:}} parser function and does no additional checks
    See https://www.mediawiki.org/wiki/Help:Magic_words#Miscellaneous
    Examples:
        get_language_name('de') = 'Deutsch'
        get_language_name('de','en') = 'German'
        get_language_name('nonsense') = 'nonsense' FYI
    @param language_code: identifies the language we're interested in
    @param translate_to: optional target language the language name should be translated into (None returns autonym)
    @return Language name if successful
    @return None in case of error
    """
    lang_parameter: str = language_code
    if isinstance(translate_to, str):
        lang_parameter += '|' + translate_to
    response = requests.get(APIURL, params={
        'action': 'parse',
        'text': '{{#language:' + lang_parameter + '}}',
        'contentmodel': 'wikitext',
        'format': 'json',
        'prop': 'text',
        'disablelimitreport': 'true'})
    try:
        langname = re.search('<p>([^<]*)</p>', response.json()['parse']['text']['*'], re.MULTILINE)
        if langname:
            return langname.group(1).strip()
        return None
    except KeyError:
        return None


def get_file_url(filename: str):
    """ Return the full URL of the requested file

    @return string with the URL or None in case of an error
    """
    # request url for downloading odt-file
    parameters = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "titles": "File:" + filename,
        "iiprop": "url"
    }

    response_url = requests.get(APIURL, params=parameters)
    logger.info("Retrieving URL of file " + filename + "... " + str(response_url.status_code))
    url_json = response_url.json()
    logger.debug(url_json)

    # check if there is only one page in the answer and get its name
    if len(list(url_json["query"]["pages"])) == 1:
        page_number = list(url_json["query"]["pages"])[0]
    else:
        logger.warning(F"fortraininglib:get_file_url: Couldn't get URL of file {filename}: multiple pages detected")
        return None

    if int(page_number) == -1:
        logger.info(F"fortraininglib:get_file_url: file {filename} doesn't seem to exist.")
        return None
    return url_json["query"]["pages"][page_number]["imageinfo"][0]["url"]


def get_page_content(page: str) -> Optional[str]:
    """
    Return the wikitext (source) of a page
    @return None on error
    """
    response = requests.get(APIURL, params={
        "action": "query",
        "prop": "revisions",
        "rvlimit": "1",
        "rvprop": "content",
        "format": "json",
        "titles": page})
    try:
        pageid = next(iter(response.json()["query"]["pages"]))
        return response.json()["query"]["pages"][pageid]['revisions'][0]['*']
    except KeyError:
        return None


def get_pdf_name(worksheet: str, languagecode: str):
    """ returns the name of the PDF associated with that worksheet translated into a specific language
    @return None in case we didn't find it
    """
    # we need to retrieve the page source of the English original and scan it for the name of the PDF file
    content = get_page_content(worksheet)
    if not content:
        return None
    # We have the page source, scan it for the PDF file name now
    pdfdownload = re.search('{{PdfDownload[^}]*}', content)
    if not pdfdownload:
        return None
    pdffile = re.search(r'[^ \n>]+\.pdf', pdfdownload.group())
    if not pdffile:
        return None
    if languagecode == 'en':    # we're already done
        return pdffile.group()
    translation_unit: int = 0   # the number of the translation unit containing the name of the PDF file
    search_tu = re.search(r'--T:(\d+)--', pdfdownload.group())
    if search_tu:
        translation_unit = int(search_tu.group(1))
    if translation_unit == 0:
        logger.warning("Couldn't find number of translation unit containing the PDF file name")
        return None

    # now we just need to look up the translation of this translation unit
    return get_page_content(f"Translations:{worksheet}/{translation_unit}/{languagecode}")


def list_page_translations(page: str, include_unfinished=False) -> Dict[str, TranslationProgress]:
    """ Returns all the existing translations of a page
    @param page the worksheet name
    @param include_unfinished whether unfinished translations should also be included

    Example: https://www.4training.net/mediawiki/api.php?action=query&meta=messagegroupstats&mgsgroup=page-Church
    @return a dictionary of language codes -> TranslationProgress objects
            In case no other translation exists the result will be {'en': progress object}
            In case of an error the map will be empty {}
            if you're not interested in the unfinished translations, you're probably only interested in the keys
    """
    counter = 1
    while counter < 4:
        # Tricky: Often we need to run this query for a second time so that all data is gathered.
        response = requests.get(APIURL, params={
            'action': 'query',
            'meta': 'messagegroupstats',
            'format': 'json',
            'mgsgroup': 'page-' + page})
        logger.info(f"Retrieving translation information of {page}, try #{counter}. Response: {response.status_code}")
        json = response.json()

        if 'continue' not in json:  # Now we have a complete response
            break
        counter += 1
    if ('continue' in json) or (counter == 4):
        logger.warning(f"Error while trying to get all translations of {page} - tried 3 times, still no result")
        return {}

    available_translations: Dict[str, TranslationProgress] = {}     # map of language codes to the translation progress
    try:
        for line in json['query']['messagegroupstats']:
            if line['translated'] > 0:
                # Definition: a translation is unfinished if more than 4 units are neither translated nor fuzzy
                progress = TranslationProgress(**line)
                if not progress.is_unfinished() or include_unfinished:
                    available_translations[line['language']] = progress
    except KeyError:
        return {}

    return available_translations


def list_page_templates(page: str) -> List[str]:
    """ Returns list of templates that are transcluded by a given page
    Strips potential language code at the end of a template (e.g. returns 'Template:Italic', not 'Template:Italic/en')
    See also https://translatewiki.net/w/api.php?action=help&modules=query%2Btemplates
    Example: https://www.4training.net/mediawiki/api.php?action=query&format=json&titles=Polish&prop=templates
    @return empty list in case of an error
    """
    response = requests.get(APIURL, params={
        'action': 'query',
        'format': 'json',
        'titles': page,
        'prop': 'templates'})
    json = response.json()
    try:
        if len(list(json["query"]["pages"])) == 1:
            pageid = list(json["query"]["pages"])[0]
        else:
            logger.warning("fortraininglib:list_page_templates: Error, multiple pages detected")
            return []
        result = []
        for line in json['query']['pages'][pageid]['templates']:
            if 'title' in line:
                language_code = line['title'].find('/')
                if language_code == -1:
                    result.append(line['title'])
                else:
                    result.append(line['title'][0:language_code])
        return result
    except KeyError:
        return []


def get_translation_units(worksheet: str, languagecode: str):
    """
    List the translation units of worksheet translated into the language identified by languagecode
    Example: https://www.4training.net/mediawiki/api.php?action=query&format=json&list=messagecollection&mcgroup=page-Forgiving_Step_by_Step&mclanguage=de
    @return if successful than returns the structure as is in response.json()["query"]["messagecollection"]
    @return on error: returns string with error message
    """
    response = requests.get(APIURL, params={
        "action": "query",
        "format": "json",
        "list": "messagecollection",
        "mcgroup": "page-" + worksheet,
        "mclanguage": languagecode,
    })

    logger.info(f"Retrieving translation of {worksheet} into language {languagecode}... {response.status_code}")
    json = response.json()
    if "error" in json:
        if "info" in json["error"]:
            return f"Couldn't get translation units. Error: {json['error']['info']}"
        return "Couldn't get translation units. Strange error."
    if "query" not in json:
        return "Couldn't get translation units. Some serious error"
    if "messagecollection" not in json["query"]:
        return "Couldn't get translation units. Unexpected error."
    return json["query"]["messagecollection"]


def title_to_message(title: str) -> str:
    """Converts a mediawiki title to its corresponding system message
    Examples:
        Prayer -> sidebar-prayer
        Forgiving_Step_by_Step -> sidebar-forgivingstepbystep
        The_Three-Thirds_Process -> sidebar-thethreethirdsprocess
        God's_Story_(five_fingers) -> sidebar-godsstory-fivefingers
    """
    ret = title.replace("-", '')
    ret = ret.replace('_(', '-')
    ret = ret.replace(')', '')
    ret = ret.replace("'", '')
    ret = ret.replace("_", '')
    ret = ret.replace(':', '')
    ret = ret.lower()
    return 'sidebar-' + ret


def expand_template(raw_template: str) -> str:
    """
    TODO more documentation
    https://www.4training.net/mediawiki/api.php?action=expandtemplates&text={{CC0Notice/de|1.3}}&prop=wikitext&format=json
    """
    response = requests.get(APIURL, params={
        "action": "expandtemplates",
        "text": raw_template,
        "prop": "wikitext",
        "format": "json"})
    if "expandtemplates" in response.json():
        if "wikitext" in response.json()["expandtemplates"]:
            return response.json()["expandtemplates"]["wikitext"]
    logger.warning(f"Warning: couldn't expand template {raw_template}")
    return ""


def get_cc0_notice(version: str, languagecode: str) -> str:
    """
    Returns the translated CC0 notice (https://www.4training.net/Template:CC0Notice)
    @param version Version number to put in
    @param languagecode Which language to translate it
    @return The translated notice (for footers in worksheets)
    @return string with a TODO in case the translation doesn't exist
    """
    expanded = expand_template("{{CC0Notice/" + languagecode + "|" + version + "}}")
    if "mw-translate-fuzzy" in expanded:
        logger.warning("Warning: Template:CC0Notice doesn't seem to be correctly translated into this language. "
                       "Please check https://www.4training.net/Template:CC0Notice")
    if "Template:CC0Notice" in expanded:
        logger.warning("Warning: Template:CC0Notice doesn't seem to be translated into this language. "
                       "Please translate https://www.4training.net/Template:CC0Notice")
        return "TODO translate https://www.4training.net/Template:CC0Notice"
    return expanded


def mark_for_translation(title: str, user_name: str, password: str):
    """
    Mark a page for translation

    Unfortunately this functionality is not exposed in the API yet. (See https://phabricator.wikimedia.org/T235397)
    Also pywikibot doesn't support calling anything outside the API
    So we need to log in on our own and call Special:PageTranslation in the necessary way:
    1. GET https://www.4training.net/mediawiki/index.php?title=Special:PageTranslation&target=Afrikaans&do=mark
    2. scrape the answer: we need the content of the hidden input fields
    3. POST https://www.4training.net/Special:PageTranslation (with some data)
    @param title The title of the page that should be marked for translation
    @todo currently it's always marking the page for translation, even if there are no changes -> add check
    @todo better error handling, return if we were successful
    """
    try:
        session = requests.Session()
        # We need a token in order to log in
        response = session.get(APIURL, params={
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json"
        })

        # Now we log in (see also https://www.mediawiki.org/wiki/API:Login )
        session.post(APIURL, data={
            'action': 'login',
            'lgname': user_name,
            'lgpassword': password,
            'lgtoken': response.json()["query"]["tokens"]["logintoken"]
        })

        # First step of marking a page for translation
        response = session.get("https://www.4training.net/mediawiki/index.php", params={
            "title": "Special:PageTranslation",
            "target": title,
            "do": "mark"})

        # scrape the result for the hidden input values we need
        pattern = re.compile('<input type="hidden" value="([^"]*)" name="([^"]*)"')
        hidden_inputs: Dict[str, str] = {}
        for m in pattern.finditer(response.text):
            hidden_inputs[m.group(2)] = m.group(1)

        # Now we can mark the page for translation
        session.post("https://www.4training.net/Special:PageTranslation", data={
            "do": "mark",
            "title": "Special:PageTranslation",
            "translatetitle": 1,
            "revision": hidden_inputs["revision"],
            "target": hidden_inputs["target"],
            "token": hidden_inputs["token"]
        })
    except KeyError as error:
        logger.warning(f"mark_for_translation failed: KeyError, no key named {error}")


# Other possibly relevant API calls:
# https://www.4training.net/mediawiki/api.php?action=query&meta=messagetranslations&mttitle=Translations:Church/44
# Is equivalent to https://www.4training.net/Special:Translations?message=Church%2F44&namespace=1198
# Directly lists all translations of one specific translation unit
