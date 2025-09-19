import os
import zipfile
import uuid
import json
import asyncio
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from kasa import SmartPlug
import logging

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SCHEDULE_FILE = "schedules.json"

# ==============================
# LOGGING
# ==============================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==============================
# KONFIGURATION LADEN / SPEICHERN
# ==============================
def load_config():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {"schedules": [], "plug_ip": "192.168.2.193"}

def save_config(config):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(config, f)

CONFIG = load_config()

# ==============================
# SMART PLUG
# ==============================
async def set_plug_state(state: bool):
    plug_ip = CONFIG.get("plug_ip")
    plug = SmartPlug(plug_ip)
    try:
        logging.info(f"🔌 Versuche Plug {plug_ip} {'EIN' if state else 'AUS'} zu schalten ...")
        await plug.update()
        if state:
            await plug.turn_on()
            logging.info("✅ Plug wurde eingeschaltet.")
        else:
            await plug.turn_off()
            logging.info("⛔ Plug wurde ausgeschaltet.")
    except Exception as e:
        logging.error(f"⚠️ Fehler beim Steuern des Plugs ({plug_ip}): {e}")

def turn_pi_on():
    asyncio.run(set_plug_state(True))

def turn_pi_off():
    asyncio.run(set_plug_state(False))

@app.route("/pi/on")
def pi_on():
    turn_pi_on()
    return "✅ Raspberry Pi eingeschaltet (KP105 an)"

@app.route("/pi/off")
def pi_off():
    turn_pi_off()
    return "⛔ Raspberry Pi ausgeschaltet (KP105 aus)"

# ==============================
# OFFLINE-ZEITEN
# ==============================
def scheduler_loop():
    is_on = None  # None = unbekannt, True = an, False = aus

    while True:
        schedules = CONFIG.get("schedules", [])
        now = datetime.now().strftime("%H:%M")
        in_offline = any(s["start"] <= now <= s["end"] for s in schedules)

        if in_offline:
            # Wenn Pi noch an ist, ausschalten
            if is_on is not False:
                logging.info("⏰ Offline-Zeit erreicht – schalte Pi aus")
                turn_pi_off()
                is_on = False
        else:
            # Außerhalb der Offline-Zeit nur einschalten, wenn noch aus
            if is_on is not True:
                logging.info("✅ Offline-Zeit vorbei – schalte Pi ein")
                turn_pi_on()
                is_on = True

        time.sleep(60)

threading.Thread(target=scheduler_loop, daemon=True).start()

@app.route("/schedules", methods=["POST"])
def schedules():
    global CONFIG
    schedules = []
    starts = request.form.getlist("start")
    ends = request.form.getlist("end")
    for s, e in zip(starts, ends):
        if s and e:
            schedules.append({"start": s, "end": e})

    plug_ip = request.form.get("plug_ip", "").strip()
    if plug_ip:
        CONFIG["plug_ip"] = plug_ip

    CONFIG["schedules"] = schedules
    save_config(CONFIG)

    logging.info(f"💾 Neue Konfiguration gespeichert: {CONFIG}")
    return redirect(url_for("index"))

# ==============================
# SLIDESHOW & UPLOAD
# ==============================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "zipfile" not in request.files:
            return "Keine Datei hochgeladen", 400
        file = request.files["zipfile"]
        if file.filename == "":
            return "Leere Datei", 400

        folder_id = str(uuid.uuid4())
        folder_path = os.path.join(UPLOAD_DIR, folder_id)
        os.makedirs(folder_path, exist_ok=True)

        zip_path = os.path.join(folder_path, "upload.zip")
        file.save(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(folder_path)

        return redirect(url_for("slideshow", folder=folder_id))

    shows = [f for f in os.listdir(UPLOAD_DIR) if os.path.isdir(os.path.join(UPLOAD_DIR, f))]
    return render_template(
        "menu.html",
        shows=shows,
        interval=SLIDESHOW_INTERVAL,
        schedules=CONFIG.get("schedules", []),
        plug_ip=CONFIG.get("plug_ip", "")
    )

@app.route("/show/<folder>")
def slideshow(folder):
    return render_template("slideshow.html", folder=folder, interval=SLIDESHOW_INTERVAL)

@app.route("/list/<folder>")
def list_images(folder):
    folder_path = os.path.join(UPLOAD_DIR, folder)
    if not os.path.exists(folder_path):
        return jsonify([])
    files = []
    for f in os.listdir(folder_path):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            files.append(f"/images/{folder}/{f}")
    return jsonify(sorted(files))

@app.route("/images/<folder>/<filename>")
def serve_image(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_DIR, folder), filename)

@app.route("/rename", methods=["POST"])
def rename_show():
    old_name = request.form.get("old")
    new_name = request.form.get("new")

    old_path = os.path.join(UPLOAD_DIR, old_name)
    new_path = os.path.join(UPLOAD_DIR, new_name)

    if not os.path.exists(old_path):
        return "Ordner nicht gefunden", 404
    if os.path.exists(new_path):
        return "Neuer Name existiert bereits", 400

    os.rename(old_path, new_path)
    return redirect(url_for("index"))

# Slideshow-Intervall
SLIDESHOW_INTERVAL = 5

@app.route("/set_interval", methods=["POST"])
def set_interval():
    global SLIDESHOW_INTERVAL
    try:
        SLIDESHOW_INTERVAL = int(request.form.get("interval", 5))
    except ValueError:
        SLIDESHOW_INTERVAL = 5
    return redirect(url_for("index"))

if __name__ == "__main__":
    print("🚀 Starte Flask-Server auf Port 5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)
