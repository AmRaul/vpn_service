import subprocess
import qrcode
import sqlite3
from datetime import datetime, timedelta

def generate_vpn(username):
    try:
        # Выполнение команды pivpn -a с указанным именем пользователя
        first_command = "pivpn -a"
        process1 = subprocess.run(first_command, input=username, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, shell=True, check=True)

        
        return process1.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения команды: {e}")
        print("Сообщение об ошибке:", e.stderr)
        return False




def create_qrcode(username):
    qr = qrcode.QRCode(
        version=10,  
        error_correction=qrcode.constants.ERROR_CORRECT_L,  
        box_size=10,  
        border=4,  
    )

    file_path = f"/home/minima/configs/{username}.conf"
    with open(file_path, "r") as source_file:
        data = source_file.read()

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    
    img.save(f"/var/www/html/qrcode/{username}.png")


def add_database(username, pay_date):
    new_date_str = new_date(pay_date)

    with sqlite3.connect("clients.sqlite") as con:
        cur = con.cursor()
        cur.execute(
            'INSERT INTO users(chat_id, date) VALUES(?, ?)', (username, new_date_str)
        )
        con.commit()

def on_vpn(username):
    command = f"/usr/local/bin/pivpn -on -n {username}"
    try:
        # Подавляем запрос на подтверждение и автоматически соглашаемся (Y)
        subprocess.check_output(f"echo 'Y' | {command}", shell=True, text=True)
        output = username + ' - Enable'
        return output
    except subprocess.CalledProcessError:
        e = 'Error'
        return e


def change_date(username, pay_date):
    with sqlite3.connect("clients.sqlite") as con:
        cur = con.cursor()

        # Получаем текущую дату клиента
        client_date_str = cur.execute(
            'SELECT date FROM users WHERE chat_id = ?', (username,)
        ).fetchone()[0]

        client_date = datetime.strptime(client_date_str, "%Y-%m-%d %H:%M:%S")
        current_date = datetime.now()

        # Проверяем, прошла ли дата
        if current_date < client_date:
            # Добавляем заданное количество дней к текущей дате клиента
            new_client_date = client_date + timedelta(days=int(pay_date))
            new_date_str = new_client_date.strftime("%Y-%m-%d %H:%M:%S")

            # Обновляем дату клиента
            cur.execute(
                'UPDATE users SET date = ? WHERE chat_id = ?', (new_date_str, username,)
            )
            con.commit()
        else:
            new_date_str = new_date(pay_date)
            cur.execute(
                'UPDATE users SET date = ? WHERE chat_id = ?', (new_date_str, username,)
            )
            con.commit()
            on_vpn(username)

def check_user_id(username):
    with sqlite3.connect("clients.sqlite") as con:
        cur = con.cursor()
        result = cur.execute(
            'SELECT chat_id FROM users WHERE chat_id = ?', (username,)
        ).fetchall()

        return result

def new_date(pay_date):
    current_date = datetime.now()
    new_date = current_date + timedelta(days=int(pay_date))
    new_date_str = new_date.strftime("%Y-%m-%d %H:%M:%S")
    return new_date_str
