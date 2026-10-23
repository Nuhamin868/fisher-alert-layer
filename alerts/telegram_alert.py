import os
import requests

class TelegramAlert:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = os.getenv("ENABLE_TELEGRAM", "false").lower() == "true"

    def is_configured(self):
        return bool(self.bot_token and self.chat_id and self.enabled)

    def send(self, message, screenshot_path=None):
        if not self.is_configured():
            return {"channel": "telegram", "sent": False, "reason": "not configured"}

        base = f"https://api.telegram.org/bot{self.bot_token}"

        try:
            if screenshot_path and os.path.exists(screenshot_path):
                with open(screenshot_path, "rb") as photo:
                    response = requests.post(
                        f"{base}/sendPhoto",
                        data={"chat_id": self.chat_id, "caption": message},
                        files={"photo": photo},
                        timeout=15
                    )
            else:
                response = requests.post(
                    f"{base}/sendMessage",
                    data={"chat_id": self.chat_id, "text": message},
                    timeout=15
                )

            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or data.get("ok") is not True:
                return {"channel": "telegram", "sent": False, "reason": "Telegram did not confirm delivery"}
            return {"channel": "telegram", "sent": True}
        except Exception as exc:
            return {"channel": "telegram", "sent": False, "reason": str(exc)}
