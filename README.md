# TikTok Live Dashboard

This project provides a Flask-based dashboard for TikTok livestreams.

## Setup

1. `pip install -r requirements.txt`
2. `python server.py`
3. Open `http://localhost:5000` in your browser.

Enter a TikTok username and click **Connect** to view live stats. Use **Disconnect** to stop watching and reset the dashboard.

All livestream events are written to `logs/events.log` and errors to `logs/errors.log` for later review.
