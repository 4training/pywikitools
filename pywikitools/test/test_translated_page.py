import unittest
from pywikitools import fortraininglib

from pywikitools.lang.translated_page import SnippetType, TranslatedPage, TranslationUnit, TranslationSnippet

TEST_UNIT_WITH_LISTS = """Jesus would not...
* <b>sell your data</b>
* trick you into his business
* give quick & dirty fixes
Jesus would...
# give everything away freely
# train people & share his skills
# care for people & treat them well
"""

TEST_UNIT_WITH_LISTS_DE = """Jesus würde nicht...
* <b>deine Daten verkaufen</b>
* dich in sein Geschäftsmodell reintricksen
* keine "quick & dirty" Lösungen anbieten
Jesus würde...
# alles frei weitergeben
# Menschen trainieren und sein Wissen teilen
# sich um Menschen kümmern und sie gut behandeln
"""

TEST_UNIT_WITH_DEFINITION = """;Forgiving myself
:Sometimes we’re angry at ourselves or blame ourselves for something. God offers a way to forgive us and
cleanse us through Jesus Christ. Forgiving myself means taking His offer and applying it to myself.
;“Forgiving” God
:Sometimes we have negative thoughts about God or are even mad at Him. God doesn’t make mistakes,
so in that sense we can’t forgive Him. But it is important that we let go of our frustrations and
negative feelings towards Him.
"""

TEST_UNIT_WITH_DEFINITION_DE_ERROR = """;Mir selbst vergeben
:Es kann sein, dass wir wütend auf uns selbst sind und uns etwas vorwerfen. Gott bietet uns einen Weg an, wie er uns durch Jesus Christus vergeben und reinigen möchte. Mir selbst vergeben bedeutet, sein Angebot anzunehmen und es auf mich anzuwenden.
Gott „vergeben“
:Manchmal haben wir negative Gedanken über Gott oder sind zornig auf ihn. Gott macht keine Fehler und in dem Sinn können wir ihm nicht vergeben. Aber es ist wichtig, dass wir Enttäuschungen über ihn loslassen und uns von allen negativen Gefühlen ihm gegenüber trennen.
"""

TEST_UNIT_WITH_HEADLINE = """== Dealing with Money ==
Money is a tool. With the same banknote I can bring blessing or harm.
=== Be fair ===
With money comes temptation.
"""

TEST_UNIT_WITH_BR = """But God wants us to see clearly and know the truth.
He wants to set us free from our distorted views and the negative consequences they have for us and other people.<br/>

Jesus says in John 8:31-32: <i>“If you obey my teaching, you are really my disciples.
Then you will know the truth. And the truth will set you free.”</i>"""

TEST_UNIT_WITH_FORMATTING = """''God, through which glasses am I seeing You?''<br/>
'''Let God show you what happened.'''<br/>
Use the ''support'' of a '''good''' helper!
"""

# TODO: Ideally this should be split into four snippets... but that would require
# more complexity in split_into_snippets() to understand that the newline after the third item
# should also be a splitting point... so currently this is split up into three snippets only
LIST_TEST = """* soll er Gott um Vergebung bitten, dass er die Lüge geglaubt und mit ihr zusammengearbeitet hat,
* die Lüge an Gott abgeben und
* fragen, „Gott, was ist die Wahrheit stattdessen?“
Lass denjenigen fragen, „Welche Lüge habe ich dadurch über mich gelernt?“ und fahre wie oben fort.
"""

