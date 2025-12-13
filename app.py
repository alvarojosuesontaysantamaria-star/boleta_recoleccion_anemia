from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os
import tempfile

# -------- CLOUDINARY --------
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# -------- GOOGLE SHEETS --------
from google.oauth2 import service_account
from googleapiclient.discovery import build

SPREADSHEET_ID = "17I58LOPaHVIMueCR_c_aRi-79_-n7_v0BXjq-YjLlFU"
SHEET_NAME = "Hoja 1"

def get_sheets_service():
    json_data = os.getenv("SERVICE_ACCOUNT_JSON")
    if not json_data:
        raise Exception("❌ Falta SERVICE_ACCOUNT_JSON en Render")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(json_data.encode("utf-8"))
        json_path = tmp.name

    creds = service_account.Credentials.from_service_account_file(
        json_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    return build("sheets", "v4", credentials=creds)

sheets_service = get_sheets_service()

# -------- APP --------
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generar", methods=["POST"])
def generar():
    # 📋 DATOS DEL FORMULARIO
    edad = request.form["edad"]
    centro = request.form["lugar"]
    trimestre = request.form["trimestre"]
    hemoglobina = request.form["hemoglobina"]
    semanas = request.form["semanas"]

    # 📸 SUBIR IMAGEN A CLOUDINARY
    foto = request.files["photo"]

    upload_result = cloudinary.uploader.upload(
        foto,
        folder="anemia_conjuntiva"
    )

    image_url = upload_result["secure_url"]

    # 🔢 CALCULAR ID DE PACIENTE (filas actuales)
    sheet_data = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:A"
    ).execute()

    filas_actuales = len(sheet_data.get("values", []))
    numero_paciente = filas_actuales  # fila 1 = encabezado

    # 📝 NUEVA FILA (orden EXACTO del Sheet)
    nueva_fila = [
        numero_paciente,                         # A ID_Paciente
        edad,                                    # B Edad
        centro,                                  # C Centro_Atencion
        trimestre,                               # D Trimestre
        hemoglobina,                             # E Hemoglobina
        semanas,                                 # F Semanas_Gestacion
        image_url,                               # G URL_Imagen
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # H Fecha
    ]

    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:H",
        valueInputOption="USER_ENTERED",
        body={"values": [nueva_fila]}
    ).execute()

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
