import re


class EnglishCorrector:
    """
    Corrects typical English typos to follow the following rules:
    * TODO: No plain quotation marks: instead of "Foo" use “Foo”
    * TODO: No German quotation marks
      * “ must be at the beginning of a word, not at the end as in German (check for trailing whitespace?)
    * Substitute wrong apostrophe
    """

    def __init__(self, text_to_correct: str):
        self.text_to_correct: str = text_to_correct

    def run(self) -> str:
        """
        Executes the English corrector with the implemented rules in this function
        """
        fixed_section = re.sub("'", '’', self.text_to_correct)  # Substitute wrong apostrophe
        print("Assumption is that the text to correct never contains single quotation marks,"
              " but always beginning and end of both of them")
        # # Rules for quotation marks:
        # # Correct way is “Forgivi”ng Step" by St”ep

        # Lorem Ipsum “Forgiving Step by Step
        # Lorem Ipsum Forgiving Step by Step”
        # TODO: Count appearances of german, english quotation marks
        # TODO: parse text from left to right and replace odd appearences with “ and even ones with ”
        return self.text_to_correct
