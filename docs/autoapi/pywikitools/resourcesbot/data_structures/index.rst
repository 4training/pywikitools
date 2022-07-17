:orphan:

:py:mod:`pywikitools.resourcesbot.data_structures`
==================================================

.. py:module:: pywikitools.resourcesbot.data_structures


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.data_structures.PdfMetadataSummary
   pywikitools.resourcesbot.data_structures.FileInfo
   pywikitools.resourcesbot.data_structures.WorksheetInfo
   pywikitools.resourcesbot.data_structures.LanguageInfo
   pywikitools.resourcesbot.data_structures.DataStructureEncoder



Functions
~~~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.data_structures.json_decode



.. py:class:: PdfMetadataSummary(version: str, correct: bool, pdf1a: bool, only_docinfo: bool, warnings: str)

   This class creates read-only data structure with evaluation result of the PDF metadata.

   .. py:method:: to_string(self, include_version: bool) -> str

      Write a human-readable string.

      :param include_version: Version to be included in the string output.

      :returns: A string of metadata with the version labels.


   .. py:method:: to_html(self) -> str

      Write a HTML string (specifically for the use case of the WriteReport plugin).



.. py:class:: FileInfo(file_type: str, url: str, timestamp: Union[datetime.datetime, str], *, translation_unit: Optional[int] = None, metadata: Optional[PdfMetadataSummary] = None)

   This class holds information on one file that is available on the website.

   .. note:: This shouldn't be modified after creation.

   .. py:method:: get_file_name(self) -> str

      Return the file name out of the url address.



.. py:class:: WorksheetInfo(page: str, language_code: str, title: str, progress: TranslationProgress, version: str, version_unit: Optional[int] = None)

   This class holds information on one worksheet in one specific language.

   .. note:: Only for worksheets that are at least partially translated.

   .. py:method:: add_file_info(self, file_info: Optional[FileInfo] = None, file_type: Optional[str] = None, from_pywikibot: Optional[pywikibot.page.FileInfo] = None, unit: Optional[int] = None, metadata: Optional[PdfMetadataSummary] = None)

      Add information about another file associated with this worksheet.

      You can call the function in two different ways:

          * providing file_info;
          * providing file_type and from_pywikibot (and potentially unit and/or metadata).

      .. note:: This will log on errors but shouldn't raise exceptions.


   .. py:method:: get_file_infos(self) -> Dict[str, FileInfo]

      Returns all available files associated with this worksheet.


   .. py:method:: has_file_type(self, file_type: str) -> bool

      Does the worksheet have a file for download (e.g. ``pdf``)?


   .. py:method:: get_file_type_info(self, file_type: str) -> Optional[FileInfo]

      Returns FileInfo of specified type (e.g. ``pdf``), None if not existing.

      :param file_type: File-type.


   .. py:method:: get_file_type_name(self, file_type: str) -> str

      Returns name of the file of the specified type (e.g. "pdf")
      @return only name (not full URL)
      @return empty string if we don't have the specified file type


   .. py:method:: is_incomplete(self) -> bool

      A translation is considered incomplete if most units are translated
      but at least one unit is not translated or fuzzy.


   .. py:method:: has_same_version(self, english_info) -> bool

      Compare our version string with the version string of the English original: is it the same?
      Native numerals will be converted to standard numerals.
      One additional character in our version will be ignored (e.g. "1.2b" is the same as "1.2")
      @param english_info: WorksheetInfo



.. py:class:: LanguageInfo(language_code: str, english_name: str)

   This class holds information on all available worksheets in one specific language.

   .. py:method:: worksheet_has_type(self, name: str, file_type: str) -> bool

      A convienence method combining ``LanguageInfo.has_worksheet()`` and ``WorksheetInfo.has_file_type()``.


   .. py:method:: compare(self, old) -> pywikitools.resourcesbot.changes.ChangeLog

      Compare ourselves to another (older) LanguageInfo object: have there been changes or updates?

      In case of ``NEW_WORKSHEET``, no ``NEW_PDF`` / ``NEW_ODT`` will be emitted (even if files got added)
      In case of ``DELETED_WORKSHEET``, no ``DELETED_PDF`` / ``DELETED_ODT`` will be emitted (even if files existed before).

      :returns: The data structure with all changes.


   .. py:method:: list_worksheets_with_missing_pdf(self) -> List[str]

      Returns a list of translated worksheets but are missing the PDF.



.. py:function:: json_decode(data: Dict[str, Any])

   Deserializes a JSON-formatted string back into different objects
   (``TranslationProgress``, ``FileInfo``, ``WorksheetInfo``, ``LanguageInfo`` objects).

   :raises AssertionError if the data is malformatted.:


.. py:class:: DataStructureEncoder(*, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, sort_keys=False, indent=None, separators=None, default=None)

   Bases: :py:obj:`json.JSONEncoder`

   Serializes a ``LanguageInfo`` / ``WorksheetInfo`` / ``FileInfo`` / ``PdfMetadataSummary`` / ``TranslationProgress`` object
   into a JSON string.

   .. py:method:: default(self, obj)

      Implement this method in a subclass such that it returns
      a serializable object for ``o``, or calls the base implementation
      (to raise a ``TypeError``).

      For example, to support arbitrary iterators, you could
      implement default like this::

          def default(self, o):
              try:
                  iterable = iter(o)
              except TypeError:
                  pass
              else:
                  return list(iterable)
              # Let the base class default method raise the TypeError
              return JSONEncoder.default(self, o)




