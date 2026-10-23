import os
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

from .logger import AlertLogger
from .telegram_alert import TelegramAlert
from .email_alert import EmailAlert
from .sms_alert import SMSAlert
from .utils import format_alert_message, save_screenshot_copy



class AlertManager:
    def __init__(self, cooldown_seconds=None):
        self.cooldown_seconds = (
            int(cooldown_seconds)
            if cooldown_seconds is not None
            else int(os.getenv("ALERT_COOLDOWN_SECONDS", "30"))
        )
        self.last_sent = defaultdict(lambda: 0.0)

        self.telegram = TelegramAlert()
        self.email = EmailAlert()
        self.sms = SMSAlert()
        self.logger = AlertLogger(os.getenv("ALERT_LOG_PATH", "logs/alerts.jsonl"))

    def _cooldown_key(self, event):
        return f"{event.camera}:{event.event_type}"

    def _is_on_cooldown(self, event):
        key = self._cooldown_key(event)
        elapsed = time.time() - self.last_sent[key]
        return elapsed < self.cooldown_seconds

    def _mark_sent(self, event):
        self.last_sent[self._cooldown_key(event)] = time.time()

    def send_alert(self, event):
        if self._is_on_cooldown(event):
            result = {
                "status": "skipped",
                "reason": "cooldown",
                "event": event.to_dict()
            }
            self.logger.log(result)
            return result

        screenshot_error = None
        try:
            screenshot = save_screenshot_copy(event.screenshot_path)
            if event.screenshot_path and screenshot is None:
                screenshot_error = "Screenshot source is not a readable file"
        except (OSError, ValueError) as exc:
            screenshot = None
            screenshot_error = str(exc)
        message = format_alert_message(event)

        results = []

        telegram_result = self.telegram.send(message, screenshot)
        results.append(telegram_result)

        email_result = self.email.send(
            subject=f"FISHER Alert: {event.event_type}",
            message=message,
            screenshot_path=screenshot
        )
        results.append(email_result)

        sms_result = self.sms.send(message)
        results.append(sms_result)

        self._mark_sent(event)

        payload = {
            "status": "processed",
            "event": event.to_dict(),
            "saved_screenshot": screenshot,
            "screenshot_error": screenshot_error,
            "channel_results": results
        }

        self.logger.log(payload)
        return payload
