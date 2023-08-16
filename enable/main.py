from datetime import datetime
import subprocess
import sqlite3

def disable_expired_clients():
    with sqlite3.connect("/home/vpn/clients.sqlite") as con:
        cur = con.cursor()
        result = cur.execute(
            'SELECT chat_id, date FROM users'
        ).fetchall()

        current_date = datetime.now()

        for row in result:
            chat_id = row[0]
            cl_date_str = row[1]  # Получаем строку с датой из результата запроса
            cl_date = datetime.strptime(cl_date_str, "%Y-%m-%d %H:%M:%S")  # Преобразовываем строку в объект datetime

            if current_date > cl_date:
                command = f"/usr/local/bin/pivpn -off -n {chat_id}"
                try:
                    # Подавляем запрос на подтверждение и автоматически соглашаемся (Y)
                    output = subprocess.check_output(f"echo 'Y' | {command}", shell=True, text=True)
                    print(f"Disabled client {chat_id}. Command output:", output)
                except subprocess.CalledProcessError as e:
                    print("Error:", e)


if __name__ == '__main__':
    disable_expired_clients()
