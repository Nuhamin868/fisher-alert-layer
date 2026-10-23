from pathlib import Path
from datetime import datetime
import shutil
from uuid import uuid4

def format_alert_message(event):
    confidence_pct = round(event.confidence * 100, 2)
    custom_message = f"\nDetails: {event.message}" if event.message else ""
    return (
        "🚨 FISHER SECURITY ALERT\n\n"
        f"Event: {event.event_type}\n"
        f"Camera: {event.camera}\n"
        f"Confidence: {confidence_pct}%\n"
        f"Severity: {event.severity}\n"
        f"Time: {event.timestamp}"
        f"{custom_message}\n\n"
        "Please check the CCTV feed."
    )

def save_screenshot_copy(source_path, screenshots_dir="screenshots"):
    if not source_path:
        return None

    source = Path(source_path)
    if not source.is_file():
        return None

    dest_dir = Path(screenshots_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{source.stem}_{stamp}_{uuid4().hex}{source.suffix}"
    shutil.copy2(source, dest)
    return str(dest)
