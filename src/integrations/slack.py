"""Slack integration helpers for escalation alerts."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import requests

from src.config.settings import settings

logger = logging.getLogger(__name__)


async def send_escalation_alert(
    *,
    session_id: str,
    user_email: str,
    user_query: str,
    assistant_answer: str,
    escalation_reason: str | None = None,
    ui_url: str | None = None,
) -> bool:
    """Send an escalation notification to Slack.

    Returns True when the request is dispatched successfully. False otherwise.
    """
    slack_webhook = settings.slack_webhook_url.strip()
    slack_bot_token = settings.slack_bot_token.strip()
    slack_channel = settings.slack_channel_id.strip()

    if not slack_webhook and not (slack_bot_token and slack_channel):
        logger.debug("Slack credentials missing; skipping escalation alert")
        return False

    link_text = f"View session: {ui_url}" if ui_url else ""
    reason = escalation_reason or "User requested human assistance."
    text_lines = [
        "*Customer escalation alert*",
        f"• User: `{user_email}`",
        f"• Session: `{session_id}`",
        f"• Latest query: {user_query}",
        f"• Assistant response: {assistant_answer}",
        f"• Reason: {reason}",
    ]
    if link_text:
        text_lines.append(link_text)
    message_text = "\n".join(text_lines)

    def _post_message() -> bool:
        try:
            if slack_webhook:
                resp = requests.post(
                    slack_webhook,
                    json={"text": message_text},
                    timeout=10,
                )
                if not resp.ok:
                    logger.warning("Slack webhook returned %s: %s", resp.status_code, resp.text)
                return resp.ok
            headers = {
                "Authorization": f"Bearer {slack_bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            }
            payload: dict[str, Any] = {"channel": slack_channel, "text": message_text}
            resp = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload,
                timeout=10,
            )
            if not resp.ok:
                logger.warning("Slack API request failed %s: %s", resp.status_code, resp.text)
                return False
            data = resp.json()
            if not data.get("ok"):
                logger.warning("Slack API error response: %s", data)
                return False
            return True
        except Exception:  # pragma: no cover - log and swallow errors
            logger.exception("Failed to send Slack escalation alert")
            return False

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _post_message)
