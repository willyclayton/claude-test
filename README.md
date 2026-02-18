# CTA Commute Tracker

Real-time train tracker for the Diversey → Merchandise Mart commute on the Brown and Purple lines.

## Purpose

Shows upcoming southbound trains at Diversey, flags which ones you can actually catch based on your walk time, and tells you when to leave.

## Tech

- **Python / Flask** — web server
- **CTA Train Tracker API** — real-time arrival data
- **SQLite** — local storage for bulk train position data (`cta_trains.py`)
- **Gunicorn** — production WSGI server
- **Railway** — hosting

## Setup

1. Clone the repo
2. Create a `.env` file with your CTA API key:
   ```
   CTA_API_KEY=your_key_here
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run locally:
   ```
   python app.py
   ```

## Considerations

- **API key** — stored in `.env` locally, set as an environment variable in Railway. Never committed to git.
- **Timezone** — the server runs in UTC; times are explicitly converted to `America/Chicago` so arrival math is correct.
- **Walk time** — hardcoded to 8 minutes. Change `WALK_MINUTES` in `app.py` to adjust.
- **Service hours** — CTA Brown/Purple lines don't run overnight. The app will show "No trains available" during those gaps.
- **Auto-refresh** — page refreshes every 30 seconds automatically.
