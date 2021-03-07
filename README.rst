======================
Python Mediawiki Tools
======================

Python tools for mediawiki with the Translate plugin (some based on pywikibot).
Used for https://www.4training.net but hopefully more projects will benefit from it.
That's why currently it's focusing a lot on 4training.net but our plan is
to make it more generic.

* Free software: GNU General Public License v3

.. NOT YET * Documentation: https://pywikitools.readthedocs.io.

See https://github.com/orgs/4training/projects/1 for the project roadmap

| The tools use the mediawiki API. URL and all documentation:
  https://www.4training.net/mediawiki/api.php
| Read-only scripts make direct use of the API calls. Bots writing to
  the system use the pywikibot framework:
  https://www.mediawiki.org/wiki/Manual:Pywikibot

Pywikibot setup:
----------------

1. Install it, following
   https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation
2. Copy pywikibot/families/4training_family.py to the pywikibot families
   directory
3. ``python3 pwb.py generate_user_files``
   -> select 1: 4training family
   -> enter the bot user name
   -> don’t enter a password here
4. ``python3 pwb.py login`` -> enter password here

Run scripts with pywikibot:
---------------------------

``python3 pwb.py path/to/script.py args``

File overview
-------------

4training-backup.py
    Web-scraping tool to download all worksheets
config.example.ini
    Example for all configuration settings
config.ini
    Not in repository, needs to be created by you
downloadalltranslations.py
    Download all translated worksheets of a given worksheet
dropboxupload.py
    Upload files into dropbox
fortraininglib.py
    Our central library with important functions and API calls
generateodtbot.py
    Wrapper script for translateodt.py (requires pywikibot)
resourcesbot.py
    Automatically fill out the “Available training resources in...” for each language (requires pywikibot)
translateodt.py
    Processes English ODT file and replaces it with the translation into another language
    Introduction for users: https://www.youtube.com/watch?v=g9lZbLaXma0
cgi-bin/generateodt.py
    CGI-Handler that receives the request (coming from outside like https://www.example.net/cgi-bin/generateodt.py)
    and calls generateodtbot.py

Configuration
-------------

You first need to create a file config.ini with the correct settings
(see the config.example.ini for more hints)

Contributing and coding conventions
-----------------------------------

See CONTRIBUTING.rst

Communication
~~~~~~~~~~~~~

Please subscribe to the repository to get informed on changes.
We use github issues for specific tasks, wishes, bugs etc. 
Please don’t hesitate to open a new one! Assign yourself on the issues that
you plan to work on.

Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
