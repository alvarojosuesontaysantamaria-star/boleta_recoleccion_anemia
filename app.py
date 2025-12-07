import os
from flask import Flask, render_template, request, redirect, url_for
import csv
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# CONFIG
# -----------------------------
UPLOAD_FOLDER = "uploads"
EXCEL_FILE = "registros_anemia.xlsx"
CSV_FILE = "registros_anemia.csv"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar archivos si no existen
if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(columns=[
        "ID", "Lugar", "Trimestre", "Hemoglobina", "Semanas", "Resultado", "Foto", "Fecha"
    ])
    df_init.to_excel(EXCEL_FILE, index=False)

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID","Lugar","Trimestre","Hemoglobina","Semanas","Resultado","Foto","Fecha"
        ])

# -----------------------------
# FUNCIONES
# -----------------------------
def guardar_en_excel(registro):
    df = pd.read_excel(EXCEL_FILE)
    df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)

def guardar_en_csv(registro):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            registro["ID"],
            registro["Lugar"],
            registro["Trimestre"],
            registro["Hemoglobina"],
            registro["Semanas"],
            registro["Resultado"],
            registro["Foto"],
            registro["Fecha"]
        ])


# -----------------------------
# RUTAS
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generar", methods=["POST"])
def generar():
    lugar = request.form.get("lugar", "")
    trimestre = request.form.get("trimestre", "")
    hemoglobina = request.form.get("hemoglobina", "")
    semanas = request.form.get("semanas", "")
    resultado = request.form.get("resultado", "")

    # ID basado en filas actuales del Excel
    df = pd.read_excel(EXCEL_FILE)
    numero_paciente = len(df)

    # Guardar imagen renombrada
    foto = request.files.get("photo")
    if foto and foto.filename != "":
        extension = foto.filename.split(".")[-1].lower()
        foto_nombre = f"paciente{numero_paciente}_conjuntiva.{extension}"
        ruta_foto = os.path.join(UPLOAD_FOLDER, foto_nombre)
        foto.save(ruta_foto)
    else:
        foto_nombre = ""

    registro = {
        "ID": numero_paciente,
        "Lugar": lugar,
        "Trimestre": trimestre,
        "Hemoglobina": hemoglobina,
        "Semanas": semanas,
        "Resultado": resultado,
        "Foto": foto_nombre,
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    guardar_en_excel(registro)
    guardar_en_csv(registro)

    # regresar al inicio para poder ingresar otro
    return redirect(url_for("index"))


# Solo ejecutar con flask dev si ejecutas el archivo localmente (no cuando gunicorn lo importe)
if __name__ == "__main__":
    # Usa puerto del entorno si existe (Render lo provee), si no 5000 para pruebas locales
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
