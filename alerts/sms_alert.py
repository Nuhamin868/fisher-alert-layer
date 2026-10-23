import os

import requests
from dotenv import load_dotenv

load_dotenv()


class SMSAlert:
    def __init__(self):
        self.api_key = os.getenv("SMS_API_KEY")
        self.phone_number = os.getenv("SMS_TO")
        self.sender_id = os.getenv("SMS_FROM", "")
        self.enabled = os.getenv("SMS_ENABLED", "false").lower() == "true"

        self.url = "https://sms.esmsafrica.io/api/messages/send"

    def is_configured(self):
        return bool(
            self.enabled
            and self.api_key
            and self.phone_number
        )

    def send(self, message):
        if not self.enabled:
            return {
                "channel": "sms",
                "sent": False,
                "reason": "disabled",
            }

        if not self.api_key:
            return {
                "channel": "sms",
                "sent": False,
                "reason": "SMS_API_KEY is not configured",
            }

        if not self.phone_number:
            return {
                "channel": "sms",
                "sent": False,
                "reason": "SMS_TO is not configured",
            }

        payload = {
            "to": self.phone_number,
            "text": message,
        }

        # Only send a sender ID if one has been configured.
        # This avoids using the unapproved default "FISHER".
        if self.sender_id:
            payload["sender_id"] = self.sender_id

        try:
            response = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15,
            )

            if response.ok:
                data = response.json()

                if not isinstance(data, dict):
                    return {"channel": "sms", "sent": False, "reason": "Invalid provider response"}
                status = str(data.get("status", "")).lower()
                if data.get("error") or data.get("success") is False or status in {
                    "failed", "failure", "rejected", "error", "undelivered", "cancelled"
                } or not data.get("id"):
                    return {
                        "channel": "sms", "sent": False,
                        "status": data.get("status"),
                        "reason": str(data.get("error") or "Provider did not confirm message acceptance"),
                    }
                return {
                    "channel": "sms",
                    "sent": True,
                    "message_id": data.get("id"),
                    "status": data.get("status"),
                }

            return {
                "channel": "sms",
                "sent": False,
                "status_code": response.status_code,
                "reason": response.text,
            }

        except (requests.RequestException, ValueError) as exc:
            return {
                "channel": "sms",
                "sent": False,
                "reason": str(exc),
            }
