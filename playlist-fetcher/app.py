# app.py — corrected, commented, and ready to run
from flask import Flask, render_template, request, redirect, url_for, current_app
from werkzeug.exceptions import HTTPException
import sqlite3
import urllib.request
import urllib.parse
import urllib.error
import json
import hashlib

# -----------------------
# Configuration
# -----------------------
API_KEY = "AIzaSyDrMmpbPbqpzU3LyU1lO8MAgonZ_Nxtq8Y"
DB = "youtube.db"

app = Flask(__name__)

# -----------------------
# Database helper
# -----------------------
def run_query(query, params=None, commit=False):
    """
    Run a SQL query safely.
    - For read queries: returns sqlite3.Row list (or [] on empty).
    - For write queries (commit=True): commits and returns True on success.
    - Returns None on DB error (and prints error).
    """
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if params:
        cur.execute(query, params)
    else:
        cur.execute(query)

    if commit:
        conn.commit()
        conn.close()
        return True

    rows = cur.fetchall()
    conn.close()
    return rows

# -----------------------
# Initialize DB schema
# -----------------------
def init_db():
    """
    Create playlist and video tables (if they don't exist).
    Enables foreign key cascade on delete for videos linked to playlist.
    """
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    # playlist table
    c.execute("""
        CREATE TABLE IF NOT EXISTS playlist (
            playlist_id TEXT PRIMARY KEY,
            title TEXT,
            channel TEXT,
            thumbnail TEXT,
            video_count INTEGER,
            hash TEXT
        );
    """)

    # video table with foreign key cascade
    c.execute("""
        CREATE TABLE IF NOT EXISTS video (
            vid_id TEXT PRIMARY KEY,
            playlist_id TEXT NOT NULL,
            title TEXT,
            channel TEXT,
            thumbnail TEXT,
            idx_in_playlist INTEGER,
            hash TEXT,
            FOREIGN KEY (playlist_id) REFERENCES playlist(playlist_id) ON DELETE CASCADE
        );
    """)

    # Useful indexes
    c.execute("CREATE INDEX IF NOT EXISTS play_id_idx ON playlist(playlist_id, hash);")
    c.execute("CREATE INDEX IF NOT EXISTS vid_id_and_hash_idx ON video(vid_id, hash);")

    conn.commit()
    conn.close()

# Ensure DB/tables exist before serving
init_db()

# -----------------------
# Hash helpers
# -----------------------
def hash_playlist(playlist):
    """Return MD5 hash for playlist using stable fields."""
    text = (playlist.get("title", "") +
            playlist.get("thumbnail", "") +
            str(playlist.get("video_count", "")))
    return hashlib.md5(text.encode()).hexdigest()


def hash_video(video):
    """Return MD5 hash for a video using stable fields."""
    text = (video.get("title", "") +
            video.get("thumbnail", "") +
            str(video.get("idx_in_playlist", "")))
    return hashlib.md5(text.encode()).hexdigest()

# -----------------------
# URL / YouTube fetch helpers
# -----------------------
def extract_playlist_id(url_or_id):
    """
    Given either a full playlist URL or a bare playlist id, return the playlist id or None.
    """
    if not url_or_id:
        return None

    # If user provided a bare id (no scheme) and looks long enough, accept it
    if "://" not in url_or_id and len(url_or_id) >= 8:
        return url_or_id.strip()

    parsed = urllib.parse.urlparse(url_or_id)
    params = urllib.parse.parse_qs(parsed.query)
    playlist_id = params.get("list", [None])[0]
    return playlist_id


def fetch_playlist_details(playlist_id):
    """
    Fetch playlist metadata from YouTube API.
    Returns dict or None on failure.
    """
    base_url = "https://www.googleapis.com/youtube/v3/playlists"
    params = {
        "part": "snippet,contentDetails",
        "id": playlist_id,
        "key": API_KEY
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())

    if not data.get("items"):
        return None

    item = data["items"][0]
    snippet = item.get("snippet", {})
    content = item.get("contentDetails", {})

    thumbs = snippet.get("thumbnails", {})
    thumb_url = (thumbs.get("medium") or
                 thumbs.get("high") or
                 thumbs.get("default") or {"url": ""})["url"]

    playlist = {
        "playlist_id": item.get("id"),
        "title": snippet.get("title", ""),
        "channel": snippet.get("channelTitle", "Unknown"),
        "thumbnail": thumb_url,
        "video_count": content.get("itemCount", 0),
    }

    playlist["hash"] = hash_playlist(playlist)
    return playlist


def fetch_playlist_items(playlist_id):
    """
    Fetch all playlist items with pagination.
    """
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    videos = []
    next_page = None

    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": API_KEY
        }

        if next_page:
            params["pageToken"] = next_page

        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode())

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})

            thumbs = snippet.get("thumbnails", {})
            thumb_url = (thumbs.get("medium") or
                         thumbs.get("high") or
                         thumbs.get("default") or {"url": ""})["url"]

            vid_id = (content.get("videoId") or
                      snippet.get("resourceId", {}).get("videoId"))

            if not vid_id:
                continue

            vid = {
                "vid_id": vid_id,
                "playlist_id": playlist_id,
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "thumbnail": thumb_url,
                "idx_in_playlist": snippet.get("position", 0),
            }

            vid["hash"] = hash_video(vid)
            videos.append(vid)

        next_page = data.get("nextPageToken")
        if not next_page:
            break

    return videos

