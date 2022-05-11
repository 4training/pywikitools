"""
A module for analyzing PDF metadata with pikepdf:
- PDF 1/A compatibility
- is it using XMP metadata or the deprecated DocInfo?
- are the title, subject and keywords properties set as expected?

This contains our standards for filling metadata.
TODO: Find a good place for our standards in a dedicated module and avoid duplicate code -
      they're also in TranslateODT._set_properties()
"""
import re
import pikepdf
from pywikitools.fortraininglib import ForTrainingLib

from pywikitools.resourcesbot.data_structures import PdfMetadataSummary, WorksheetInfo


def check_metadata(fortraininglib: ForTrainingLib, filename: str, info: WorksheetInfo) -> PdfMetadataSummary:
    """Check the PDF metadata whether it meets our standards. This involves:
    - title must start with translated title (identical if there is no subheadline)
    - subject must start with English worksheet name and end with correct language names
    - keywords must include version number

    Extracts the version number as well ("" indicates an error)
    @param filename: path of the PDF file to analyze
    @param info: WorksheetInfo so that we can compare the PDF metadata with the expected results
    """
    pdf = pikepdf.open(filename)
    version = ""
    metadata_correct = True
    only_docinfo = False
    warnings = ""
    title = ""
    subject = ""
    keywords = ""
    if (meta := pdf.open_metadata()):
        # This PDF has proper XMP metadata
        if "dc:title" in meta:
            title = meta["dc:title"]
        if "dc:description" in meta:
            subject = meta["dc:description"]
        if "pdf:Keywords" in meta:
            keywords = meta["pdf:Keywords"]
    else:
        # This PDF has only DocInfo metadata (deprecated)
        only_docinfo = True
        if "/Title" in pdf.docinfo:
            title = str(pdf.docinfo["/Title"])
        if "/Subject" in pdf.docinfo:
            subject = str(pdf.docinfo["/Subject"])
        if "/Keywords" in pdf.docinfo:
            keywords = str(pdf.docinfo["/Keywords"])

    # Little hack: Let's not care if it's God’s Story or God's Story
    title = title.replace("’", "'")
    subject = subject.replace("’", "'")

    # Check title metadata
    expected_title = info.title
    if (info.language_code == "en") and ((pos := expected_title.find(" (")) > 0):
        # Special case in English: title doesn't contain the part in parenthesis
        expected_title = expected_title[:pos]
    if not title.startswith(expected_title):
        metadata_correct = False
        warnings += f"Expected title to start with '{expected_title}' but found '{title}'\n"

    # Check subject metadata (except for the English originals)
    if info.language_code != "en":
        expected_subject = info.page.replace("_", " ")
        if not subject.startswith(expected_subject):
            metadata_correct = False
            warnings += f"Expected subject to start with '{expected_subject}' but found '{subject}'\n"
        english_language_name = str(fortraininglib.get_language_name(info.language_code, 'en'))
        autonym = str(fortraininglib.get_language_name(info.language_code))
        expected_subject_end = f"{english_language_name} {autonym}"
        # TODO the following special cases should go into some dedicated module
        if expected_subject_end == "Hausa Hausa":
            expected_subject_end = "Hausa"
        if expected_subject_end == "Afrikaans Afrikaans":
            expected_subject_end = "Afrikaans"
        if expected_subject_end == "Persian فارسی":
            expected_subject_end = "Persian Farsi فارسی"
        if not subject.endswith(expected_subject_end):
            metadata_correct = False
            warnings += f"Expected subject to end with '{expected_subject_end}' names but found '{subject}'\n"

    # Check keywords (should contain Template:CC0Notice with version information)
    handler = re.search(r"\d\.\d[a-zA-Z]?", keywords)
    if handler:
        version = handler.group(0)
    else:
        metadata_correct = False
        warnings += f"Couldn't extract version from keyword string '{keywords}'"

    return PdfMetadataSummary(version, metadata_correct, meta.pdfa_status == "1A", only_docinfo, warnings)
