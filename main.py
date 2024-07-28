from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
import os
from create_clients import generate_vpn, create_qrcode, add_database, check_user_id, change_date, on_vpn
import sqlite3
from enable.main import disable_manual_profile
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json

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



@app.get("/create_profile")
def create_profile(user_id: str = Query(..., title="User ID"),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = 'i' + str(user_id)
    generate_vpn(user_id)

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

@app.get("/disenable_profile")
def disenable_profile_client(user_id: str = Query(..., title="User ID"),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = 'i' + str(user_id)
    result = disable_manual_profile(user_id)

    return JSONResponse(content=result)


@app.get("/enable_profile")
def enable_profile_client(user_id: str = Query(..., title="User ID"),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = 'i' + str(user_id)
    result = on_vpn(user_id)

    return JSONResponse(content=result)


@app.get("/link_file")
def return_link_file(user_id: str = Query(..., title="User ID"),
                     pay_date: str = Query(..., title="Date Payment"),
                     credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = 'i' + str(user_id)
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

# Функция для изменения имени ключа
def change_key_name(api_url, key_id, new_name):
    data = {'name': new_name}
    response = requests.put(f'{api_url}/access-keys/{key_id}/name', data=data, verify=False)
    if response.status_code == 204:
        return True
    else:
        return False

@app.get("/outline/create")
def create_keys(user_id: str = Query(..., title="User ID"),
                credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    api_url = '*****'
    
    # Создание ключа
    response = requests.post(f'{api_url}/access-keys/', verify=False)
    
    # Проверка успешности запроса
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Failed to create key")
    
    key_id = response.json().get('id')
    new_name = user_id  # Замените на желаемое имя
    
    # Вызов функции для изменения имени ключа
    if change_key_name(api_url, key_id, new_name):
        return JSONResponse(content={"key": response.json()['accessUrl']})
    else:
        raise HTTPException(status_code=500, detail="Failed to change key name")


@app.get("/outline/response_key")
def response_key(user_id: str = Query(..., title="User ID"),
                credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    api_url = '*****'

    response = requests.get(f'{api_url}/access-keys/', verify=False)

    # Используйте json.loads() для преобразования строки JSON в объект Python
    response_data = json.loads(response.text)

    filtered_data = next((item for item in response_data['accessKeys'] if item.get('name') == user_id), None)

    if filtered_data:
        return {"key": filtered_data.get('accessUrl')}
    else:
        raise HTTPException(status_code=404, detail="Key not found")


@app.get("/outline/limit_off")
def limit_off(user_id: str = Query(..., title="User ID"),
                credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    api_url = '*****/access-keys/{id}/data-limit'
    api_url_data = '*******'

    response = requests.get(f'{api_url_data}/access-keys/', verify=False)
    
    # Используйте json.loads() для преобразования строки JSON в объект Python
    response_data = json.loads(response.text)
    
    filtered_data = next((item for item in response_data['accessKeys'] if item.get('name') == user_id), None)
    
    id_key = filtered_data['id']
    
    # Создаем JSON-запрос
    json_data = {
        "limit": {
            "bytes": 10000
        }
    }
    
    headers = {'Content-type': 'application/json'}
    
    # Выполняем PUT-запрос для обновления данных о лимите
    response = requests.put(api_url.replace('{id}', id_key), json=json_data, headers=headers, verify=False)
    
    if response.status_code == 204:
        return JSONResponse(content={"code": 200, "message": "disable"})
    else:
        raise HTTPException(status_code=500, detail="Ошибка при изменении лимита")


@app.get("/outline/limit_delete")
def limit_delete(user_id: str = Query(..., title="User ID"),
                credentials: HTTPBasicCredentials = Depends(security)):
    if not (auth_login == credentials.username and credentials.password == auth_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    api_url = '*****/access-keys/{id}/data-limit'
    api_url_data = '*****'

    response = requests.get(f'{api_url_data}/access-keys/', verify=False)
    
    # Используйте json.loads() для преобразования строки JSON в объект Python
    response_data = json.loads(response.text)
    
    filtered_data = next((item for item in response_data['accessKeys'] if item.get('name') == user_id), None)
    
    id_key = filtered_data['id']
    
    # Выполняем DELETE-запрос
    response = requests.delete(api_url.replace('{id}', id_key), verify=False)

    if response.status_code == 204:
        return JSONResponse(content={"code": 200, "message": "enable"})
    else:
        raise HTTPException(status_code=500, detail="Ошибка при удалении лимита")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

