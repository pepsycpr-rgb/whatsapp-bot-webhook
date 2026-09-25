"""WhatsApp Cloud API webhook receiver (production-ready).

GET  /webhook  -> Meta verification (hub.verify_token vs VERIFY_TOKEN)
POST /webhook  -> receives incoming messages, saves each text message as a JSON
                  file in inbox/ for the reply loop to pick up.
GET  /pending  -> returns unacknowledged inbox messages (X-Brain-Key required).
                  Polled by the assistant's reply loop (outbound-friendly).
POST /ack      -> marks message ids as handled: {"ids": ["file.json", ...]}
GET  /health   -> liveness check.

Config: environment variables take precedence over config.json:
  VERIFY_TOKEN  (Meta webhook verification)
  BRAIN_KEY     (shared secret protecting /pending and /ack)
  APP_SECRET    (optional: validates X-Hub-Signature-256 on POST /webhook)
  PORT          (Render sets this automatically)

Run locally:  ./start.sh
Deploy:       gunicorn webhook:app  (see render.yaml)
"""

import hashlib
import hmac
import json
import os
import time

from flask import Flask, request, abort, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INBOX_DIR = os.path.join(BASE_DIR, "inbox")
ACKED_FILE = os.path.join(BASE_DIR, "acked.json")

try:
    with open(os.path.join(BASE_DIR, "config.json")) as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    CONFIG = {}

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN") or CONFIG.get("verify_token", "")
BRAIN_KEY = os.environ.get("BRAIN_KEY") or CONFIG.get("brain_key", "")
APP_SECRET = os.environ.get("APP_SECRET") or CONFIG.get("app_secret", "")

app = Flask(__name__)


def _load_acked():
    try:
        with open(ACKED_FILE) as f:
            data = json.load(f)
            return set(data) if isinstance(data, list) else set()
    except (FileNotFoundError, ValueError):
        return set()


def _save_acked(acked):
    with open(ACKED_FILE, "w") as f:
        json.dump(sorted(acked), f)


def _brain_auth_ok():
    if not BRAIN_KEY:
        return False  # fail closed: no key configured -> deny
    return request.headers.get("X-Brain-Key", "") == BRAIN_KEY


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token and token == VERIFY_TOKEN:
        return challenge, 200
    return "verification failed", 403


def _signature_ok(raw_body: bytes) -> bool:
    """Validate X-Hub-Signature-256 when APP_SECRET is configured."""
    if not APP_SECRET:
        return True  # not configured yet -> skip validation
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature.split("=", 1)[1])


@app.route("/webhook", methods=["POST"])
def receive():
    raw_body = request.get_data()
    if not _signature_ok(raw_body):
        abort(403)

    try:
        payload = request.get_json(force=True, silent=True) or {}
    except Exception:
        return "ok", 200

    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                contacts = {c.get("wa_id"): c.get("profile", {}).get("name", "")
                            for c in value.get("contacts", [])}
                for msg in value.get("messages", []):
                    if msg.get("type") != "text":
                        continue
                    sender = msg.get("from", "unknown")
                    record = {
                        "sender": sender,
                        "name": contacts.get(sender, ""),
                        "text": (msg.get("text") or {}).get("body", ""),
                        "timestamp": msg.get("timestamp", str(int(time.time()))),
                        "received_at": int(time.time()),
                    }
                    fname = "%d_%s.json" % (record["received_at"], sender)
                    with open(os.path.join(INBOX_DIR, fname), "w") as f:
                        json.dump(record, f, ensure_ascii=False, indent=2)
    except Exception:
        # Never let a malformed payload break the webhook; Meta retries anyway.
        pass

    return "ok", 200


@app.route("/pending", methods=["GET"])
def pending():
    """List inbox messages not yet acknowledged by the reply loop."""
    if not _brain_auth_ok():
        abort(403)
    acked = _load_acked()
    messages = []
    try:
        files = sorted(os.listdir(INBOX_DIR))
    except FileNotFoundError:
        files = []
    for fname in files:
        if not fname.endswith(".json") or fname in acked:
            continue
        try:
            with open(os.path.join(INBOX_DIR, fname)) as f:
                record = json.load(f)
        except (ValueError, OSError):
            continue
        record["id"] = fname
        messages.append(record)
    return jsonify({"messages": messages}), 200


@app.route("/ack", methods=["POST"])
def ack():
    """Mark message ids as handled: {"ids": ["<file>.json", ...]}."""
    if not _brain_auth_ok():
        abort(403)
    body = request.get_json(force=True, silent=True) or {}
    ids = body.get("ids", [])
    if not isinstance(ids, list):
        abort(400)
    acked = _load_acked()
    for i in ids:
        if isinstance(i, str) and i.endswith(".json") and "/" not in i:
            acked.add(i)
    _save_acked(acked)
    return jsonify({"acked": len(ids)}), 200


@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


if __name__ == "__main__":
    os.makedirs(INBOX_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", CONFIG.get("port", 5000)))
    app.run(host="0.0.0.0", port=port)
