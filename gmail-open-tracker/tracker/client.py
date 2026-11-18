"""Gmail message construction and Supabase event persistence."""

import base64
import html
import os
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def build_pixel_url(function_url: str, tracking_token: str) -> str:
    return f"{function_url.rstrip('/')}?{urlencode({'id': tracking_token})}"


def build_html_body(message_text: str, pixel_url: str) -> str:
    escaped_text = html.escape(message_text).replace("\n", "<br>\n")
    escaped_url = html.escape(pixel_url, quote=True)
    return (
        "<!doctype html><html><body>"
        f"<div>{escaped_text}</div>"
        f'<img src="{escaped_url}" width="1" height="1" alt="" '
        'style="width:1px;height:1px;border:0">'
        "</body></html>"
    )


def create_email_message(
    sender: str,
    recipient: str,
    subject: str,
    message_text: str,
    pixel_url: str,
) -> EmailMessage:
    email_message = EmailMessage()
    email_message["From"] = sender
    email_message["To"] = recipient
    email_message["Subject"] = subject
    email_message.set_content(message_text)
    email_message.add_alternative(
        build_html_body(message_text, pixel_url), subtype="html"
    )
    return email_message


class TrackerRepository:
    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self.supabase_url = supabase_url.rstrip("/")
        self.request_headers = {
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        }

    def register(self, recipient: str, subject: str) -> str:
        response = requests.post(
            f"{self.supabase_url}/rest/v1/caucao_email_tracker_messages",
            headers={**self.request_headers, "Prefer": "return=representation"},
            json={"recipient": recipient, "subject": subject},
            timeout=20,
        )
        response.raise_for_status()
        return str(response.json()[0]["token"])

    def associate_gmail_message(
        self, token: str, message_id: str, thread_id: str
    ) -> None:
        response = requests.patch(
            f"{self.supabase_url}/rest/v1/caucao_email_tracker_messages",
            headers=self.request_headers,
            params={"token": f"eq.{token}"},
            json={"gmail_message_id": message_id, "gmail_thread_id": thread_id},
            timeout=20,
        )
        response.raise_for_status()

    def list_requests(self, token: str) -> list[str]:
        response = requests.get(
            f"{self.supabase_url}/rest/v1/caucao_email_tracker_requests",
            headers=self.request_headers,
            params={
                "token": f"eq.{token}",
                "select": "requested_at",
                "order": "requested_at.asc",
            },
            timeout=20,
        )
        response.raise_for_status()
        return [str(event["requested_at"]) for event in response.json()]


def load_gmail_credentials(credentials_file: Path, token_file: Path) -> Any:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    credentials: Credentials | None = None
    if token_file.exists():
        credentials = Credentials.from_authorized_user_file(
            str(token_file), GMAIL_SCOPES
        )
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif credentials is None or not credentials.valid:
        oauth_flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_file), GMAIL_SCOPES
        )
        credentials = oauth_flow.run_local_server(port=0)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def create_gmail_client(credentials_file: Path, token_file: Path) -> Any:
    from googleapiclient.discovery import build

    return build(
        "gmail",
        "v1",
        credentials=load_gmail_credentials(credentials_file, token_file),
    )


def send_message(
    gmail_client: Any,
    email_message: EmailMessage,
    thread_id: str | None = None,
) -> dict[str, Any]:
    encoded_message = base64.urlsafe_b64encode(
        email_message.as_bytes()
    ).decode("ascii")
    payload: dict[str, str] = {"raw": encoded_message}
    if thread_id:
        payload["threadId"] = thread_id
    return gmail_client.users().messages().send(
        userId="me", body=payload
    ).execute()


def tracker_repository_from_environment() -> TrackerRepository:
    return TrackerRepository(
        supabase_url=os.environ["SUPABASE_URL"],
        service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )
