[![Run tests](https://github.com/4training/pywikitools/actions/workflows/main.yml/badge.svg)](https://github.com/4training/pywikitools/actions/workflows/main.yml)
[![Coverage](https://codecov.io/gh/4training/pywikitools/branch/main/graph/badge.svg)](https://codecov.io/gh/4training/pywikitools)
[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)
[![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/)

# Python Mediawiki Tools

Python tools for mediawiki with the Translate plugin (some based on pywikibot).
This is used for [4training](https://www.4training.net) to remove some
bottlenecks of the project, providing different automation and reports (TODO:
document the outcomes of these scripts). Hopefully, others can benefit from some
scripts as well!

* Free
  software: [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html)

The tools use the [MediaWiki API](https://www.4training.net/mediawiki/api.php).

Read-only scripts make direct use of the API calls. Bots writing to the system
use the [pywikibot framework](https://www.mediawiki.org/wiki/Manual:Pywikibot).

<!-- TOC -->
* [Python Mediawiki Tools](#python-mediawiki-tools)
  * [Setup](#setup)
  * [Run scripts](#run-scripts)
  * [Testing and ensuring good code quality](#testing-and-ensuring-good-code-quality)
  * [File overview: Configuration and main entry scripts](#file-overview-configuration-and-main-entry-scripts)
  * [More tools](#more-tools)
  * [License](#license)
  * [Contributing and coding conventions](#contributing-and-coding-conventions)
  * [Communication](#communication)
  * [Credits](#credits)
<!-- TOC -->

## Setup

> **Note**: pywikitools base path refers to the directory where you can find
> `README.md`, `CONTRIBUTING.md`, and `requirements.txt`.

1. Install required libraries within a `virtualenv`:

    > We strongly recommend you to use a virtual environment to manage your  
      Python dependencies.

    * Install `virtualenv`:

       ```shell
       $ sudo python -m pip install virtualenv
       ```

    * Create a new virtual environment:

       ```shell
       $ virtualenv new_venv_name
       ```

    * Activate the virtual environment:

       ```shell
       $ source new_venv_name/bin/activate
       ```

    * At the root directory of `pywikitools`, run:

       ```shell
       $ pip install -r requirements.txt
       ```

2. Install LibreOffice UNO (python bridge, on linux)
   ```shell
   $ sudo apt-get install python3-uno
   ``` 
   > This is required for our LibreOffice module and scripts using it
   > (`translateodt.py`), and to run the complete test suite.

3. Set up configuration in `config.ini`:
   ```shell
   $ cp config.example.ini config.ini
   ```
    * Change the base path in `config.ini` to the directory where you cloned the
      pywikitools base directory, for example:
      ```config
      base = /YOUR_HOME_PATH/pywikitools/
      ```
    * Configure all other necessary options like usernames and site (connect to
      `4training.net` / `test.4training.net`)

4. You're ready to go! Look at the different scripts and how to invoke them and
   try them out! To get to know everything and to understand what is going on,
   set the logging level to INFO (default is WARN) by adding `-l info`.

## Run scripts

```shell
$ python3 path/to/script args
```

If you're not yet logged in, `pywikibot` will ask you for the password for the
user you defined in `config.ini`. After successful login, the login cookie is
stored in `pywikibot-[UserName].lwp` so you don't have to log in every time.

## Testing and ensuring good code quality

From your base pywikitools path, use the following command to run the test
suite.

```shell
$ python3 -m unittest discover -s pywikitools/test
``` 

Also, run the next command to check for linting issues

```shell
$ flake8
```

With `GitHub Actions` these two commands are automatically run also on every
push or pull request in the repository. The goal is to cover all important code
with good test coverage.

Some tests are making real API calls, that's why running the tests can
take half a
minute. [More details](https://www.holydevelopers.net/python-setting-up-automatic-testing-with-github-actions)

We use codecov to calculate the coverage ratio. You can see it in the codecov
badge on the repository page or check out the details
on [codecov.io](https://app.codecov.io/gh/4training/pywikitools)

## File overview: Configuration and main entry scripts

autotranslate.py
: Create a first translation draft by using automated translation by DeepL or
Google translation.
Introduction for
users: [https://www.youtube.com/watch?v=czsqgA6Ua7s](https://www.youtube.com/watch?v=czsqgA6Ua7s)

config.example.ini
: Example for all configuration settings.

config.ini
: Not in repository, needs to be created by you.
This is where you set up your configuration for each script, e.g.:
Which system should it connect to? `4training.net` || `test.4training.net`
Which username should it use?

correct_bot.py
: Automatically correct simple mistakes in texts of different languages.

resources_bot.py
: Automatically scan through all available translations, gather information on
each language and do many useful things with this information.
Such as filling out the “Available training resources in...”
for each language and exporting the worksheets into HTML

translateodt.py
: Processes an English ODT file and replaces it with the translation into
another language.
Introduction for
users: [https://www.youtube.com/watch?v=g9lZbLaXma0](https://www.youtube.com/watch?v=g9lZbLaXma0)

pywikitools/fortraininglib.py
: Our central library with important functions and API calls.

## More tools

downloadalltranslations.py
: Download all translated worksheets of a given language.

dropboxupload.py
: Upload files into dropbox.

mediawiki2drupal.py
: Export content from mediawiki into Drupal.

## License

Jesus says in Matthew 10:8, “Freely you have received; freely give.”

We follow His example and believe His principles are well expressed in the
developer world through free and open-source software. That's why we want you to
have the [four freedoms](https://fsfe.org/freesoftware/) to freely use, study,
share, and improve this software. We only require you to release any derived
work under the same conditions (you're not allowed to take this code, build upon
it, and make the result
proprietary): [GNU General Public License (Version 3)](https://www.gnu.org/licenses/gpl-3.0.en.html)

## Contributing and coding conventions

By contributing you release your contributed code under the licensing terms
explained above. Thank you!
For more details, see CONTRIBUTING.md

## Communication

Please subscribe to the repository to get informed on changes. We use GitHub
issues for specific tasks, wishes, bugs, etc. Please don’t hesitate to open
a new one! Assign yourself to the issues that you plan to work on.

## Credits

This package was created
with [Cookiecutter](https://github.com/audreyr/cookiecutter) and
the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage)
project template.