class TestTranslationUnit(unittest.TestCase):
    def test_untranslated_unit(self):
        # Make sure None isn't accidentally converted to "None"
        not_translated = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, None)
        self.assertEqual(not_translated.get_translation(), "")
        not_translated = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, "")
        self.assertEqual(not_translated.get_translation(), "")

    def test_read_and_write(self):
        with_lists = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        with_lists.set_definition(TEST_UNIT_WITH_HEADLINE)
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING'):
            self.assertFalse(with_lists.is_translation_well_structured())   # Split everything in snippets
        self.assertEqual(with_lists.get_definition(), TEST_UNIT_WITH_HEADLINE)
        with_lists.set_translation(TEST_UNIT_WITH_DEFINITION_DE_ERROR)
        self.assertTrue(with_lists.has_translation_changes())
        self.assertNotEqual(with_lists.get_translation_diff(), "")

        # Making no changes to snippets should leave everything as it was before
        with_lists = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING'):
            with_lists.sync_from_snippets()
        self.assertTrue(with_lists.is_translation_well_structured())
        with_lists.sync_from_snippets()
        self.assertFalse(with_lists.has_translation_changes())

        # Test making changes to snippets
        for _, translation_snippet in with_lists:
            translation_snippet.content = translation_snippet.content.replace("e", "i")
        self.assertFalse(with_lists.has_translation_changes())  # because we haven't synced yet
        self.assertEqual(with_lists.get_translation_diff(), "")
        with_lists.sync_from_snippets()
        self.assertTrue(with_lists.has_translation_changes())
        self.assertNotEqual(with_lists.get_translation_diff(), "")

    def test_is_title(self):
        headline = TranslationUnit("Test/Page_display_title", "de", "Test headline", "Test-Überschrift")
        self.assertTrue(headline.is_title())
        no_headline = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        self.assertFalse(no_headline.is_title())

    def test_split_into_snippets(self):
        with_lists = TranslationUnit.split_into_snippets(TEST_UNIT_WITH_LISTS)
        self.assertEqual(len(with_lists), 16)
        self.assertEqual(len([s for s in with_lists if s.is_text()]), 8)
        self.assertEqual(TEST_UNIT_WITH_LISTS, "".join([s.content for s in with_lists]))

        with_definition = TranslationUnit.split_into_snippets(TEST_UNIT_WITH_DEFINITION)
        self.assertEqual(len(with_definition), 8)
        self.assertEqual(len([s for s in with_definition if s.is_text()]), 4)
        self.assertEqual(TEST_UNIT_WITH_DEFINITION, "".join([s.content for s in with_definition]))

        with_headline = TranslationUnit.split_into_snippets(TEST_UNIT_WITH_HEADLINE)
        self.assertEqual(len(with_headline), 8)
        self.assertEqual(len([s for s in with_headline if s.is_text()]), 4)
        self.assertEqual(TEST_UNIT_WITH_HEADLINE, "".join([s.content for s in with_headline]))

        with_br = TranslationUnit.split_into_snippets(TEST_UNIT_WITH_BR)
        self.assertEqual(len(with_br), 6)
        self.assertEqual(len([s for s in with_br if s.is_text()]), 3)
        self.assertEqual(TEST_UNIT_WITH_BR, "".join([s.content for s in with_br]))

        with_formatting = TranslationUnit.split_into_snippets(TEST_UNIT_WITH_FORMATTING)
        self.assertEqual(len(with_formatting), 17)
        self.assertEqual(len([s for s in with_formatting if s.is_text()]), 7)
        self.assertEqual(TEST_UNIT_WITH_FORMATTING, "".join([s.content for s in with_formatting]))

    def test_is_translation_well_structured(self):
        with_lists = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        self.assertTrue(with_lists.is_translation_well_structured())
        with_lists = TranslationUnit("Test/2", "de", TEST_UNIT_WITH_DEFINITION, TEST_UNIT_WITH_DEFINITION_DE_ERROR)
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING'):
            self.assertFalse(with_lists.is_translation_well_structured())

    def test_iteration(self):
        with_lists = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        counter = 0
        for orig, trans in with_lists:
            self.assertTrue(orig.is_text())
            self.assertTrue(trans.is_text())
            counter += 1
        self.assertTrue(with_lists.is_translation_well_structured())
        self.assertGreaterEqual(counter, 8)

        # Iterating over not well-structured translation unit should give a warning (and not raise an error)
        with_lists = TranslationUnit("Test/2", "de", TEST_UNIT_WITH_DEFINITION, TEST_UNIT_WITH_DEFINITION_DE_ERROR)
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING'):
            for _, _ in with_lists:
                pass

    def test_remove_links(self):
        DEFINITION_WITH_LINK = "This is a [[destination|link]]."
        DEFINITION_WITHOUT_LINK = "This is a link."
        TRANSLATION_WITH_LINK = "Das ist ein [[destination/de|Link]]."
        TRANSLATION_WITHOUT_LINK = "Das ist ein Link."
        link_unit = TranslationUnit("Test/1", "de", DEFINITION_WITH_LINK, TRANSLATION_WITH_LINK)
        link_unit.remove_links()
        self.assertEqual(link_unit.get_definition(), DEFINITION_WITHOUT_LINK)
        self.assertEqual(link_unit.get_translation(), TRANSLATION_WITHOUT_LINK)
        (definition, translation) = next(iter(link_unit))
        self.assertEqual(definition.content, DEFINITION_WITHOUT_LINK)
        self.assertEqual(translation.content, TRANSLATION_WITHOUT_LINK)

        link_unit.set_definition("This is a [[link]].")
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING'):
            link_unit.remove_links()
        self.assertEqual(link_unit.get_definition(), DEFINITION_WITHOUT_LINK)
        self.assertEqual(link_unit.get_translation(), TRANSLATION_WITHOUT_LINK)
        (definition, translation) = next(iter(link_unit))
        self.assertEqual(definition.content, DEFINITION_WITHOUT_LINK)
        self.assertEqual(translation.content, TRANSLATION_WITHOUT_LINK)

        link_unit.set_definition("This is a [[#link]].")
        link_unit.set_translation("Das ist ein [[Link]].")
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING'):
            link_unit.remove_links()
        self.assertEqual(link_unit.get_definition(), DEFINITION_WITHOUT_LINK)
        self.assertEqual(link_unit.get_translation(), TRANSLATION_WITHOUT_LINK)
        (definition, translation) = next(iter(link_unit))
        self.assertEqual(definition.content, DEFINITION_WITHOUT_LINK)
        self.assertEqual(translation.content, TRANSLATION_WITHOUT_LINK)


