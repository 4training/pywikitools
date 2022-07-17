:py:mod:`pywikitools.test.test_correctbot`
==========================================

.. py:module:: pywikitools.test.test_correctbot

.. autoapi-nested-parse::

   Test cases for CorrectBot: Testing core functionality as well as language-specific rules



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.test.test_correctbot.CorrectorTestCase
   pywikitools.test.test_correctbot.TestLanguageCorrectors
   pywikitools.test.test_correctbot.UniversalCorrectorTester
   pywikitools.test.test_correctbot.TestUniversalCorrector
   pywikitools.test.test_correctbot.NoSpaceBeforePunctuationCorrectorTester
   pywikitools.test.test_correctbot.TestNoSpaceBeforePunctuationCorrector
   pywikitools.test.test_correctbot.RTLCorrectorTester
   pywikitools.test.test_correctbot.TestRTLCorrector
   pywikitools.test.test_correctbot.TestGermanCorrector
   pywikitools.test.test_correctbot.TestFrenchCorrector
   pywikitools.test.test_correctbot.TestArabicCorrector
   pywikitools.test.test_correctbot.TestCorrectBot



Functions
~~~~~~~~~

.. autoapisummary::

   pywikitools.test.test_correctbot.correct
   pywikitools.test.test_correctbot.title_correct
   pywikitools.test.test_correctbot.filename_correct



.. py:function:: correct(corrector: pywikitools.correctbot.correctors.base.CorrectorBase, text: str, original: Optional[str] = None) -> str

   Shorthand function for running a test with CorrectorBase.correct()


.. py:function:: title_correct(corrector: pywikitools.correctbot.correctors.base.CorrectorBase, text: str, original: Optional[str] = None) -> str

   Shorthand function for running a test with CorrectorBase.title_correct()


.. py:function:: filename_correct(corrector: pywikitools.correctbot.correctors.base.CorrectorBase, text: str, original: Optional[str] = None) -> str

   Shorthand function for running a test with CorrectorBase.filename_correct()


.. py:class:: CorrectorTestCase(methodName='runTest')

   Bases: :py:obj:`unittest.TestCase`

   Adds functions to check corrections against revisions made in the mediawiki system

   Use this as base class if you need this functionality. They come with the cost of doing
   real mediawiki API calls, taking significant time. The benefit is that you don't need to include
   potentially long strings in complex languages in the source code

   If you use this as base class, you need to set it up with the right corrector class like this:
   @classmethod
   def setUpClass(cls):
       cls.corrector = GermanCorrector()

   Example: compare_revisions("How_to_Continue_After_a_Prayer_Time", "ar", 1, 62195, 62258)
   calls
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62195
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62258
   which is similar to https://www.4training.net/mediawiki/index.php?Translations:How_to_Continue_After_a_Prayer_Time/1/ar&type=revision&diff=62258&oldid=62195    # noqa: E501
   See also https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&action=history                               # noqa: E501

   .. py:method:: compare_revisions(self, page: str, language_code: str, identifier: int, old_revision: int, new_revision: int)

      For all "normal" translation units: Calls CorrectorBase.correct()


   .. py:method:: compare_title_revisions(self, page: str, language_code: str, old_revision: int, new_revision)

      Calls CorrectBase.title_correct()


   .. py:method:: compare_filename_revisions(self, page: str, language_code: str, identifier: int, old_revision: int, new_revision)

      Calls CorrectorBase.filename_correct()



.. py:class:: TestLanguageCorrectors(methodName='runTest')

   Bases: :py:obj:`unittest.TestCase`

   A class whose instances are single test cases.

   By default, the test code itself should be placed in a method named
   'runTest'.

   If the fixture may be used for many test cases, create as
   many test methods as are needed. When instantiating such a TestCase
   subclass, specify in the constructor arguments the name of the test method
   that the instance is to execute.

   Test authors should subclass TestCase for their own tests. Construction
   and deconstruction of the test's environment ('fixture') can be
   implemented by overriding the 'setUp' and 'tearDown' methods respectively.

   If it is necessary to override the __init__ method, the base class
   __init__ method must always be called. It is important that subclasses
   should not change the signature of their __init__ method, since instances
   of the classes are instantiated automatically by parts of the framework
   in order to be run.

   When subclassing TestCase, you can set these attributes:
   * failureException: determines which exception will be raised when
       the instance's assertion methods fail; test methods raising this
       exception will be deemed to have 'failed' rather than 'errored'.
   * longMessage: determines whether long messages (including repr of
       objects used in assert methods) will be printed on failure in *addition*
       to any explicit message passed.
   * maxDiff: sets the maximum length of a diff in failure messages
       by assert methods using difflib. It is looked up as an instance
       attribute so can be configured by individual tests if required.

   .. py:method:: setUp(self)

      Load all language-specific corrector classes so that we can afterwards easily run our checks on them


   .. py:method:: test_for_meaningful_names(self)

      Make sure each function either starts with "correct_" or ends with "_title" or with "_filename.


   .. py:method:: test_for_correct_parameters(self)

      Make sure all correction functions take either one or two strings as parameters.


   .. py:method:: test_for_unique_function_names(self)

      Make sure that there are no functions with the same name in a language-specific corrector
      and a flexible corrector


   .. py:method:: test_for_function_documentation(self)

      Make sure that each corrector function has a documentation and its first line is not empty



