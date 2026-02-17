import os
import requests
from datetime import datetime
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("CTA_API_KEY")
API_URL = "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
DIVERSEY_STATION_ID = 40530
WALK_MINUTES = 8


def get_trains():
    params = {
        "key": API_KEY,
        "mapid": DIVERSEY_STATION_ID,
        "outputType": "JSON"
    }
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    etas = response.json()["ctatt"]["eta"]

    trains = []
    now = datetime.now()
    for eta in etas:
        if eta.get("rt") not in ("Brn", "P") or eta.get("trDr") != "5":
            continue
        arr_time = datetime.fromisoformat(eta["arrT"])
        minutes = round((arr_time - now).total_seconds() / 60)
        trains.append({
            "route": "Brown" if eta["rt"] == "Brn" else "Purple",
            "dest": eta.get("destNm", ""),
            "minutes": minutes,
            "catchable": minutes >= WALK_MINUTES,
            "approaching": eta.get("isApp") == "1",
            "delayed": eta.get("isDly") == "1",
        })

    return sorted(trains, key=lambda x: x["minutes"]), now


@app.route("/")
def index():
    trains, now = get_trains()

    next_catchable = next((t for t in trains if t["catchable"]), None)
    if next_catchable:
        if next_catchable["minutes"] <= WALK_MINUTES:
            urgency = "leave-now"
            message = "Leave now!"
        elif next_catchable["minutes"] <= WALK_MINUTES + 3:
            urgency = "soon"
            message = f"Leave in ~{next_catchable['minutes'] - WALK_MINUTES} min"
        else:
            urgency = "ok"
            message = f"Leave in ~{next_catchable['minutes'] - WALK_MINUTES} min"
    else:
        urgency = "none"
        message = "No trains available"

    rows = ""
    for t in trains:
        tag = ""
        if t["approaching"]:
            tag = '<span class="tag approaching">Approaching</span>'
        elif t["delayed"]:
            tag = '<span class="tag delayed">Delayed</span>'

        status_class = "catchable" if t["catchable"] else "too-soon"
        icon = "✓" if t["catchable"] else "✗"
        mins_label = f"{t['minutes']} min" if t["minutes"] > 0 else "Now"

        rows += f"""
        <tr class="{status_class}">
            <td class="icon">{icon}</td>
            <td><span class="route {t['route'].lower()}">{t['route']}</span></td>
            <td>to {t['dest']}</td>
            <td class="mins">{mins_label}</td>
            <td>{tag}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <title>Diversey → Merch Mart</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0f0f0f;
            color: #f0f0f0;
            padding: 24px 16px;
            max-width: 480px;
            margin: 0 auto;
        }}
        h1 {{ font-size: 1.1rem; color: #aaa; font-weight: 400; margin-bottom: 4px; }}
        .time {{ font-size: 0.85rem; color: #555; margin-bottom: 20px; }}
        .banner {{
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 24px;
            font-size: 1.4rem;
            font-weight: 700;
        }}
        .ok      {{ background: #1a3a1a; color: #4caf50; }}
        .soon    {{ background: #3a2a00; color: #ffc107; }}
        .leave-now {{ background: #3a1a1a; color: #f44336; }}
        .none    {{ background: #222; color: #aaa; }}
        table {{ width: 100%; border-collapse: collapse; }}
        tr {{ border-bottom: 1px solid #1e1e1e; }}
        td {{ padding: 12px 6px; vertical-align: middle; }}
        .icon {{ font-size: 1rem; width: 28px; }}
        .catchable .icon {{ color: #4caf50; }}
        .too-soon .icon   {{ color: #444; }}
        .too-soon td      {{ color: #555; }}
        .route {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 700;
            color: white;
        }}
        .route.brown  {{ background: #62361b; }}
        .route.purple {{ background: #522398; }}
        .mins {{ font-weight: 600; text-align: right; padding-right: 12px; }}
        .tag {{
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .approaching {{ background: #1a3a3a; color: #4dd0e1; }}
        .delayed     {{ background: #3a1a1a; color: #f44336; }}
        .footer {{ margin-top: 16px; font-size: 0.75rem; color: #333; text-align: center; }}
    </style>
</head>
<body>
    <h1>Diversey → Merchandise Mart</h1>
    <div class="time">Updated {now.strftime('%-I:%M %p')} &nbsp;·&nbsp; {WALK_MINUTES} min walk &nbsp;·&nbsp; auto-refreshes every 30s</div>
    <div class="banner {urgency}">{message}</div>
    <table>
        {rows}
    </table>
    <div class="footer">✓ = catchable &nbsp;·&nbsp; ✗ = leaves before you arrive</div>
</body>
</html>"""
    return html


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
