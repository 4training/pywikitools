from . import universal

class GermanCorrector(universal.LanguageCorrector, universal.UniversalCorrector):
    """
    Corrects typical German typos to follow the following rules:
    * TODO: no plain quotation marks like "
    * TODO: no English quotation marks like ”
    * TODO: German quotation marks consist of two parts: at the beginning and “ at the and
    """

    def correct_replace_a_with_o(self, text: str) -> str:
        """TODO for testing only: Replace a with o"""
        return text.replace("a", "o")
