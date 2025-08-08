import logging
import sys
from pathlib import Path
from threading import Thread

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from TikTokLive import TikTokLiveClient

app = Flask(__name__)

# Avoid eventlet on Python versions where it is incompatible
async_mode = "threading"
if sys.version_info < (3, 12):
    try:
        import eventlet  # noqa: F401
        async_mode = "eventlet"
    except Exception:
        pass

socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)

# Logging
logs_path = Path("logs")
logs_path.mkdir(exist_ok=True)

event_logger = logging.getLogger("events")
event_logger.setLevel(logging.INFO)
event_logger.addHandler(logging.FileHandler(logs_path / "events.log"))

error_logger = logging.getLogger("errors")
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(logging.FileHandler(logs_path / "errors.log"))

client = None
client_thread = None
leaderboard = {}

def safe_get(obj, *attrs):
    for attr in attrs:
        obj = getattr(obj, attr, None)
        if obj is None:
            return None
    return obj

def start_client(username: str):
    global client, client_thread, leaderboard

    if client:
        try:
            client.close()
        except Exception:
            pass
    leaderboard = {}
    client = TikTokLiveClient(unique_id=username)

    @client.on("comment")
    async def on_comment(event):
        try:
            avatar = safe_get(event, "user", "profile_picture_url")
            nickname = safe_get(event, "user", "nickname")
            text = getattr(event, "comment", "")
            event_logger.info(f"comment: {nickname}: {text}")
            socketio.emit("comment", {"avatar": avatar, "nickname": nickname, "comment": text})
        except Exception:
            error_logger.exception("comment event")

    @client.on("like")
    async def on_like(event):
        try:
            total = getattr(event, "total_likes", getattr(event, "like_count", 0))
            event_logger.info(f"like: {total}")
            socketio.emit("like", {"total": total})
        except Exception:
            error_logger.exception("like event")

    @client.on("viewer_update")
    async def on_viewer(event):
        try:
            count = getattr(event, "viewer_count", getattr(event, "viewerCount", 0))
            event_logger.info(f"viewer: {count}")
            socketio.emit("viewer", {"count": count})
        except Exception:
            error_logger.exception("viewer event")

    @client.on("share")
    async def on_share(event):
        try:
            count = getattr(event, "share_count", 1)
            event_logger.info("share event")
            socketio.emit("share", {"count": count})
        except Exception:
            error_logger.exception("share event")

    @client.on("gift")
    async def on_gift(event):
        try:
            user = getattr(event, "user", None)
            gift = getattr(event, "gift", None)
            nickname = getattr(user, "nickname", "")
            gift_name = getattr(gift, "name", "")
            count = getattr(event, "repeat_count", getattr(event, "count", 1))
            diamonds = getattr(gift, "diamond_count", 0) * count
            if nickname:
                leaderboard[nickname] = leaderboard.get(nickname, 0) + diamonds
            event_logger.info(f"gift: {nickname} sent {count} x {gift_name}")
            socketio.emit("gift", {"nickname": nickname, "gift": gift_name, "count": count})
            socketio.emit("leaderboard", leaderboard)
        except Exception:
            error_logger.exception("gift event")

    @client.on("link_mic_armies")
    async def on_battle(event):
        try:
            data = event.to_dict() if hasattr(event, "to_dict") else {}
            event_logger.info("battle event")
            socketio.emit("battle", data)
        except Exception:
            error_logger.exception("battle event")

    @client.on("live_end")
    async def on_live_end(event):
        try:
            event_logger.info("live end")
            socketio.emit("end")
        except Exception:
            error_logger.exception("live end event")

    def run_client():
        try:
            client.run()
        except Exception:
            error_logger.exception("client run error")

    client_thread = Thread(target=run_client, daemon=True)
    client_thread.start()

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect_stream")
def handle_connect_stream(data):
    username = data.get("username")
    if username:
        start_client(username)
        emit("connected")

@socketio.on("disconnect_stream")
def handle_disconnect_stream():
    global client
    if client:
        try:
            client.close()
        except Exception:
            pass
    client = None
    emit("disconnected")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
