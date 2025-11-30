from flask import Flask, render_template, request, redirect, url_for, current_app
from werkzeug.exceptions import HTTPException
import sqlite3
import urllib.request
import urllib.parse
import urllib.error
import json
import hashlib

# ===============================
# Global Configuration
# ===============================

API_KEY = "YOUR_API_KEY"   # YouTube API key
DB = "youtube.db"        # SQLite database file name

app = Flask(__name__)


# ===============================
# Database Helper
# ===============================

def run_query(query, params=None, commit=False):
    """
    Execute SQL queries safely.
    - For SELECT queries → returns rows (list of sqlite3.Row)
    - For INSERT/UPDATE/DELETE → commit=True and returns True
    - On error → returns None
    """
    conn = sqlite3.connect(DB)  
    conn.row_factory = sqlite3.Row  
    
    # turn on foreign key to manage relations
    conn.execute("PRAGMA foreign_keys = ON;")
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


# ===============================
# Database Schema Initialization
# ===============================

def init_db():
    """
    Create database tables if they don't exist.
    Also sets up helpful indexes and foreign key cascade.
    """
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    # Create playlist table
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

    # Create video table (connected to playlist)
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

    # Indexes to improve performance
    c.execute("CREATE INDEX IF NOT EXISTS play_id_idx ON playlist(playlist_id, hash);")
    c.execute("CREATE INDEX IF NOT EXISTS vid_id_and_hash_idx ON video(vid_id, hash);")

    conn.commit()
    conn.close()


# Initialize database at startup
init_db()


# ===============================
# Hash Helpers (detect content changes)
# ===============================

def hash_playlist(playlist):
    """
    Generate an MD5 hash for a playlist based on its stable fields.
    Used to detect playlist updates.
    """
    text = (
        playlist.get("title", "") +
        playlist.get("thumbnail", "") +
        str(playlist.get("video_count", ""))
    )
    return hashlib.md5(text.encode()).hexdigest()


def hash_video(video):
    """
    Generate MD5 hash for a video to detect changes.
    """
    text = (
        video.get("title", "") +
        video.get("thumbnail", "") +
        str(video.get("idx_in_playlist", ""))
    )
    return hashlib.md5(text.encode()).hexdigest()


# ===============================
# URL & YouTube API Helpers
# ===============================

def extract_playlist_id(url_or_id):
    """
    Extract playlist ID from:
    - a full YouTube URL, or
    - a raw playlist ID
    Returns None if invalid.
    """
    if not url_or_id:
        return None

    # Raw ID case
    if "://" not in url_or_id and len(url_or_id) >= 8:
        return url_or_id.strip()

    # Parse from URL
    parsed = urllib.parse.urlparse(url_or_id)
    params = urllib.parse.parse_qs(parsed.query)
    return params.get("list", [None])[0]


def fetch_playlist_details(playlist_id):
    """
    Fetch playlist metadata (title, channel, thumbnail, video count).
    Returns a dictionary or None on failure.
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
    snippet = item["snippet"]
    content = item["contentDetails"]

    # Pick best quality thumbnail available
    thumbs = snippet.get("thumbnails", {})
    thumb_url = (thumbs.get("medium") or thumbs.get("high") or thumbs.get("default") or {"url": ""})["url"]

    playlist = {
        "playlist_id": playlist_id,
        "title": snippet.get("title", ""),
        "channel": snippet.get("channelTitle", "Unknown"),
        "thumbnail": thumb_url,
        "video_count": content.get("itemCount", 0),
    }

    playlist["hash"] = hash_playlist(playlist)
    return playlist


def fetch_playlist_items(playlist_id):
    """
    Fetch all videos inside a playlist (auto handles pagination).
    Returns list of video dictionaries.
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
            snippet = item["snippet"]
            content = item["contentDetails"]

            thumbs = snippet.get("thumbnails", {})
            thumb_url = (thumbs.get("medium") or thumbs.get("high") or thumbs.get("default") or {"url": ""})["url"]

            vid_id = content.get("videoId") or snippet.get("resourceId", {}).get("videoId")
            if not vid_id:
                continue

            video = {
                "vid_id": vid_id,
                "playlist_id": playlist_id,
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "thumbnail": thumb_url,
                "idx_in_playlist": snippet.get("position", 0)
            }

            video["hash"] = hash_video(video)
            videos.append(video)

        next_page = data.get("nextPageToken")
        if not next_page:
            break

    return videos


# ===============================
# Playlist & Video Database Management
# ===============================

def manage_playlist(playlist, videos, update=False):
    """
    Insert or update a playlist and its videos.
    - update=True → UPDATE existing playlist
    - update=False → INSERT new playlist
    """
    if not playlist:
        return False

    if update:
        # Update playlist details
        query = """
            UPDATE playlist SET
                title=?, thumbnail=?, video_count=?, hash=?
            WHERE playlist_id=?;
        """
        params = (
            playlist["title"], playlist["thumbnail"],
            playlist["video_count"], playlist["hash"],
            playlist["playlist_id"]
        )
        run_query(query, params, commit=True)

        # Handle video differences
        manage_videos(videos, playlist["playlist_id"])
        return True

    # Insert new playlist
    insert_query = """
        INSERT INTO playlist (playlist_id, title, channel, thumbnail, video_count, hash)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    params = (
        playlist["playlist_id"], playlist["title"], playlist["channel"],
        playlist["thumbnail"], playlist["video_count"], playlist["hash"]
    )
    run_query(insert_query, params, commit=True)

    # Insert all videos
    for v in videos:
        run_query("""
            INSERT INTO video (vid_id, playlist_id, title, channel, thumbnail, idx_in_playlist, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            v["vid_id"], v["playlist_id"], v["title"], v["channel"],
            v["thumbnail"], v["idx_in_playlist"], v["hash"]
        ), commit=True)

    return True


