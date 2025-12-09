from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def upload_test():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("credentials.json")

    drive = GoogleDrive(gauth)

    # ARCHIVO DE PRUEBA A SUBIR
    file = drive.CreateFile({"title": "prueba_drive.txt"})
    file.SetContentString("Hola, Google Drive!")
    file.Upload()

    print("Archivo subido correctamente.")

if __name__ == "__main__":
    upload_test()