.. py:class:: UniversalCorrectorTester

   Bases: :py:obj:`pywikitools.correctbot.correctors.base.CorrectorBase`, :py:obj:`pywikitools.correctbot.correctors.universal.UniversalCorrector`

   With this class we can test the rules of UniversalCorrector


.. py:class:: TestUniversalCorrector(methodName='runTest')

   Bases: :py:obj:`unittest.TestCase`

   A class whose instances are single test cases.

   By default, the test code itself should be placed in a method named
   'runTest'.

   If the fixture may be used for many test cases, create as
   many test methods as are needed. When instantiating such a TestCase
   subclass, specify in the constructor arguments the name of the test method
   that the instance is to execute.

   Test authors should subclass TestCase for their own tests. Construction
   and deconstruction of the test's environment ('fixture') can be
   implemented by overriding the 'setUp' and 'tearDown' methods respectively.

   If it is necessary to override the __init__ method, the base class
   __init__ method must always be called. It is important that subclasses
   should not change the signature of their __init__ method, since instances
   of the classes are instantiated automatically by parts of the framework
   in order to be run.

   When subclassing TestCase, you can set these attributes:
   * failureException: determines which exception will be raised when
       the instance's assertion methods fail; test methods raising this
       exception will be deemed to have 'failed' rather than 'errored'.
   * longMessage: determines whether long messages (including repr of
       objects used in assert methods) will be printed on failure in *addition*
       to any explicit message passed.
   * maxDiff: sets the maximum length of a diff in failure messages
       by assert methods using difflib. It is looked up as an instance
       attribute so can be configured by individual tests if required.


.. py:class:: NoSpaceBeforePunctuationCorrectorTester

   Bases: :py:obj:`pywikitools.correctbot.correctors.base.CorrectorBase`, :py:obj:`pywikitools.correctbot.correctors.universal.NoSpaceBeforePunctuationCorrector`

   With this class we can test the rules of NoSpaceBeforePunctuationCorrector


.. py:class:: TestNoSpaceBeforePunctuationCorrector(methodName='runTest')

   Bases: :py:obj:`CorrectorTestCase`

   Adds functions to check corrections against revisions made in the mediawiki system

   Use this as base class if you need this functionality. They come with the cost of doing
   real mediawiki API calls, taking significant time. The benefit is that you don't need to include
   potentially long strings in complex languages in the source code

   If you use this as base class, you need to set it up with the right corrector class like this:
   @classmethod
   def setUpClass(cls):
       cls.corrector = GermanCorrector()

   Example: compare_revisions("How_to_Continue_After_a_Prayer_Time", "ar", 1, 62195, 62258)
   calls
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62195
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62258
   which is similar to https://www.4training.net/mediawiki/index.php?Translations:How_to_Continue_After_a_Prayer_Time/1/ar&type=revision&diff=62258&oldid=62195    # noqa: E501
   See also https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&action=history                               # noqa: E501


.. py:class:: RTLCorrectorTester

   Bases: :py:obj:`pywikitools.correctbot.correctors.base.CorrectorBase`, :py:obj:`pywikitools.correctbot.correctors.universal.RTLCorrector`

   With this class we can test the rules of RTLCorrector


.. py:class:: TestRTLCorrector(methodName='runTest')

   Bases: :py:obj:`CorrectorTestCase`

   Adds functions to check corrections against revisions made in the mediawiki system

   Use this as base class if you need this functionality. They come with the cost of doing
   real mediawiki API calls, taking significant time. The benefit is that you don't need to include
   potentially long strings in complex languages in the source code

   If you use this as base class, you need to set it up with the right corrector class like this:
   @classmethod
   def setUpClass(cls):
       cls.corrector = GermanCorrector()

   Example: compare_revisions("How_to_Continue_After_a_Prayer_Time", "ar", 1, 62195, 62258)
   calls
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62195
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62258
   which is similar to https://www.4training.net/mediawiki/index.php?Translations:How_to_Continue_After_a_Prayer_Time/1/ar&type=revision&diff=62258&oldid=62195    # noqa: E501
   See also https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&action=history                               # noqa: E501

   .. py:method:: setUpClass(cls)
      :classmethod:

      Hook method for setting up class fixture before running tests in the class.



