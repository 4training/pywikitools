.. highlight:: shell

============
Contributing
============

We're very happy about every contribution! :)

You can contribute in many ways:

Types of Contributions
----------------------

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues: If there is nobody assigned for an issue it is open to whoever wants to
implement it.

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

3. Follow the setup instructions in README.rst

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that all tests still pass and that flake8 has nothing to complain::

    $ python3 -m unittest discover -s pywikitools/test
    $ flake8 .

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
  ``logger = logging.getLogger('pywikitools.scriptname')``
* Implement -l / --loglevel argument
* Standard log level is WARNING. INFO adds relevant information. DEBUG is for verbose debugging.
* ERROR means script couldn’t finish as expected

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Minimum
   is to make sure functions have correct docstrings.
3. Write meaningful commit messages

Tips
----

To run a subset of tests::

    $ python3 pywikitools/test/test_script.py
