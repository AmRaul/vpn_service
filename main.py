from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
import os
from create_clients import generate_vpn, create_qrcode, add_database, check_user_id, change_date
import sqlite3


app = FastAPI()
security = HTTPBasic()

auth_login = '****'
auth_pass = '****'

with sqlite3.connect("clients.sqlite") as con:
    cur = con.cursor()
    result = cur.execute(
        'CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,'
        ' chat_id char(255) UNIQUE,'
        ' date char(255))'
    )
    con.commit()


@app.get("/download_file")
def download_file(user_id: str = Query(..., title="User ID"), credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Create user
    generate_vpn(user_id)
    # Путь к файлу, который мы хотим вернуть
    file_path = f"/home/minima/configs/{user_id}.conf"

    # Проверяем, существует ли файл
    if not os.path.isfile(file_path):
        return {"message": f"Файл с user_id={user_id} не найден."}, 404

    # Возвращаем файл в ответе на запрос
    return FileResponse(file_path, headers={"Content-Disposition": f"attachment; filename={file_path}"})

@app.post("/download_file2")
def download_file(user_id: str = Query(..., title="User ID"), credentials: HTTPBasicCredentials = Depends(security)):
     if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
     # Create user
     generate_vpn(user_id)
     # Путь к файлу, который мы хотим вернуть
     file_path = f"/home/minima/configs/{user_id}.conf"

     # Проверяем, существует ли файл
     if not os.path.isfile(file_path):
        return {"message": f"Файл с user_id={user_id} не найден."}, 404

     # Возвращаем файл в ответе на запрос
     return FileResponse(file_path)

@app.get("/link_file")
def return_link_file(user_id: str = Query(..., title="User ID"),
                     pay_date: str = Query(..., title="Date Payment"),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = check_user_id(user_id)
    existing_chat_ids = [row[0] for row in result]
    if user_id not in existing_chat_ids:
        generate_vpn(user_id)
        add_database(user_id, pay_date)
    else:
        change_date(user_id, pay_date)

    file_path = f"/home/minima/configs/{user_id}.conf"

    if not os.path.isfile(file_path):
        return {"message": f"Файл с user_id={user_id} не найден."}, 404

    target_directory = f'/var/www/html/{user_id}.conf'

    with open(file_path, "r") as source_file:
        file_content = source_file.read()

    with open(target_directory, "w") as target_file:
        target_file.write(file_content)
    create_qrcode(user_id)
    return_link = f"https://rocketfire.ru/{user_id}.conf"
    return_qrcode = f"https://rocketfire.ru/qrcode/{user_id}.png"

    return JSONResponse(content={"link": return_link, "qrcode": return_qrcode})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
