# FISHER AI CCTV System - Standalone Alert Layer

This module is designed to work independently from the main FISHER backend.
It can later be connected to the Analytics Layer, YOLO detection pipeline, or FastAPI service.

## Features

- Telegram alerts
- Email alerts
- SMS delivery using eSMS Africa
- Alert message formatting
- Screenshot copying/evidence handling
- Cooldown / duplicate-alert prevention
- JSONL alert logging
- Simple test and demo scripts
- Environment-variable configuration

## Architecture

Analytics / AI Detection
        |
        v
   AlertManager
        |
        +--> Telegram
        +--> Email
        +--> SMS
        +--> Screenshot evidence
        +--> Alert logs

## 1. Setup

Open this folder in VS Code.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

Windows:
```bash
.venv\Scripts\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in only the services you want to test.

## 2. Telegram setup

Create a Telegram bot using BotFather.
Place the bot token and destination chat ID in `.env`.

Example:

```env
ENABLE_TELEGRAM=true
TELEGRAM_BOT_TOKEN=replace_me
TELEGRAM_CHAT_ID=replace_me
```

Never commit the real `.env` file to GitHub.

## 3. Run the standalone demo

```bash
python demo.py
# Explicitly opt in to configured live services:
python demo.py --live
```

## 4. Run the cooldown test

```bash
python tests/test_alert.py
```

The first event should be processed.
The immediate duplicate should be skipped because of cooldown.

## 5. How the backend will connect later

The backend or Analytics Layer only needs to create an event and call:

```python
from alerts import AlertManager
from alerts.models import AlertEvent

manager = AlertManager()

event = AlertEvent(
    event_type="Intrusion Detected",
    camera="Camera 01",
    confidence=0.94,
    timestamp="2026-09-08T14:30:00",
    severity="HIGH",
    screenshot_path="path/to/frame.jpg"
)

manager.send_alert(event)
```

This means the AI team does not need to know how Telegram, email, cooldown,
or logging works internally.

## 6. Suggested integration contract

The Analytics Layer can send data shaped like:

```json
{
  "event_type": "Intrusion Detected",
  "camera": "Camera 01",
  "confidence": 0.94,
  "timestamp": "2026-09-08T14:30:00",
  "severity": "HIGH",
  "screenshot_path": "screenshots/frame_001.jpg"
}
```

## 7. Notes for the team leader

This project is intentionally modular.
The Alert Layer can be integrated after the detection/analytics pipeline is ready.

Recommended future improvements:
- FastAPI endpoint for receiving alerts
- PostgreSQL alert-table integration
- Retry queue for failed notifications
- Configurable dashboard alert rules
- Per-user notification preferences
- Delivery receipts and retry handling

## API and dashboard

Run `uvicorn api:app --host 127.0.0.1 --port 8000` after installing requirements.
Open `http://127.0.0.1:8000/dashboard` for recorded alerts and `/docs` for the API.
The API has no authentication; keep it on localhost or behind an authenticated gateway.
The demo disables delivery unless `--live` is supplied. A processed event does not imply successful delivery: inspect channel results.

Run isolated regression tests with `python -m unittest discover -s tests -p test_alert_layer.py -v`.
The legacy `tests/test_alert.py` is a manual demo and may send configured notifications.

Optional object detection requires `pip install -r requirements-detection.txt`.
It runs separately and is not wired to alert dispatch. Its model may download on first use.

Screenshot copies have unique names. Evidence-copy failures are recorded without stopping notifications.
Email attachments use the source MIME type. SMS acceptance requires a message ID and no explicit failure response.
Cooldown is in memory, includes unsuccessful dispatch attempts, and is not shared across processes.
Notification delivery is synchronous; no retry queue is implemented.
