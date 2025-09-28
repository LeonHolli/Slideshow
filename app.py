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
import tempfile

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

CONFIG_DIR = "config"
os.makedirs(CONFIG_DIR, exist_ok=True)
SCHEDULE_FILE = os.path.join(CONFIG_DIR, "schedules.json")

# ==============================
# LOGGING
# ==============================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==============================
# KONFIGURATION LADEN / SPEICHERN
# ==============================
def default_config():
    return {
        "schedules": [],
        "plug_ip": "192.168.2.193",
        "autoplay_show": ""
    }

def load_config():
    if os.path.exists(SCHEDULE_FILE) and os.path.isfile(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Fehler beim Laden der Konfig ({SCHEDULE_FILE}): {e}")
            return default_config()
    else:
        return default_config()

def save_config(config):
    # atomar schreiben: in temp schreiben und mv
    try:
        fd, tmp = tempfile.mkstemp(dir=CONFIG_DIR, text=True)
        with os.fdopen(fd, "w") as f:
            json.dump(config, f, indent=2)
        os.replace(tmp, SCHEDULE_FILE)
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der Konfig ({SCHEDULE_FILE}): {e}")

CONFIG = load_config()
logging.info(f"CONFIG geladen: {CONFIG}")

# ==============================
# SMART PLUG
# ==============================
async def set_plug_state(state: bool):
    plug_ip = CONFIG.get("plug_ip")
    if not plug_ip:
        logging.error("Keine Plug-IP konfiguriert.")
        return
    plug = SmartPlug(plug_ip)
    try:
        logging.info(f"🔌 Versuche Plug {plug_ip} {'EIN' if state else 'AUS'} zu schalten ...")
        await plug.update()  # aktualisieren
        if state:
            await plug.turn_on()
            logging.info("✅ Plug wurde eingeschaltet.")
        else:
            await plug.turn_off()
            logging.info("⛔ Plug wurde ausgeschaltet.")
    except Exception as e:
        logging.error(f"⚠️ Fehler beim Steuern des Plugs ({plug_ip}): {e}")

def turn_pi_on():
    try:
        asyncio.run(set_plug_state(True))
    except Exception as e:
        logging.error(f"Fehler beim turn_pi_on: {e}")

def turn_pi_off():
    try:
        asyncio.run(set_plug_state(False))
    except Exception as e:
        logging.error(f"Fehler beim turn_pi_off: {e}")

@app.route("/pi/on")
def pi_on():
    turn_pi_on()
    return "✅ Raspberry Pi eingeschaltet (KP105 an)"

@app.route("/pi/off")
def pi_off():
    turn_pi_off()
    return "⛔ Raspberry Pi ausgeschaltet (KP105 aus)"

# ==============================
# OFFLINE-ZEITEN (Scheduler)
# ==============================
def scheduler_loop():
    is_on = None  # None = unbekannt, True = an, False = aus
    while True:
        try:
            schedules = CONFIG.get("schedules", [])
            now = datetime.now().strftime("%H:%M")
            in_offline = any(s["start"] <= now <= s["end"] for s in schedules)

            if in_offline:
                if is_on is not False:
                    logging.info("⏰ Offline-Zeit erreicht – schalte Pi aus")
                    turn_pi_off()
                    is_on = False
            else:
                if is_on is not True:
                    logging.info("✅ Offline-Zeit vorbei – schalte Pi ein")
                    turn_pi_on()
                    is_on = True
        except Exception as e:
            logging.error(f"Fehler im Scheduler: {e}")
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
# AUTOPLAY
# ==============================
@app.route("/set_autoplay", methods=["POST"])
def set_autoplay():
    global CONFIG
    autoplay = request.form.get("autoplay", "").strip()
    CONFIG["autoplay_show"] = autoplay
    save_config(CONFIG)
    logging.info(f"🎬 Autoplay-Show gesetzt: {autoplay}")
    # Nach Änderung zurück ins Menü mit autoplay=1 → nur einmal Autostart
    return redirect(url_for("index") + "?autoplay=1")

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

        # 📂 Namen aus ZIP-Datei ableiten
        base_name = os.path.splitext(file.filename)[0]
        folder_name = base_name
        counter = 1
        while os.path.exists(os.path.join(UPLOAD_DIR, folder_name)):
            folder_name = f"{base_name}_{counter}"
            counter += 1

        folder_path = os.path.join(UPLOAD_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        zip_path = os.path.join(folder_path, "upload.zip")
        file.save(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(folder_path)

        return redirect(url_for("slideshow", folder=folder_name))

    shows = [f for f in os.listdir(UPLOAD_DIR) if os.path.isdir(os.path.join(UPLOAD_DIR, f))]
    return render_template(
        "menu.html",
        shows=shows,
        interval=SLIDESHOW_INTERVAL,
        schedules=CONFIG.get("schedules", []),
        plug_ip=CONFIG.get("plug_ip", ""),
        autoplay_show=CONFIG.get("autoplay_show", "")
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
