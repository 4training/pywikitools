import unittest

from pywikitools.lang.translated_page import SnippetType, TranslationUnit, TranslationSnippet

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

class TestTranslationUnit(unittest.TestCase):
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
        with_lists = TranslationUnit("Test", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        self.assertTrue(with_lists.is_translation_well_structured())
        with_lists = TranslationUnit("Test", "de", TEST_UNIT_WITH_DEFINITION, TEST_UNIT_WITH_DEFINITION_DE_ERROR)
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING'):
            self.assertFalse(with_lists.is_translation_well_structured())

    def test_iteration(self):
        with_lists = TranslationUnit("Test", "de", TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE)
        counter = 0
        for orig, trans in with_lists:
            self.assertTrue(orig.is_text())
            self.assertTrue(trans.is_text())
            counter += 1
        self.assertTrue(with_lists.is_translation_well_structured())
        self.assertGreaterEqual(counter, 8)


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

if __name__ == '__main__':
    unittest.main()
