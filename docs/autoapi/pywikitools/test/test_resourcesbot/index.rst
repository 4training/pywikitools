:py:mod:`pywikitools.test.test_resourcesbot`
============================================

.. py:module:: pywikitools.test.test_resourcesbot

.. autoapi-nested-parse::

   Testing ResourcesBot

   Currently we have only little test coverage...
   TODO: Find ways to run meaningful tests that don't take too long...



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.test.test_resourcesbot.TestResourcesBot




.. py:class:: TestResourcesBot(methodName='runTest')

   Bases: :py:obj:`unittest.TestCase`

   We mock pywikibot because otherwise we would need to provide a valid user-config.py (and because it saves time)

   .. py:method:: setUp(self)

      Hook method for setting up the test fixture before exercising it.


   .. py:method:: tearDown(self)

      Hook method for deconstructing the test fixture after testing it.



