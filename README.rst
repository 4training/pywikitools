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

Setup:
------

#. Install pywikibot, following
   https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation
#. Request a user-config.py (not in the repository) and place it in the ``pywikitools/pywikitools/`` directory
   (same directory where the python scripts you want to run are located). Alternatively you can generate it yourself:

   * You need a "full" pywikibot installation (not just the one you get with ``pip install pywikibot``)
   * Make sure the 4training_family.py is at the correct place in that pywikibot installation
   * ``python3 pwb.py generate_user_files``
   * select 1: 4training family
   * enter the bot user name
   * don't enter a password here
#. Set up configuration in ``config.ini``:

   * ``cp config.example.ini config.ini``
   * Edit and where necessary adjust it
#. You're ready to go! Look at the different scripts and how to invoke them and try them out! To get to know everything and to understand what is going on, set the logging level to INFO (default is WARN) by adding ``-l info``.

Run scripts
---------------------------
``python3 path/to/script args``

(*more cumbersome alternative using a full pywikibot installation:* ``python3 /path/to/pwb.py path/to/script.py args``)

If you're not yet logged in, pywikibot will ask you for the password for the user you defined in ``user-config.py``. After successful login, the login cookie is stored in ``pywikibot.lwp`` so you don't have to log in every time again.

File overview
-------------

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
correctbot/
    Can automatically correct simple mistakes in texts of different languages (not yet operational)

License
-------
Jesus says in Matthew 10:8, “Freely you have received; freely give.”

We follow His example and believe His principles are well expressed in the developer world through free and open-source software.
That's why we want you to have the `four freedoms <https://fsfe.org/freesoftware/>`_ to freely use, study, share and improve this software.
We only require you to release any derived work under the same conditions (you're not allowed to take this code, build upon it and make the result proprietary):

`GNU General Public License (Version 3) <https://www.gnu.org/licenses/gpl-3.0.en.html>`_

Contributing and coding conventions
-----------------------------------

By contributing you release your contributed code under the licensing terms explained above. Thank you!

For more details see CONTRIBUTING.rst

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
