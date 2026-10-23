import os
import smtplib
import mimetypes
from email.message import EmailMessage

class EmailAlert:
    def __init__(self):
        self.enabled = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("ALERT_FROM_EMAIL")
        self.to_email = os.getenv("ALERT_TO_EMAIL")

    def is_configured(self):
        values = [
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.from_email,
            self.to_email,
        ]
        return self.enabled and all(values)

    def send(self, subject, message, screenshot_path=None):
        if not self.is_configured():
            return {"channel": "email", "sent": False, "reason": "not configured"}

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            msg.set_content(message)

            if screenshot_path and os.path.exists(screenshot_path):
                with open(screenshot_path, "rb") as f:
                    data = f.read()
                content_type = mimetypes.guess_type(screenshot_path)[0] or "application/octet-stream"
                maintype, subtype = content_type.split("/", 1)
                msg.add_attachment(
                    data,
                    maintype=maintype,
                    subtype=subtype,
                    filename=os.path.basename(screenshot_path)
                )

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return {"channel": "email", "sent": True}
        except Exception as exc:
            return {"channel": "email", "sent": False, "reason": str(exc)}
