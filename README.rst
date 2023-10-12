|Run tests| |Coverage| |GPLv3 license| |Open Source? Yes!|

.. |Run tests| image:: https://github.com/4training/pywikitools/actions/workflows/main.yml/badge.svg
   :target: https://github.com/4training/pywikitools/actions/workflows/main.yml
.. |Coverage| image:: https://codecov.io/gh/4training/pywikitools/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/4training/pywikitools
.. |GPLv3 license| image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: http://perso.crans.org/besson/LICENSE.html
.. |Open Source? Yes!| image:: https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github
   :target: https://github.com/Naereen/badges/
======================
Python Mediawiki Tools
======================

Python tools for mediawiki with the Translate plugin (some based on pywikibot).
This is used for https://www.4training.net to remove some bottlenecks of the project,
providing different automation and reports (TODO: document the outcomes of these scripts).
Hopefully others can benefit from some of the scripts as well!

* Free software: GNU General Public License v3

.. NOT YET * Documentation: https://pywikitools.readthedocs.io.

| The tools use the mediawiki API. URL and all documentation:
  https://www.4training.net/mediawiki/api.php
| Read-only scripts make direct use of the API calls. Bots writing to
  the system use the pywikibot framework:
  https://www.mediawiki.org/wiki/Manual:Pywikibot

Setup:
------

**Note**: pywikitools base path refers to the directory, where you can find ``README.rst``, ``CONTRIBUTING.rst`` and ``requirements.txt``.

#. Install required libraries: ``pip install -r requirements.txt``:

    * Follow these steps if you are using a virtual environment on a Linux machine:

   	    * To install ``virtualenv``: ``sudo python3 -m pip install virtualenv``
   	    * To create a new virtual environment: ``virtualenv --system-site-packages new_venv_name``. It is important to include the tag ``--system-site-packages``, else the virtual environment will not be able to import the uno package into your working environment.
   	    * To activate the virtual environment: ``source new_venv_name/bin/activate``
   	    * Change into pywikitools base path and run ``pip install -r requirements.txt``.

#. Install LibreOffice UNO (python bridge): ``sudo apt-get install python3-uno`` (on linux)

    * This is not necessary for all scripts, only for our LibreOffice module and scripts using it (``translateodt.py``)
    * Running the complete test suite requires it, though

#. Set up configuration in ``config.ini``:

        * ``cp config.example.ini config.ini``
        * Change the base path ini ``config.ini`` to the directory where you cloned the pywikitools base folder, for example:  ``base = /YOUR_HOME_PATH/pywikitools/``
        * Configure all other necessary options like user names and site (connect to ``4training.net`` / ``test.4training.net``)

#. You're ready to go! Look at the different scripts and how to invoke them and try them out! To get to know everything and to understand what is going on, set the logging level to INFO (default is WARN) by adding ``-l info``.


Run scripts
-----------
``python3 path/to/script args``

If you're not yet logged in, pywikibot will ask you for the password for the user you defined in ``config.ini``. After successful login, the login cookie is stored in ``pywikibot-[UserName].lwp`` so you don't have to log in every time again.

Testing and ensuring good code quality
--------------------------------------

From your base pywikitools path, run ``python3 -m unittest discover -s pywikitools/test`` to run the test suite.
Run also ``flake8 .`` to check for any linting issues.

With GitHub Actions these two commands are run also on any push or pull request in the repository.
The goal is to cover all important code parts with good tests.
Some of the tests are making real API calls, that's why running the tests can take half a minute. `More details`_

We use codecov to calculate the coverage ratio. You can see it in the codecov badge on the repository page or
check out the details on `codecov.io`_


File overview: Configuration and main entry scripts
---------------------------------------------------

autotranslate.py
    Create a first translation draft by using machine translation by DeepL or Google translate
    Introduction for users: https://www.youtube.com/watch?v=czsqgA6Ua7s
config.example.ini
    Example for all configuration settings
config.ini
    Not in repository, needs to be created by you. Configure here for each script:
    Which system should we connect to? (www.4training.net / test.4training.net)
    Which user name does it use?
correct_bot.py
    Automatically correct simple mistakes in texts of different languages
resources_bot.py
    Automatically scan through all available translations, gather information on each language
    and do many useful things with this information, like
    filling out the “Available training resources in...” for each language and
    exporting the worksheets into HTML
translateodt.py
    Processes English ODT file and replaces it with the translation into another language
    Introduction for users: https://www.youtube.com/watch?v=g9lZbLaXma0
pywikitools/fortraininglib.py
    Our central library with important functions and API calls


More tools:

downloadalltranslations.py
    Download all translated worksheets of a given worksheet
dropboxupload.py
    Upload files into dropbox
mediawiki2drupal.py
    Export content from mediawiki into Drupal


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


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _More details: https://www.holydevelopers.net/python-setting-up-automatic-testing-with-github-actions
.. _codecov.io: https://app.codecov.io/gh/4training/pywikitools
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
