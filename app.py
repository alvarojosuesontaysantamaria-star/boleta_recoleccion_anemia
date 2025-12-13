from flask import Flask, render_template, request, redirect, url_for
import os
import csv
from datetime import datetime
import pandas as pd
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# ================== CLOUDINARY ==================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
# ===============================================

CSV_FILE = "registros_anemia.csv"
EXCEL_FILE = "registros_anemia.xlsx"

# Crear Excel si no existe
if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(columns=[
        "ID", "Edad", "Lugar", "Trimestre",
        "Hemoglobina", "Semanas", "Resultado",
        "Foto_URL", "Fecha"
    ])
    df_init.to_excel(EXCEL_FILE, index=False)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generar", methods=["POST"])
def generar():
    edad = request.form["edad"]
    lugar = request.form["lugar"]
    trimestre = request.form["trimestre"]
    hemoglobina = request.form["hemoglobina"]
    semanas = request.form["semanas"]
    resultado = request.form["resultado"]
    foto = request.files["photo"]

    # Calcular ID
    registros_previos = 0
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            registros_previos = sum(1 for _ in f) - 1
    numero_paciente = registros_previos + 1

    # Subir imagen a Cloudinary
    upload_result = cloudinary.uploader.upload(
        foto,
        folder="anemia_conjuntiva",
        public_id=f"paciente_{numero_paciente}"
    )
    foto_url = upload_result["secure_url"]

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Guardar CSV
    archivo_nuevo = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if archivo_nuevo:
            writer.writerow([
                "ID", "Edad", "Lugar", "Trimestre",
                "Hemoglobina", "Semanas", "Resultado",
                "Foto_URL", "Fecha"
            ])
        writer.writerow([
            numero_paciente, edad, lugar, trimestre,
            hemoglobina, semanas, resultado,
            foto_url, fecha
        ])

    # Guardar Excel
    df = pd.read_excel(EXCEL_FILE)
    df.loc[len(df)] = [
        numero_paciente, edad, lugar, trimestre,
        hemoglobina, semanas, resultado,
        foto_url, fecha
    ]
    df.to_excel(EXCEL_FILE, index=False)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
