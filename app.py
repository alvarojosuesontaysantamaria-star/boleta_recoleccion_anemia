from flask import Flask, render_template, request, redirect, url_for
import os
import csv
from datetime import datetime
import pandas as pd
import tempfile

# ---------- GOOGLE DRIVE ----------
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

GOOGLE_DRIVE_FOLDER_ID = "1lkWk5WNYSSPPMg-Z_bH-dBbTsA7qz2eu"  # tu carpeta


def create_drive_service():
    json_data = os.getenv("SERVICE_ACCOUNT_JSON")

    if not json_data:
        raise Exception("❌ ERROR: Falta la variable SERVICE_ACCOUNT_JSON en Render")

    # Crear archivo temporal con el JSON
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(json_data.encode("utf-8"))
        path = tmp.name

    creds = service_account.Credentials.from_service_account_file(
        path,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


drive_service = create_drive_service()

# ----------------------------------

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
CSV_FILE = "registros_anemia.csv"
EXCEL_FILE = "registros_anemia.xlsx"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Crear Excel si no existe
if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(columns=[
        "ID", "Lugar", "Trimestre", "Hemoglobina",
        "Semanas", "Resultado", "Foto", "Fecha"
    ])
    df_init.to_excel(EXCEL_FILE, index=False)


# ----------- SUBIR ARCHIVO A DRIVE ----------------
def upload_to_drive(filepath, filename):
    file_metadata = {
        "name": filename,
        "parents": [GOOGLE_DRIVE_FOLDER_ID]
    }

    media = MediaFileUpload(filepath, resumable=True)

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    print("Archivo subido a Drive:", filename)
    return file.get("id")
# ---------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generar", methods=["POST"])
def generar():
    lugar = request.form["lugar"]
    trimestre = request.form["trimestre"]
    hemoglobina = request.form["hemoglobina"]
    semanas = request.form["semanas"]
    resultado = request.form["resultado"]

    # Calcular ID
    registros_previos = 0
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            registros_previos = sum(1 for _ in f) - 1

    numero_paciente = registros_previos + 1

    # Guardar foto
    foto = request.files["photo"]
    extension = foto.filename.split(".")[-1]
    nuevo_nombre = f"paciente{numero_paciente}_conjuntiva.{extension}"
    ruta_foto = os.path.join(UPLOAD_FOLDER, nuevo_nombre)
    foto.save(ruta_foto)

    # Subir foto
    upload_to_drive(ruta_foto, nuevo_nombre)

    # Guardar CSV
    archivo_nuevo = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if archivo_nuevo:
            writer.writerow([
                "ID", "Lugar", "Trimestre", "Hemoglobina",
                "Semanas", "Resultado", "Foto", "Fecha"
            ])
        writer.writerow([
            numero_paciente, lugar, trimestre, hemoglobina, semanas,
            resultado, nuevo_nombre,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

    # Guardar Excel
    df = pd.read_excel(EXCEL_FILE)
    df.loc[len(df)] = [
        numero_paciente, lugar, trimestre, hemoglobina,
        semanas, resultado, nuevo_nombre,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    df.to_excel(EXCEL_FILE, index=False)

    # Subir Excel actualizado
    upload_to_drive(EXCEL_FILE, "registros_anemia.xlsx")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
