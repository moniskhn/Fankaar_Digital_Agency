"""
Fankaar Digital — WhatsApp Integration (Twilio)
Send/receive messages via Twilio WhatsApp API.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.models import DailyReport


class WhatsAppService:
    """WhatsApp messaging service using Twilio API."""

    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_whatsapp_number
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"

    @property
    def is_configured(self) -> bool:
        """Check if Twilio credentials are properly configured."""
        if not all([self.account_sid, self.auth_token, self.from_number]):
            return False
        if not self.account_sid.startswith("AC"):
            return False
        return True

    def _validate_credentials(self) -> None:
        if not self.account_sid:
            raise ValueError("Twilio Account SID not configured")
        if not self.auth_token:
            raise ValueError("Twilio Auth Token not configured")
        if not self.from_number:
            raise ValueError("Twilio WhatsApp number not configured")
        if not self.account_sid.startswith("AC"):
            raise ValueError(
                f"Invalid Twilio Account SID: '{self.account_sid[:10]}...'. "
                "Must start with 'AC'. Get the correct one from https://console.twilio.com/"
            )

    async def send_message(self, to_number: str, body: str) -> bool:
        """
        Send a WhatsApp message via Twilio.

        Args:
            to_number: Recipient WhatsApp number (with country code)
            body: Message body text

        Returns:
            True if sent successfully
        """
        try:
            self._validate_credentials()
        except ValueError as e:
            # If any credential is set but invalid, it's an error (return False)
            # If all credentials are EMPTY, we treat it as DEV mode (return True)
            if not any([self.account_sid, self.auth_token, self.from_number]):
                print(f"[WhatsApp DEV] To: {to_number}\n{body[:200]}...")
                return True

            print(f"[WhatsApp Error] {e}")
            return False

        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        if not self.from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{self.from_number}"
        else:
            from_number = self.from_number

        url = f"{self.base_url}/Messages.json"
        data = {
            "From": from_number,
            "To": to_number,
            "Body": body,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    data=data,
                    auth=(self.account_sid, self.auth_token),
                    timeout=30.0,
                )
                resp.raise_for_status()
                result = resp.json()
                return result.get("status") in ["queued", "sending", "sent"]
        except Exception as e:
            print(f"[WhatsApp Error] Failed to send: {e}")
            return False

    async def send_daily_report(self, report: DailyReport, to_number: str) -> bool:
        """
        Format and send a daily report via WhatsApp.
        Splits long reports into multiple messages if needed.
        """
        from app.agents.jon_ceo import JonCEO
        ceo = JonCEO()
        formatted = ceo.format_report_for_whatsapp(report)

        # WhatsApp message limit ~1600 chars, but we want shorter for readability
        MAX_LEN = 1500

        if len(formatted) <= MAX_LEN:
            return await self.send_message(to_number, formatted)

        # Split into multiple messages
        parts = self._split_message(formatted, MAX_LEN)
        total = len(parts)

        success = True
        for i, part in enumerate(parts, 1):
            header = f"📄 *Report {i}/{total}*\n\n" if total > 1 else ""
            part_text = header + part
            result = await self.send_message(to_number, part_text)
            if not result:
                success = False

        return success

    def _split_message(self, text: str, max_len: int) -> List[str]:
        """Split a long message into readable parts at natural boundaries."""
        if len(text) <= max_len:
            return [text]

        parts = []
        lines = text.split("\n")
        current = ""

        for line in lines:
            if len(current) + len(line) + 1 > max_len and current:
                parts.append(current.strip())
                current = line
            else:
                current = current + "\n" + line if current else line

        if current:
            parts.append(current.strip())

        return parts if parts else [text[:max_len]]

    async def parse_incoming_message(self, from_number: str, body: str) -> Dict[str, Any]:
        """
        Parse an incoming WhatsApp message from the owner.

        Args:
            from_number: Sender's WhatsApp number
            body: Message body

        Returns:
            Parsed message dict with intent and actions
        """
        body_lower = body.lower().strip()

        # Detect intent
        intent = "general"
        if any(k in body_lower for k in ["report", "update", "status", "briefing"]):
            intent = "request_report"
        elif any(k in body_lower for k in ["approve", "yes", "go ahead", "ok"]):
            intent = "approve"
        elif any(k in body_lower for k in ["reject", "no", "cancel", "stop"]):
            intent = "reject"
        elif any(k in body_lower for k in ["urgent", "asap", "emergency"]):
            intent = "urgent"
        elif any(k in body_lower for k in ["task", "assign", "delegate"]):
            intent = "delegate"

        return {
            "from_number": from_number,
            "body": body,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat(),
            "parsed": True,
        }

    async def handle_owner_reply(self, reply: str, from_number: str) -> str:
        """
        Handle a reply from the owner.
        Routes to CEO and returns a response.
        """
        from app.agents.jon_ceo import JonCEO

        ceo = JonCEO()

        # Store the reply
        parsed = await self.parse_incoming_message(from_number, reply)

        # Handle different intents
        if parsed["intent"] == "request_report":
            report = await ceo.generate_daily_report()
            await self.send_daily_report(report, from_number)
            return "Report sent to your WhatsApp."

        elif parsed["intent"] == "approve":
            response = await ceo.handle_owner_message(f"approve: {reply}")
            return response

        elif parsed["intent"] == "reject":
            response = await ceo.handle_owner_message(f"reject: {reply}")
            return response

        else:
            # General message to CEO
            response = await ceo.handle_owner_message(reply)
            return response

    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """Get the delivery status of a sent message."""
        if not self.is_configured:
            return {"status": "unknown", "configured": False}

        url = f"{self.base_url}/Messages/{message_sid}.json"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, auth=(self.account_sid, self.auth_token))
                resp.raise_for_status()
                data = resp.json()
                return {
                    "status": data.get("status"),
                    "to": data.get("to"),
                    "body_preview": data.get("body", "")[:50],
                    "date_sent": data.get("date_sent"),
                    "error_message": data.get("error_message"),
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}
