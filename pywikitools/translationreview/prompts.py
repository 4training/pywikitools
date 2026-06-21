from os.path import abspath, dirname, join
from typing import Final

PROMPTS_DIR: Final[str] = join(dirname(abspath(__file__)), "prompts")

LANGUAGE_NAMES: Final[dict[str, str]] = {
    "tr": "Turkish",
    "de": "German",
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "ar": "Arabic",
    "fa": "Persian",
    "ru": "Russian",
    "uk": "Ukrainian",
    "pl": "Polish",
    "it": "Italian",
    "nl": "Dutch",
    "ro": "Romanian",
    "sq": "Albanian",
    "sw": "Swahili",
    "lg": "Luganda",
    "kn": "Kannada",
    "ta": "Tamil",
    "ky": "Kyrgyz",
    "nb": "Norwegian",
}


def language_name(language_code: str) -> str:
    return LANGUAGE_NAMES.get(language_code, language_code)


def _load_template(filename: str) -> str:
    path = join(PROMPTS_DIR, filename)
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _load_guidelines(language_code: str) -> str:
    guidelines_path = join(PROMPTS_DIR, "guidelines", f"{language_code}.txt")
    try:
        with open(guidelines_path, encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        default_path = join(PROMPTS_DIR, "guidelines", "default.txt")
        with open(default_path, encoding="utf-8") as handle:
            return handle.read()


def build_review_prompt(
    *,
    language_code: str,
    english: str,
    reference: str,
    target: str,
) -> str:
    template = _load_template("review.txt")
    return template.format(
        target_language_name=language_name(language_code),
        english=english,
        reference=reference,
        target=target,
        guidelines=_load_guidelines(language_code),
    )


def build_translate_prompt(
    *,
    language_code: str,
    english: str,
    reference: str,
    target: str,
    review: str = "",
) -> str:
    guidelines = _load_guidelines(language_code)
    if review:
        template = _load_template("translate_after_review.txt")
        return template.format(
            target_language_name=language_name(language_code),
            english=english,
            reference=reference,
            target=target,
            review=review,
            guidelines=guidelines,
        )
    template = _load_template("translate.txt")
    return template.format(
        target_language_name=language_name(language_code),
        english=english,
        reference=reference,
        target=target,
        guidelines=guidelines,
    )
