import os
import zipfile
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Startseite → Upload + Übersicht vorhandener Shows
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

    # Liste der vorhandenen Shows
    shows = [f for f in os.listdir(UPLOAD_DIR) if os.path.isdir(os.path.join(UPLOAD_DIR, f))]
    return render_template("menu.html", shows=shows)

# Slideshow-Seite
@app.route("/show/<folder>")
def slideshow(folder):
    return render_template("slideshow.html", folder=folder)

# JSON-Liste mit Bildern
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

# Bilder ausliefern
@app.route("/images/<folder>/<filename>")
def serve_image(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_DIR, folder), filename)

# Show umbenennen
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

if __name__ == "__main__":
    print("🚀 Starte Flask-Server auf Port 5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)
