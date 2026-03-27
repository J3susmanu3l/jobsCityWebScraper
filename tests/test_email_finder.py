from jobs_scraper.email_finder import _extract_first_email


def test_extract_first_email_found() -> None:
    text = "Contact us at hello@example.com for details."
    assert _extract_first_email(text) == "hello@example.com"


def test_extract_first_email_missing() -> None:
    text = "No contact data here."
    assert _extract_first_email(text) is None

