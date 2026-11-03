#!/usr/bin/env python3
"""Track TV shows via TVMaze, store subscriptions and compute next episodes."""
import argparse
import datetime as dt
import http.server
import json
import os
import sqlite3
import tempfile
import threading
import urllib.parse
import urllib.request

API = "https://api.tvmaze.com"

SCHEMA = """CREATE TABLE IF NOT EXISTS subscriptions (
    show_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    added TEXT NOT NULL
)"""

def get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "tv-show-tracker/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

def search_shows(name: str, base=API):
    results = get_json(f"{base}/search/shows?q={urllib.parse.quote(name)}")
    return [{"id": item["show"]["id"], "name": item["show"]["name"],
             "premiered": item["show"].get("premiered") or ""} for item in results]

def episodes(show_id: int, base=API):
    rows = get_json(f"{base}/shows/{show_id}/episodes")
    return [{"season": row.get("season"), "number": row.get("number"), "name": row.get("name"),
             "airdate": row.get("airdate") or ""} for row in rows]

def next_episode(episode_list, today: dt.date):
    upcoming = [episode for episode in episode_list
                if episode["airdate"] and dt.date.fromisoformat(episode["airdate"]) >= today]
    return min(upcoming, key=lambda e: e["airdate"]) if upcoming else None

def connect(path):
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA)
    connection.commit()
    return connection

def follow(connection, show_id, name):
    connection.execute("INSERT OR REPLACE INTO subscriptions (show_id,name,added) VALUES (?,?,?)",
                       (show_id, name, dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")))
    connection.commit()

def demo() -> None:
    search_payload = json.dumps([{"score": 1.0, "show": {"id": 82, "name": "Game of Thrones",
                                                          "premiered": "2011-04-17"}}]).encode()
    episodes_payload = json.dumps([
        {"season": 1, "number": 1, "name": "Winter Is Coming", "airdate": "2011-04-17"},
        {"season": 8, "number": 6, "name": "The Iron Throne", "airdate": "2019-05-19"},
        {"season": 9, "number": 1, "name": "A Dream of Spring", "airdate": "2027-04-01"},
    ]).encode()
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            payload = search_payload if self.path.startswith("/search/shows") else episodes_payload
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)
        def log_message(self, *args): pass
    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        shows = search_shows("Game of Thrones", base)
        print("search:", shows)
        with tempfile.TemporaryDirectory() as tmp:
            connection = connect(os.path.join(tmp, "tv.db"))
            follow(connection, shows[0]["id"], shows[0]["name"])
            shows_in_db = connection.execute("SELECT show_id,name FROM subscriptions").fetchall()
            print("following:", shows_in_db)
            upcoming = next_episode(episodes(82, base), dt.date(2026, 11, 2))
            print("next episode:", upcoming)
            connection.close()
    finally:
        server.shutdown(); server.server_close()

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="tvshows.db")
    parser.add_argument("--search")
    parser.add_argument("--follow", type=int, metavar="SHOW_ID")
    parser.add_argument("--name")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--next", action="store_true")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        demo(); return
    connection = connect(args.db)
    try:
        if args.search:
            for show in search_shows(args.search):
                print(f"{show['id']:>6}  {show['name']} ({show['premiered']})")
        if args.follow:
            name = args.name or f"show {args.follow}"
            follow(connection, args.follow, name)
            print("following", name)
        if args.list or args.next:
            today = dt.date.today()
            for show_id, name in connection.execute("SELECT show_id,name FROM subscriptions ORDER BY name").fetchall():
                if args.next:
                    upcoming = next_episode(episodes(show_id), today)
                    print(f"{name}: {upcoming}" if upcoming else f"{name}: no upcoming episodes")
                else:
                    print(f"{show_id:>6}  {name}")
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