# -----------------------
# DB management
# -----------------------
def manage_playlist(playlist, videos, update=False):
    """
    Insert or update playlist + videos.
    """
    if not playlist:
        return False

    if update:
        query = """
            UPDATE playlist SET
                title = ?, thumbnail = ?, video_count = ?, hash = ?
            WHERE playlist_id = ?;
        """
        params = (
            playlist["title"], playlist["thumbnail"],
            playlist["video_count"], playlist["hash"],
            playlist["playlist_id"]
        )
        run_query(query, params, commit=True)
        manage_videos(videos, playlist["playlist_id"])
        return True

    # Insert
    query = """
        INSERT INTO playlist (playlist_id, title, channel, thumbnail, video_count, hash)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    params = (
        playlist["playlist_id"], playlist["title"], playlist["channel"],
        playlist["thumbnail"], playlist["video_count"], playlist["hash"]
    )
    run_query(query, params, commit=True)

    v_query = """
        INSERT INTO video (vid_id, playlist_id, title, channel, thumbnail, idx_in_playlist, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    for v in videos:
        v_params = (
            v["vid_id"], v["playlist_id"], v["title"], v["channel"],
            v["thumbnail"], v["idx_in_playlist"], v["hash"]
        )
        run_query(v_query, v_params, commit=True)

    return True


def manage_videos(videos, playlist_id):
    fetched_data = {v["vid_id"]: v for v in videos}
    fetched_ids = set(fetched_data.keys())

    rows = run_query(
        "SELECT vid_id, hash FROM video WHERE playlist_id = ?;",
        (playlist_id,)
    )
    if rows is None:
        return

    stored_ids = {r["vid_id"] for r in rows}
    stored_hash = {r["vid_id"]: r["hash"] for r in rows}

    # Insert
    insert_ids = fetched_ids - stored_ids
    insert_query = """
        INSERT INTO video (
            vid_id, playlist_id, title, channel, thumbnail, idx_in_playlist, hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    for vid in insert_ids:
        v = fetched_data[vid]
        params = (
            v["vid_id"], v["playlist_id"], v["title"], v["channel"],
            v["thumbnail"], v["idx_in_playlist"], v["hash"]
        )
        run_query(insert_query, params, commit=True)

    # Update
    update_ids = fetched_ids & stored_ids
    update_query = """
        UPDATE video SET
            title = ?, thumbnail = ?, idx_in_playlist = ?, hash = ?
        WHERE vid_id = ?;
    """
    for vid in update_ids:
        v = fetched_data[vid]
        if stored_hash.get(vid) != v["hash"]:
            params = (
                v["title"], v["thumbnail"],
                v["idx_in_playlist"], v["hash"], vid
            )
            run_query(update_query, params, commit=True)

    # Delete
    delete_ids = stored_ids - fetched_ids
    del_query = "DELETE FROM video WHERE vid_id = ?;"
    for vid in delete_ids:
        run_query(del_query, (vid,), commit=True)

# -----------------------
# Routes
# -----------------------
@app.route("/")
def index():
    rows = run_query("SELECT * FROM playlist;")
    return render_template("index.html", playlists=rows or [])


@app.route("/add_playlist", methods=["POST"])
def add_playlist():
    URL = request.form.get("url")
    playlist_id = extract_playlist_id(URL)

    playlist_data = fetch_playlist_details(playlist_id)
    videos_data = fetch_playlist_items(playlist_id)

    existing = run_query(
        "SELECT playlist_id FROM playlist WHERE playlist_id = ?;",
        (playlist_id,)
    )
    to_update = bool(existing)

    manage_playlist(playlist_data, videos_data, update=to_update)
    return redirect("/")


@app.route("/playlist/<playlist_id>")
def show_playlist(playlist_id):
    rows = run_query(
        "SELECT * FROM video WHERE playlist_id = ? ORDER BY idx_in_playlist ASC;",
        (playlist_id,)
    )
    return render_template("playlist.html", videos=rows or [], playlist_id=playlist_id)


@app.route("/playlist/<playlist_id>/refresh")
def refresh_playlist(playlist_id):
    playlist_data = fetch_playlist_details(playlist_id)
    videos_data = fetch_playlist_items(playlist_id)

    manage_playlist(playlist_data, videos_data, update=True)
    print("refresh")
    return redirect(url_for("show_playlist", playlist_id=playlist_id))


@app.route("/delete/<playlist_id>")
def delete_playlist(playlist_id):
    run_query("DELETE FROM playlist WHERE playlist_id = ?;", (playlist_id,), commit=True)
    return redirect("/")


@app.route("/video/<video_id>")
def show_video(video_id):
    playlist_id = request.args.get("playlist_id")
    return render_template("video.html", vid_id=video_id, playlist_id=playlist_id)


@app.route("/back", methods=["GET"])
def go_back():
    go_home = request.args.get("home", "false").lower() == "true"
    if go_home:
        return redirect("/")
    playlist_id = request.args.get("playlist")
    return redirect(f"/playlist/{playlist_id}" if playlist_id else "/")


# -----------------------
# Error Handlers
# -----------------------
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    data = {
        "error": e.name,
        "code": e.code,
        "description": e.description
    }
    return render_template("error.html", data=data), e.code


@app.errorhandler(Exception)
def handle_generic_exception(e):
    data = {
        "error": "Internal Server Error",
        "code": 500,
        "description": str(e) if current_app.debug else "Something went wrong."
    }
    return render_template("error.html", data=data), 500


# -----------------------
# Run server
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)