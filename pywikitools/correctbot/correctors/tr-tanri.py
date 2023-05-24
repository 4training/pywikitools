from .tr import TurkishCorrector


class TurkishSecularCorrector(TurkishCorrector):
    """
    Correct typos in the secular Turkish language variant (language code: tr-tanri)
    Uses all Turkish correction rules.
    Generates correct filenames for this language variant
    """
    def _compose_filename(self, converted_title: str, extension: str, is_print_pdf: bool) -> str:
        """Overwrite this to integrate Tanrı correctly into the filename

        If Tanrı is already part of the translated worksheet title, we don't need to do anything.
        If not, add _(Tanrı) at the end of the filename.
        Examples: Tanrıyı_Duymak.pdf, Şifa_(Tanrı).pdf
        """
        if "Tanrı" not in converted_title:
            converted_title += "_(Tanrı)"
        if is_print_pdf:
            converted_title += self._suffix_for_print_version()
        converted_title += extension
        return converted_title
