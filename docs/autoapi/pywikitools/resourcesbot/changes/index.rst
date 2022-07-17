:py:mod:`pywikitools.resourcesbot.changes`
==========================================

.. py:module:: pywikitools.resourcesbot.changes

.. autoapi-nested-parse::

   Contains the classes ChangeType, ChangeItem and ChangeLog that describe the list of changes on the 4training.net website
   since the last run of the resourcesbot.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.changes.ChangeType
   pywikitools.resourcesbot.changes.ChangeItem
   pywikitools.resourcesbot.changes.ChangeLog




.. py:class:: ChangeType

   Bases: :py:obj:`enum.Enum`

   The different types of changes that can happen.
   Normally there wouldn't be any deletions


.. py:class:: ChangeItem(worksheet: str, change_type: ChangeType)

   Holds the details of one change
   This shouldn't be modified after creation (is there a way to enforce that?)


.. py:class:: ChangeLog

   Holds all changes that happened in one language since the last resourcesbot run


