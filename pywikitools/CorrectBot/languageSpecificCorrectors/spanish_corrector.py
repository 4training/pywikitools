class SpanishCorrector:
    """
    Corrects typical Spanish typos to follow the following rules:
    * TODO: Instead of ellipsis, use "..."
    """

    def __init__(self, text_to_correct: str):
        self.text_to_correct: str = text_to_correct

    def run(self) -> str:
        """
        Executes Spanish arabic corrector with the implemented rules in this function
        """
        return self.text_to_correct
