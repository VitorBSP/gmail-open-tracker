"""Tests for MIME construction and tracker URL handling."""

from tracker.client import build_html_body, build_pixel_url, create_email_message


def test_pixel_url() -> None:
    result = build_pixel_url(
        "https://example.supabase.co/functions/v1/email-open-pixel", "abc"
    )
    assert result.endswith("/email-open-pixel?id=abc")


def test_html_escapes_input() -> None:
    result = build_html_body(
        "<script>alert(1)</script>",
        "https://example.com/pixel?id=abc",
    )
    assert "&lt;script&gt;" in result


def test_html_includes_pixel() -> None:
    result = build_html_body("Hello", "https://example.com/pixel?id=abc")
    assert 'src="https://example.com/pixel?id=abc"' in result


def test_mime_includes_html() -> None:
    message = create_email_message(
        "sender@example.com",
        "recipient@example.com",
        "Hello",
        "Example message",
        "https://example.com/pixel?id=abc",
    )
    assert message.get_body(preferencelist=("html",)) is not None


def test_mime_includes_plain_text() -> None:
    message = create_email_message(
        "sender@example.com",
        "recipient@example.com",
        "Hello",
        "Example message",
        "https://example.com/pixel?id=abc",
    )
    assert "Example message" in message.get_body(
        preferencelist=("plain",)
    ).get_content()
