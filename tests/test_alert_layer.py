import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

with patch("dotenv.load_dotenv"):
    from alerts import AlertManager
    from alerts.models import AlertEvent
    from alerts.utils import save_screenshot_copy
    from alerts.telegram_alert import TelegramAlert
    from alerts.email_alert import EmailAlert
    from alerts.sms_alert import SMSAlert


class AlertLayerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / "alerts.jsonl"
        self.env = patch.dict(os.environ, {
            "ENABLE_TELEGRAM": "false", "ENABLE_EMAIL": "false",
            "SMS_ENABLED": "false", "FISHER_DB_SYNC_ENABLED": "false",
            "ALERT_LOG_PATH": str(self.log), "FISHER_CAMERA_ID": "1",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.network = patch("requests.post", side_effect=AssertionError("Unexpected network request"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def event(self, camera="Camera 01"):
        return AlertEvent("Intrusion", camera, 0.94, "2026-10-23T12:00:00", message="Test event")

    def test_disabled_delivery_and_structured_log(self):
        result = AlertManager().send_alert(self.event())
        self.assertEqual(result["status"], "processed")
        self.assertEqual(len(result["channel_results"]), 3)
        self.assertTrue(all(not r["sent"] for r in result["channel_results"]))
        record = json.loads(self.log.read_text())
        self.assertEqual(record["event"]["camera"], "Camera 01")
        self.assertIn("logged_at", record)

    def test_duplicate_cooldown_is_scoped_to_camera_and_expires(self):
        manager = AlertManager(cooldown_seconds=30)
        with patch("alerts.alert_manager.time.time", return_value=100):
            self.assertEqual(manager.send_alert(self.event())["status"], "processed")
            self.assertEqual(manager.send_alert(self.event())["reason"], "cooldown")
            self.assertEqual(manager.send_alert(self.event("Camera 02"))["status"], "processed")
        with patch("alerts.alert_manager.time.time", return_value=131):
            self.assertEqual(manager.send_alert(self.event())["status"], "processed")

    def test_screenshot_copy_and_missing_source(self):
        source = self.root / "frame.jpg"
        source.write_bytes(b"fixture-image-bytes")
        dest = save_screenshot_copy(str(source), self.root / "evidence")
        self.assertEqual(Path(dest).read_bytes(), source.read_bytes())
        self.assertNotEqual(Path(dest), source)
        self.assertIsNone(save_screenshot_copy(str(self.root / "missing.jpg")))

    def test_telegram_text_and_photo_requests_are_mocked(self):
        os.environ.update(ENABLE_TELEGRAM="true", TELEGRAM_BOT_TOKEN="test", TELEGRAM_CHAT_ID="test")
        photo = self.root / "frame.jpg"
        photo.write_bytes(b"fixture")
        with patch("alerts.telegram_alert.requests.post", return_value=Mock(json=Mock(return_value={"ok": True}))) as post:
            channel = TelegramAlert()
            self.assertTrue(channel.send("text")["sent"])
            self.assertTrue(channel.send("text", str(photo))["sent"])
            self.assertTrue(post.call_args_list[0].args[0].endswith("/sendMessage"))
            self.assertTrue(post.call_args_list[1].args[0].endswith("/sendPhoto"))

    def test_email_delivery_is_mocked(self):
        os.environ.update(ENABLE_EMAIL="true", SMTP_HOST="smtp.invalid", SMTP_USER="user", SMTP_PASSWORD="test", ALERT_FROM_EMAIL="from@example.invalid", ALERT_TO_EMAIL="to@example.invalid")
        with patch("alerts.email_alert.smtplib.SMTP") as smtp:
            self.assertTrue(EmailAlert().send("subject", "message")["sent"])
            smtp.return_value.__enter__.return_value.starttls.assert_called_once()
            smtp.return_value.__enter__.return_value.send_message.assert_called_once()

    def test_sms_request_is_mocked(self):
        os.environ.update(SMS_ENABLED="true", SMS_API_KEY="test", SMS_TO="test")
        response = Mock(ok=True)
        response.json.return_value = {"id": "123", "status": "queued"}
        with patch("alerts.sms_alert.requests.post", return_value=response) as post:
            result = SMSAlert().send("message")
        self.assertTrue(result["sent"])
        self.assertEqual(result["message_id"], "123")
        self.assertEqual(post.call_args.kwargs["json"]["text"], "message")


    def test_screenshot_failure_does_not_stop_channels(self):
        manager = AlertManager()
        with patch("alerts.alert_manager.save_screenshot_copy", side_effect=PermissionError("denied")):
            result = manager.send_alert(self.event())
        self.assertEqual(result["status"], "processed")
        self.assertEqual(len(result["channel_results"]), 3)
        self.assertEqual(result["screenshot_error"], "denied")

    def test_screenshot_copies_do_not_overwrite(self):
        source = self.root / "image.png"
        source.write_bytes(b"first")
        first = save_screenshot_copy(source, self.root / "evidence")
        source.write_bytes(b"second")
        second = save_screenshot_copy(source, self.root / "evidence")
        self.assertNotEqual(first, second)
        self.assertEqual(Path(first).read_bytes(), b"first")
        self.assertIsNone(save_screenshot_copy(self.root, self.root / "evidence"))

    def test_sms_rejection_and_invalid_json_are_failures(self):
        os.environ.update(SMS_ENABLED="true", SMS_API_KEY="test", SMS_TO="test")
        for payload in ({"status": "failed"}, {"error": "rejected"}, {}, []):
            with self.subTest(payload=payload), patch("alerts.sms_alert.requests.post", return_value=Mock(ok=True, json=Mock(return_value=payload))):
                self.assertFalse(SMSAlert().send("test")["sent"])
        with patch("alerts.sms_alert.requests.post", return_value=Mock(ok=True, json=Mock(side_effect=ValueError("invalid JSON")))):
            self.assertFalse(SMSAlert().send("test")["sent"])

    def test_telegram_rejection_is_failure(self):
        os.environ.update(ENABLE_TELEGRAM="true", TELEGRAM_BOT_TOKEN="test", TELEGRAM_CHAT_ID="test")
        with patch("alerts.telegram_alert.requests.post", return_value=Mock(json=Mock(return_value={"ok": False}))):
            self.assertFalse(TelegramAlert().send("test")["sent"])

if __name__ == "__main__":
    unittest.main()
