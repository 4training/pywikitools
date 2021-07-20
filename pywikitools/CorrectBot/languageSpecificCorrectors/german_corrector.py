class GermanCorrector:
    """
    Corrects typical French typos to follow the following rules:
    * TODO: no plain quotation marks like "
    * TODO: no English quotation marks like ”
    * TODO: German quotation marks consist of two parts: at the beginning and “ at the and
    """

    def __init__(self, text_to_correct: str):
        self.text_to_correct: str = text_to_correct

    def run(self) -> str:
        """
        Executes the German corrector with the implemented rules in this function
        """
        # TODO: Implement the rules listed in docstring of class
        return self.text_to_correct
