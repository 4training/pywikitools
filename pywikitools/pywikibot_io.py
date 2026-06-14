"""Shared pywikibot helpers for pywikitools bots."""

import pywikibot


def save_page(
    page: pywikibot.page.BasePage,
    new_text: str,
    summary: str,
    *,
    simulate: bool = False,
) -> None:
    """Assign new page text and save; in simulate mode show a pywikibot diff only."""
    if simulate:
        pywikibot.showDiff(page.text, new_text)
        return
    page.text = new_text
    page.save(summary)
