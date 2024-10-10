
"""Family file for connecting to 4training.net with pywikibot

This is intended to be used without using the traditional pywikibot approach
of using user-config.py for configuration.
Instead we use pywikibot short site creation (requires pywikibot >= 7.3)

However, if you still want to use the traditional approach, you could just take
this file, rename it to 4training_family.py and put in the right folder
(pywikibot families folder or some other folder that you specify with
user_families_paths in user-config.py).

Then use a user-config.py with the following configuration to connect to test.4training.net:
family = '4training'
mylang = 'test'
usernames['4training']['test'] = 'YourUserName'
"""
import pywikibot


class Family(pywikibot.family.SubdomainFamily):
    """
    The family class for our 4training.net website
    for connecting to it via pywikibot short site creation (new feature of pywikibot 7.3):
    No cumbersome user-config.py is necessary anymore, instead we can write
    family = Family()
    self.site = pywikibot.Site(code='test', fam=family, user='username')
    code can be either '4training' or 'test' to connect to www.4training.net / test.4training.net
    """
    name = '4training'

    domain = '4training.net'

    # Our live and test environments
    langs = {
        '4training': 'www.4training.net',
        'test': 'test.4training.net',
        'local': 'localhost:8082'
    }

    # this must have the same value as $wgScriptPath in LocalSettings.php of the mediawiki installation
    def scriptpath(self, code):
        return '/mediawiki'

    # TODO can be removed when upgrading to pywikibot ^8.2
    def protocol(self, code):
        if code == 'local':
            return 'http'
        return 'https'
