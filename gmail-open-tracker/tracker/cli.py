"""CLI for sending tracked messages and inspecting image requests."""

import argparse
import json
import os
from pathlib import Path

from tracker.client import (
    build_pixel_url,
    create_email_message,
    create_gmail_client,
    send_message,
    tracker_repository_from_environment,
)


def send_tracked_email(arguments: argparse.Namespace) -> None:
    gmail_client = create_gmail_client(
        credentials_file=arguments.credentials_file,
        token_file=arguments.token_file,
    )
    message_text = arguments.body_file.read_text(encoding="utf-8")
    profile = gmail_client.users().getProfile(userId="me").execute()
    sender = str(profile["emailAddress"])
    repository = tracker_repository_from_environment()
    tracking_token = repository.register(arguments.recipient, arguments.subject)
    email_message = create_email_message(
        sender=sender,
        recipient=arguments.recipient,
        subject=arguments.subject,
        message_text=message_text,
        pixel_url=build_pixel_url(
            os.environ["TRACKER_FUNCTION_URL"], tracking_token
        ),
    )
    result = send_message(gmail_client, email_message)
    repository.associate_gmail_message(
        tracking_token, str(result["id"]), str(result["threadId"])
    )
    print(json.dumps({
        "message_id": result["id"],
        "tracking_token": tracking_token,
    }))


def inspect_tracking_events(arguments: argparse.Namespace) -> None:
    repository = tracker_repository_from_environment()
    print(json.dumps({
        "image_requests": repository.list_requests(arguments.token)
    }))


def main() -> None:
    parser = argparse.ArgumentParser(description="Gmail image request tracker")
    commands = parser.add_subparsers(dest="command", required=True)
    send_command = commands.add_parser("send")
    send_command.add_argument("--recipient", required=True)
    send_command.add_argument("--subject", required=True)
    send_command.add_argument("--body-file", required=True, type=Path)
    send_command.add_argument(
        "--credentials-file",
        type=Path,
        default=Path("credentials.json"),
    )
    send_command.add_argument(
        "--token-file",
        type=Path,
        default=Path("token.json"),
    )
    status_command = commands.add_parser("status")
    status_command.add_argument("--token", required=True)
    arguments = parser.parse_args()
    if arguments.command == "send":
        send_tracked_email(arguments)
    else:
        inspect_tracking_events(arguments)


if __name__ == "__main__":
    main()
