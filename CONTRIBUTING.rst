.. highlight:: shell

============
Contributing
============

We're very happy about every contribution! :)

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/4training/pywikitools/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

Python Mediawiki Tools could always use more documentation, whether as part of the
official Python Mediawiki Tools docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/4training/pywikitools/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `pywikitools` for local development.

1. Fork the `pywikitools` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/pywikitools.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv pywikitools
    $ cd pywikitools/
    $ python3 setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 pywikitools tests
    $ python3 setup.py test or pytest
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Coding conventions
------------------
  
* Please write good and readable code with meaningful documentation.
* We try to follow the PEP 8 style guide ( https://pep8.org/ ) with the
  exception that lines can have up to 120 spaces.
* Every script should print documentation on arguments when run without
  or with incorrect arguments
   
Logging 
~~~~~~~

Every script should implement good logging (see https://docs.python.org/3/howto/logging.html ).
Look at translateodt.py for examples. Details:

* Create a named logger object (and only use this object for logging)
  ``logger = logging.getLogger('4training.scriptname')``
* Implement -l / --loglevel argument
* Standard log level is WARNING. INFO adds relevant information. DEBUG is for verbose debugging.
* ERROR means script couldn’t finish as expected

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.5, 3.6, 3.7 and 3.8, and for PyPy. Check
   https://travis-ci.com/4training/pywikitools/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::


    $ python3 -m unittest tests.test_pywikitools

Deploying
---------

TODO we're not yet using Travis nor PyPI but that would be nice.
Maybe someone can help with setting this up?

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).
Then run::

$ bump2version patch # possible: major / minor / patch
$ git push
$ git push --tags

Travis will then deploy to PyPI if tests pass.