class TestTranslationSnippet(unittest.TestCase):
    def test_simple_functions(self):
        self.assertTrue(TranslationSnippet(SnippetType.MARKUP_SNIPPET, "<br>").is_br())
        self.assertTrue(TranslationSnippet(SnippetType.MARKUP_SNIPPET, "<br/>").is_br())
        self.assertTrue(TranslationSnippet(SnippetType.MARKUP_SNIPPET, "<br />").is_br())
        self.assertTrue(TranslationSnippet(SnippetType.MARKUP_SNIPPET, "<br/>\n").is_br())
        self.assertFalse(TranslationSnippet(SnippetType.MARKUP_SNIPPET, "<b>").is_br())

        with_br = TranslationUnit.split_into_snippets(TEST_UNIT_WITH_BR)
        self.assertTrue(with_br[0].is_text())
        self.assertFalse(with_br[0].is_br())
        self.assertTrue(with_br[1].is_br())
        self.assertFalse(with_br[1].is_text())
        self.assertTrue(with_br[1].is_markup())
        self.assertFalse(with_br[2].is_markup())

    def test_str(self):
        snippet = TranslationSnippet(SnippetType.MARKUP_SNIPPET, "<br/>")
        self.assertTrue(str(snippet).endswith("<br/>"))
        self.assertTrue(str(snippet).startswith("MARKUP"))

class TestTranslatedPage(unittest.TestCase):
    def test_untranslated_page(self):
        unit1 = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, None)
        unit2 = TranslationUnit("Test/2", "de", TEST_UNIT_WITH_DEFINITION, "")
        translated_page = TranslatedPage("Test", "de", [unit1, unit2])
        self.assertTrue(translated_page.is_untranslated())
        headline = TranslationUnit("Test/Page_display_title", "de", "Test headline", "Test-Überschrift")
        translated_page = TranslatedPage("Test", "de", [headline, unit1, unit2])
        self.assertFalse(translated_page.is_untranslated())

    def test_returning_empty_strings(self):
        # Constructing a strange TranslatedPage that doesn't even have a headline
        with_lists = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        translated_page = TranslatedPage("Test", "de", [with_lists])
        self.assertEqual(translated_page.get_original_headline(), "")
        self.assertEqual(translated_page.get_translated_headline(), "")
        # We construct a TranslatedPage with a headline but no version and ODT file information
        headline = TranslationUnit("Test/Page_display_title", "de", "Test headline", "Test-Überschrift")
        unit1 = TranslationUnit("Test/1", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        unit2 = TranslationUnit("Test/2", "de", TEST_UNIT_WITH_DEFINITION, TEST_UNIT_WITH_DEFINITION_DE_ERROR)
        translated_page = TranslatedPage("Test", "de", [headline, unit1, unit2])
        self.assertEqual(translated_page.get_original_headline(), headline.get_definition())
        self.assertEqual(translated_page.get_translated_headline(), headline.get_translation())
        self.assertEqual(translated_page.get_original_odt(), "")
        self.assertEqual(translated_page.get_translated_odt(), "")
        self.assertEqual(translated_page.get_original_version(), "")
        self.assertEqual(translated_page.get_translated_version(), "")

    def test_with_real_data(self):
        # TODO this test is closely tied to content on 4training.net that might change in the future
        translated_page = fortraininglib.get_translation_units("Forgiving_Step_by_Step", "de")
        self.assertIsNotNone(translated_page)
        self.assertEqual(translated_page.page, "Forgiving_Step_by_Step")
        self.assertEqual(translated_page.language_code, "de")
        self.assertEqual(translated_page.get_original_headline(), "Forgiving Step by Step")
        self.assertEqual(translated_page.get_original_odt(), "Forgiving_Step_by_Step.odt")
        self.assertEqual(translated_page.get_original_version(), "1.3")
        self.assertEqual(translated_page.get_translated_headline(), "Schritte der Vergebung")
        self.assertEqual(translated_page.get_translated_odt(), "Schritte_der_Vergebung.odt")
        self.assertEqual(translated_page.get_translated_version(), "1.3")
        unit_counter: int = 0
        for unit in translated_page:
            self.assertTrue(unit.get_name().startswith("Translations:Forgiving_Step_by_Step"))
            unit_counter += 1

        # Now let's load the translation units of one template and add them to our translated_page
        template_unit_counter: int = 0
        template_page = fortraininglib.get_translation_units("Template:BibleReadingHints", "de")
        for unit in template_page:
            translated_page.add_translation_unit(unit)
            template_unit_counter += 1
        self.assertGreater(unit_counter, 20)
        self.assertGreater(template_unit_counter, 10)

        # Make sure we have now all translation units combined
        self.assertEqual(len(translated_page.units), unit_counter + template_unit_counter)


if __name__ == '__main__':
    unittest.main()