def manage_videos(videos, playlist_id):
    """
    Sync fetched videos with stored videos:
    - Insert missing videos
    - Update modified videos
    - Delete removed videos
    """
    fetched_data = {v["vid_id"]: v for v in videos}
    fetched_ids = set(fetched_data.keys())

    # Get stored videos
    rows = run_query("SELECT vid_id, hash FROM video WHERE playlist_id=?", (playlist_id,))
    if rows is None:
        return

    stored_ids = {r["vid_id"] for r in rows}
    stored_hash = {r["vid_id"]: r["hash"] for r in rows}

    # 1. Insert new videos
    for vid in fetched_ids - stored_ids:
        v = fetched_data[vid]
        run_query("""
            INSERT INTO video (vid_id, playlist_id, title, channel, thumbnail, idx_in_playlist, hash)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            v["vid_id"], v["playlist_id"], v["title"], v["channel"],
            v["thumbnail"], v["idx_in_playlist"], v["hash"]
        ), commit=True)

    # 2. Update changed videos
    for vid in fetched_ids & stored_ids:
        v = fetched_data[vid]
        if stored_hash.get(vid) != v["hash"]:
            run_query("""
                UPDATE video SET
                    title=?, thumbnail=?, idx_in_playlist=?, hash=?
                WHERE vid_id=?;
            """, (
                v["title"], v["thumbnail"], v["idx_in_playlist"], v["hash"], vid
            ), commit=True)

    # 3. Delete removed videos
    for vid in stored_ids - fetched_ids:
        run_query("DELETE FROM video WHERE vid_id=?", (vid,), commit=True)


# ===============================
# Flask Routes
# ===============================

@app.route("/")
def index():
    """Show all saved playlists."""
    rows = run_query("SELECT * FROM playlist;")
    return render_template("index.html", playlists=rows or [])


@app.route("/add_playlist", methods=["POST"])
def add_playlist():
    """
    Add a new playlist or refresh an existing one.
    Automatically extracts ID from URL.
    """
    URL = request.form.get("url")
    playlist_id = extract_playlist_id(URL)

    playlist_data = fetch_playlist_details(playlist_id)
    videos_data = fetch_playlist_items(playlist_id)

    existing = run_query("SELECT playlist_id FROM playlist WHERE playlist_id=?", (playlist_id,))
    manage_playlist(playlist_data, videos_data, update=bool(existing))

    return redirect("/")


@app.route("/playlist/<playlist_id>")
def show_playlist(playlist_id):
    """Show playlist contents (videos list)."""
    rows = run_query(
        "SELECT * FROM video WHERE playlist_id=? ORDER BY idx_in_playlist ASC;",
        (playlist_id,)
    )
    return render_template("playlist.html", videos=rows or [], playlist_id=playlist_id)


@app.route("/playlist/<playlist_id>/refresh")
def refresh_playlist(playlist_id):
    """
    Refresh playlist: re-fetch metadata + items, apply update logic.
    """
    playlist_data = fetch_playlist_details(playlist_id)
    videos_data = fetch_playlist_items(playlist_id)

    manage_playlist(playlist_data, videos_data, update=True)
    return redirect(url_for("show_playlist", playlist_id=playlist_id))


@app.route("/delete/<playlist_id>")
def delete_playlist(playlist_id):
    """Delete playlist + its videos (cascade)."""
    run_query("DELETE FROM playlist WHERE playlist_id=?", (playlist_id,), commit=True)
    return redirect("/")


@app.route("/video/<video_id>")
def show_video(video_id):
    """Show a single video page."""
    playlist_id = request.args.get("playlist_id")
    return render_template("video.html", vid_id=video_id, playlist_id=playlist_id)


@app.route("/back")
def go_back():
    """
    Universal back button logic:
    - ?home=true → go to homepage
    - ?playlist=x → go back to playlist x
    """
    if request.args.get("home", "false").lower() == "true":
        return redirect("/")
    playlist_id = request.args.get("playlist")
    return redirect(f"/playlist/{playlist_id}" if playlist_id else "/")


# ===============================
# Error Handlers
# ===============================

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle 404, 403, etc."""
    return render_template("error.html", data={
        "error": e.name,
        "code": e.code,
        "description": e.description
    }), e.code


@app.errorhandler(Exception)
def handle_generic_exception(e):
    """Handle unexpected errors."""
    return render_template("error.html", data={
        "error": "Internal Server Error",
        "code": 500,
        "description": str(e) if current_app.debug else "Something went wrong."
    }), 500


# ===============================
# Run Server
# ===============================

if __name__ == "__main__":
    app.run(debug=True)
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