.. py:class:: TestGermanCorrector(methodName='runTest')

   Bases: :py:obj:`CorrectorTestCase`

   Adds functions to check corrections against revisions made in the mediawiki system

   Use this as base class if you need this functionality. They come with the cost of doing
   real mediawiki API calls, taking significant time. The benefit is that you don't need to include
   potentially long strings in complex languages in the source code

   If you use this as base class, you need to set it up with the right corrector class like this:
   @classmethod
   def setUpClass(cls):
       cls.corrector = GermanCorrector()

   Example: compare_revisions("How_to_Continue_After_a_Prayer_Time", "ar", 1, 62195, 62258)
   calls
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62195
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62258
   which is similar to https://www.4training.net/mediawiki/index.php?Translations:How_to_Continue_After_a_Prayer_Time/1/ar&type=revision&diff=62258&oldid=62195    # noqa: E501
   See also https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&action=history                               # noqa: E501


.. py:class:: TestFrenchCorrector(methodName='runTest')

   Bases: :py:obj:`unittest.TestCase`

   A class whose instances are single test cases.

   By default, the test code itself should be placed in a method named
   'runTest'.

   If the fixture may be used for many test cases, create as
   many test methods as are needed. When instantiating such a TestCase
   subclass, specify in the constructor arguments the name of the test method
   that the instance is to execute.

   Test authors should subclass TestCase for their own tests. Construction
   and deconstruction of the test's environment ('fixture') can be
   implemented by overriding the 'setUp' and 'tearDown' methods respectively.

   If it is necessary to override the __init__ method, the base class
   __init__ method must always be called. It is important that subclasses
   should not change the signature of their __init__ method, since instances
   of the classes are instantiated automatically by parts of the framework
   in order to be run.

   When subclassing TestCase, you can set these attributes:
   * failureException: determines which exception will be raised when
       the instance's assertion methods fail; test methods raising this
       exception will be deemed to have 'failed' rather than 'errored'.
   * longMessage: determines whether long messages (including repr of
       objects used in assert methods) will be printed on failure in *addition*
       to any explicit message passed.
   * maxDiff: sets the maximum length of a diff in failure messages
       by assert methods using difflib. It is looked up as an instance
       attribute so can be configured by individual tests if required.

   .. py:method:: test_punctuation(self)

      Ensure correct spaces around punctuation:

      No space before comma and dot, space before ; : ! ?
      Space after all punctuation marks.



.. py:class:: TestArabicCorrector(methodName='runTest')

   Bases: :py:obj:`CorrectorTestCase`

   Adds functions to check corrections against revisions made in the mediawiki system

   Use this as base class if you need this functionality. They come with the cost of doing
   real mediawiki API calls, taking significant time. The benefit is that you don't need to include
   potentially long strings in complex languages in the source code

   If you use this as base class, you need to set it up with the right corrector class like this:
   @classmethod
   def setUpClass(cls):
       cls.corrector = GermanCorrector()

   Example: compare_revisions("How_to_Continue_After_a_Prayer_Time", "ar", 1, 62195, 62258)
   calls
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62195
   https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62258
   which is similar to https://www.4training.net/mediawiki/index.php?Translations:How_to_Continue_After_a_Prayer_Time/1/ar&type=revision&diff=62258&oldid=62195    # noqa: E501
   See also https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&action=history                               # noqa: E501

   .. py:method:: setUpClass(cls)
      :classmethod:

      Hook method for setting up class fixture before running tests in the class.



.. py:class:: TestCorrectBot(methodName='runTest')

   Bases: :py:obj:`unittest.TestCase`

   A class whose instances are single test cases.

   By default, the test code itself should be placed in a method named
   'runTest'.

   If the fixture may be used for many test cases, create as
   many test methods as are needed. When instantiating such a TestCase
   subclass, specify in the constructor arguments the name of the test method
   that the instance is to execute.

   Test authors should subclass TestCase for their own tests. Construction
   and deconstruction of the test's environment ('fixture') can be
   implemented by overriding the 'setUp' and 'tearDown' methods respectively.

   If it is necessary to override the __init__ method, the base class
   __init__ method must always be called. It is important that subclasses
   should not change the signature of their __init__ method, since instances
   of the classes are instantiated automatically by parts of the framework
   in order to be run.

   When subclassing TestCase, you can set these attributes:
   * failureException: determines which exception will be raised when
       the instance's assertion methods fail; test methods raising this
       exception will be deemed to have 'failed' rather than 'errored'.
   * longMessage: determines whether long messages (including repr of
       objects used in assert methods) will be printed on failure in *addition*
       to any explicit message passed.
   * maxDiff: sets the maximum length of a diff in failure messages
       by assert methods using difflib. It is looked up as an instance
       attribute so can be configured by individual tests if required.

   .. py:method:: setUp(self)

      Hook method for setting up the test fixture before exercising it.


   .. py:method:: prepare_translated_page(self) -> pywikitools.lang.translated_page.TranslatedPage

      Prepare a TranslatedPage object out of the FRENCH_CORRECTIONS dictionary


   .. py:method:: test_save_report(self, mock_page)

      Check that output of CorrectBot.save_report() is the same as expected in data/correctbot_report.mediawiki



