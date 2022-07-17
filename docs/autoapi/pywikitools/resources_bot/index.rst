:py:mod:`pywikitools.resources_bot`
===================================

.. py:module:: pywikitools.resources_bot

.. autoapi-nested-parse::

   Script to fill the "Available Resources in ..." sections of all languages

   This scripts scans through the worksheets and all their translations, saving also the links for PDF and ODT files.
   It checks if new translations were added and changes the language overview pages where necessary.
   It is supposed to run daily as a cronjob.

   Main steps:
       1. gather data: go through all worksheets and all their translations
          This will take quite some time as it is many API calls
       2. Update language overview pages where necessary
          For example: https://www.4training.net/German#Available_training_resources_in_German
          To make that easier, a JSON representation is saved for every language, e.g.
          https://www.4training.net/4training:de.json
          The script will compare its results to the JSON and update the JSON and the language overview page when necessary
       3. Post-processing (TODO: not yet implemented)
          With information like "we now have a Hindi translation of the Prayer worksheet" we can do helpful things, e.g.
          - update a zip file with all Hindi worksheets
          - send an email notification to all interested in the Hindi resources

   Command line options:
       --lang LANGUAGECODE: only look at this one language (significantly faster)
       -l, --loglevel: change logging level (standard: warning; other options: debug, info)
       --rewrite-all: Rewrite all language information pages
       --read-from-cache: Read from the JSON structure instead of querying the current status of all worksheets

   Logging:
       If configured in config.ini (see config.example.ini), output will be logged to three different files
       in three different verbosity levels (WARNING, INFO, DEBUG)

   Reports:
       We write language reports into the folder specified in config.ini
       (section Paths, variable languagereports)

   Examples:

   Only update German language information page with more logging
       python3 resourcesbot.py --lang de -l info

   Normal run (updating language information pages where necessary)
       python3 resourcesbot.py

   Run script completely without making any changes on the server:
   Best for understanding what the script does, but requires running via pywikibot pwb.py
       python3 pwb.py -simulate resourcesbot.py -l info

   This is only the wrapper script, all main logic is in resourcesbot/bot.py



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   pywikitools.resources_bot.parse_arguments
   pywikitools.resources_bot.set_loglevel



.. py:function:: parse_arguments() -> pywikitools.resourcesbot.bot.ResourcesBot

   Parses command-line arguments.
   @return: ResourcesBot instance


.. py:function:: set_loglevel(config: configparser.ConfigParser, loglevel: int)

   Setting up logging to three log files and to stdout.

   The file paths for the three log files (for each log level WARNING, INFO and DEBUG) are
   configured in the config.ini
   @param loglevel: logging.WARNING is standard, logging.INFO for more details, logging.DEBUG for a lot of output


