"""Demonstrate the alert layer; delivery requires an explicit --live option."""
import argparse
import json
import os
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="FISHER Alert Layer demonstration")
    parser.add_argument("--live", action="store_true", help="Use configured notification services")
    parser.add_argument("--screenshot", help="Optional existing screenshot file")
    args = parser.parse_args()
    if not args.live:
        for name in ("ENABLE_TELEGRAM", "ENABLE_EMAIL", "SMS_ENABLED", "FISHER_DB_SYNC_ENABLED"):
            os.environ[name] = "false"
    from alerts import AlertManager
    from alerts.models import AlertEvent
    manager = AlertManager(cooldown_seconds=30)
    event = AlertEvent(
        event_type="Restricted Area Intrusion", camera="Camera 01",
        confidence=0.96, timestamp=datetime.now().isoformat(timespec="seconds"),
        severity="HIGH", screenshot_path=args.screenshot,
        message="Standalone demonstration by Nuhamin Anbese; simulated event."
    )
    print(json.dumps(manager.send_alert(event), indent=2, ensure_ascii=False))
    print(json.dumps(manager.send_alert(event), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
