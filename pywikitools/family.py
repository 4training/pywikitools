"""Family file for connecting to 4training.net with pywikibot

Bots connect via pywikibot short site creation (requires pywikibot >= 7.3) and
config.ini for site/username settings — no user-config.py needed:

    family = Family()
    self.site = pywikibot.Site(code='test', fam=family, user='username')

code can be
'4training' => www.4training.net
'test' => test.4training.net
'local' => localhost:8082
"""

import pywikibot


class Family(pywikibot.family.SubdomainFamily):
    """The family class for our 4training.net website."""

    name = "4training"

    domain = "4training.net"

    # Our live and test environments
    langs = {
        "4training": "www.4training.net",
        "test": "test.4training.net",
        "local": "localhost:8082",
    }

    # this must have the same value as $wgScriptPath in LocalSettings.php of the mediawiki installation
    def scriptpath(self, code):
        if code == "local":
            return "/mediawiki"
        return ""

    # TODO can be removed when upgrading to pywikibot ^8.2
    def protocol(self, code):
        if code == "local":
            return "http"
        return "https"
