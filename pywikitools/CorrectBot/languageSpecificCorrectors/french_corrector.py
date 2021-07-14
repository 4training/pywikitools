import re

class FrenchCorrector:
    """
    Corrects typical French typos to follow the following rules:
    * Instead of ellipsis, use "..."
    * "example" is English, "exemple" is French
    * quotation marks: « Foo » (with non-breaking whitespaces \u00a0 before/after the guillemets!)
    * quotation marks: « Foo » (no english quotation marks)
    """

    def __init__(self, text_to_correct: str):
        self.text_to_correct: str = text_to_correct

    def run(self) -> str:
        """
        Executes the French corrector with the implemented rules in this function
        """
        # Count all quotation marks
        if (len(re.findall(r'"',self.text_to_correct)) % 2) != 0:
            print('Warning: Quotation mark is missing.')
        # "(.*?[^\\])"
        # Identify quotes
        # quotation = re.compile(r'"(.*?)"')
        # fixed_section = re.sub()
        
        matched_quotation_marks = []
        for match in re.finditer(r'"', self.text_to_correct):
            matched_quotation_marks += match.span() #add position of matches
        matched_quotation_marks = list(matched_quotation_marks[0::2]) #only use first coordinate
        
        fixed_section = list(self.test_to_correct)
        for quotation_position in matched_quotation_marks:
            if matched_quotation_marks.index(quotation_position) % 2 == 0:
                fixed_section[quotation_position] = '«'
            else:
                fixed_section[quotation_position] = '»'
        fixed_section = ''.join(fixed_section)
        
        
        # insert non-breaking space
        #if re.search('«\u00A0|\u00A0»', str) == None:
        #    str = re.sub('« *','«\u00A0',re.sub(' *»','\u00A0»',str,re.MULTILINE),re.MULTILINE)
        #return str
      
      
        
        # TODO: Implement the rules listed in docstring of class
        return self.text_to_correct
