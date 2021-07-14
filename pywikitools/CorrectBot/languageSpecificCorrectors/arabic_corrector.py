class ArabicCorrector:
    """
    Corrects typical Arabic typos to follow the following rules:
    * TODO: Use Arabic comma symbol: instead of "," use "،"
    """

    def __init__(self, text_to_correct: str):
        self.text_to_correct: str = text_to_correct

    def run(self) -> str:
        """
        Executes the Arabic corrector with the implemented rules in this function
        """
        return self.text_to_correct
