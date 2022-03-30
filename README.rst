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

**Note**: pywikitools base path refers to the directory, where you can find ``README.rst``, ``CONTRIBUTING.rst`` and ``requirements.txt``. 

#. Install required libraries: ``pip install -r requirements.txt``:
   * Follow these steps if you are using a virtual environment on a Linux machine:
   	* To install ``virtualenv``: ``sudo python3 -m pip install virtualenv``
   	* To create a new virtual environment: ``virtualenv --system-site-packages new_venv_name``. It is important to include the tag ``--system-site-packages``, else the virtual environment will not be able to import the uno package into your working environment.
   	* To activate the virtual environment: ``source new_venv_name/bin/activate``
   	* Change into pywikitools base path and run ``pip install -r requirements.txt``.
#. Request a user-config.py (not in the repository) and place it in the ``pywikitools/pywikitools/`` directory
   (same directory where the python scripts you want to run are located). Alternatively you can generate it yourself:
   * You need a "full" pywikibot installation:
	* Step 2a: Go to official pywikibot website: https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation
	* Step 2b: If you are using Python 3, download current Pywikibot stable branch: ``https://pywikibot.toolforge.org/core_stable.tar.gz``
		   If you are using Python 2, you can use this link to download pywikibot: ``https://pywikibot.toolforge.org/core_python2.tar.gz``
	* Step 2c: Change your current directory into pywikibot (can be found from the git repos you cloned into your working space) and unpack the downloaded zip folder here (for example: core_stable for Python3 users).
	* Step 2d: Copy the file `4training_family.py` from `~/pywikitools/pywikibot/families` into `~/pywikitools/pywikibot/core_stable/pywikibot/families`.
	* Step 2e: Change into the `~/pywikitools/pywikibot/core_stable` directory, where you can also find the file `pwb.py`.
   * Run this command from the terminal: ``python3 pwb.py generate_user_files``
   	* select 1: 4training family
   	* enter the bot user name (Request the username from Samuel)
   	* don't enter a new password here
#. Set up configuration in ``config.ini``:
   * ``cp config.example.ini config.ini``
   * Change the base path ini ``config.ini`` to the directory, where you cloned the pywikitools base folder, for example:  ``base = /YOUR_HOME_PATH/pywikitools/``
#. Make sure the pywikitools package is found by python. Options:
   * Create a new PTH file in the site-packages directory:
   	* If you do not use a virtual environment: ``~/.local/lib/python3.8/site-packages/``) and write the base path of this repository into it
   	* If you use a virtual environment: ``~/your_env_name/lib/python3.8/site-packages``
   	* Create a new PTH file ``pywikitools.pth`` and copy the base path into the new file: ``/YOUR_HOME_PATH/pywikitools/``.
   * Appending it to PYTHONPATH
   * TODO: Remove this awkward step - see https://github.com/4training/pywikitools/issues/41
#. You're ready to go! Look at the different scripts and how to invoke them and try them out! To get to know everything and to understand what is going on, set the logging level to INFO (default is WARN) by adding ``-l info``.


Run scripts
-----------
``python3 path/to/script args``

(*more cumbersome alternative using a full pywikibot installation:* ``python3 /path/to/pwb.py path/to/script.py args``)

If you're not yet logged in, pywikibot will ask you for the password for the user you defined in ``user-config.py``. After successful login, the login cookie is stored in ``pywikibot.lwp`` so you don't have to log in every time again.

Testing
-------

From your base pywikitools path, run ``python3 -m unittest discover -s pywikitools/test``

With GitHub Actions these are run also on any push or pull request in the repository. The goal is to cover all important code parts with good tests. Some of the tests are making real API calls, that's why running the tests can take half a minute. `More details`_


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

.. _More details: https://www.holydevelopers.net/python-setting-up-automatic-testing-with-github-actions`_
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
