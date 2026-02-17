import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CTA_API_KEY")

API_URL = "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
DIVERSEY_STATION_ID = 40530
WALK_MINUTES = 8


def fetch_arrivals(station_id):
    params = {
        "key": API_KEY,
        "mapid": station_id,
        "outputType": "JSON"
    }
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()


def main():
    now = datetime.now()
    data = fetch_arrivals(DIVERSEY_STATION_ID)
    etas = data["ctatt"]["eta"]

    # Brown and Purple lines southbound toward Merchandise Mart
    trains = []
    for eta in etas:
        route = eta.get("rt")
        direction = eta.get("trDr")
        dest = eta.get("destNm", "")

        # Only southbound Brown/Purple trains (direction 5 = toward Loop)
        if route not in ("Brn", "P") or direction != "5":
            continue

        arr_time = datetime.fromisoformat(eta["arrT"])
        minutes_away = round((arr_time - now).total_seconds() / 60)
        catchable = minutes_away >= WALK_MINUTES

        trains.append({
            "route": "Brown" if route == "Brn" else "Purple",
            "dest": dest,
            "minutes": minutes_away,
            "catchable": catchable,
            "approaching": eta.get("isApp") == "1",
            "delayed": eta.get("isDly") == "1",
        })

    trains.sort(key=lambda x: x["minutes"])

    print(f"\n{'='*45}")
    print(f"  Diversey → Merchandise Mart")
    print(f"  {now.strftime('%I:%M %p')}  |  Walk time: {WALK_MINUTES} min")
    print(f"{'='*45}")

    if not trains:
        print("  No southbound trains found.")
    else:
        for t in trains:
            status = ""
            if t["approaching"]:
                status = " [APPROACHING]"
            elif t["delayed"]:
                status = " [DELAYED]"

            catchable_flag = "CATCH IT" if t["catchable"] else "too soon"
            mins = t["minutes"]
            label = f"{mins} min" if mins > 0 else "Now"

            print(
                f"  {'✓' if t['catchable'] else '✗'}  "
                f"{t['route']:<7} to {t['dest']:<20} "
                f"{label:<8} <- {catchable_flag}{status}"
            )

    print(f"{'='*45}\n")


if __name__ == "__main__":
    main()
