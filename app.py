import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory
from processor import process_voice_command
from language_module.pipeline import process_voice_command as process_v2
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder="static")

# ── Scheduler setup ──────────────────────────────────────────────────────────
_scheduler = BackgroundScheduler()
_scheduler.start()
_scheduled_orders = []  # in-memory store

def _execute_scheduled_order(order_id, text):
    """Called by APScheduler at the scheduled time to place the order."""
    result = process_v2(text)
    for o in _scheduled_orders:
        if o["id"] == order_id:
            o["status"] = "executed"
            o["result"] = result
            break

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# Original route — kept intact for backward compatibility
@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    result = process_voice_command(text)
    return jsonify(result)

# New enhanced route — uses language_module pipeline
@app.route("/process_v2", methods=["POST"])
def process_enhanced():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    result = process_v2(text)
    return jsonify(result)

# ── Translation helper endpoint ─────────────────────────────────────────────
@app.route("/translate", methods=["POST"])
def translate_text():
    data = request.get_json()
    text = data.get("text", "").strip()
    target_lang = data.get("target_lang", "en").strip()
    source_lang = data.get("source_lang", "auto").strip()
    if not text:
        return jsonify({"translated": text})
    # skip translation only if source and target are both English
    if target_lang == "en" and source_lang == "en":
        return jsonify({"translated": text})
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        return jsonify({"translated": translated})
    except Exception:
        return jsonify({"translated": text})


# ── Scheduling endpoints ─────────────────────────────────────────────────────
@app.route("/schedule", methods=["POST"])
def schedule_order():
    data = request.get_json()
    order_text = data.get("order_text", "").strip()
    scheduled_date = data.get("date", "").strip()   # YYYY-MM-DD
    scheduled_time = data.get("time", "").strip()   # HH:MM (24-h)
    if not order_text or not scheduled_date or not scheduled_time:
        return jsonify({"error": "order_text, date and time are required"}), 400
    try:
        run_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Invalid date/time format"}), 400
    if run_at <= datetime.now():
        return jsonify({"error": "Scheduled time must be in the future"}), 400
    order_id = f"sched_{int(datetime.now().timestamp()*1000)}"
    entry = {
        "id": order_id,
        "order_text": order_text,
        "scheduled_for": run_at.isoformat(),
        "status": "pending",
        "result": None
    }
    _scheduled_orders.append(entry)
    _scheduler.add_job(
        _execute_scheduled_order, "date",
        run_date=run_at, args=[order_id, order_text], id=order_id
    )
    return jsonify({"success": True, "order_id": order_id, "scheduled_for": run_at.isoformat()})


@app.route("/scheduled-orders", methods=["GET"])
def get_scheduled_orders():
    return jsonify(_scheduled_orders)


if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
