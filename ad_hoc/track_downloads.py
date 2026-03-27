'''
Tracks cumulative downloads of fbi-data-api, designed to be run on GitHub Actions every day to update 
running total in ./downloads.json. Locally, run this script from this project's root directory.
'''
import json
import pypistats
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("./downloads.json")

def main():
    query = pypistats.overall("fbi-data-api", mirrors = False, format = "json")
    total = int(json.loads(query)["data"][0]["downloads"])

    state = {
        "total_downloads": total,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    STATE_FILE.write_text(json.dumps(state, indent = 2) + "\n")
    print(f"fbi-data-api has {total:,} total downloads. Written to {STATE_FILE}.")


if __name__ == "__main__":
    main()
