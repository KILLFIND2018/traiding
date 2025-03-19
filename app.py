from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import threading
import time
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app, resources={r"/static/*": {"origins": "*"}})

MYSQL_CONFIG = {
    'user': '',
    'password': '',
    'host': '',
    'database': '',
    'raise_on_warnings': True
}

user_heartbeats = {}

def calculate_balance(current_balance, progression_factor, last_updated, total_generation):
    now = datetime.now()
    seconds_elapsed = (now - last_updated).total_seconds()
    
    if seconds_elapsed <= 60:
        new_balance = current_balance + total_generation * seconds_elapsed
    else:
        progression_time = max(0, seconds_elapsed - 60)
        new_balance = current_balance + total_generation * 60
        new_balance += total_generation * (progression_factor + 0.001 * progression_time)
        progression_factor += 0.001 * progression_time
    
    return int(new_balance), progression_factor

def generation_loop(user_id):
    while True:
        try:
            connection = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = connection.cursor()

            cursor.execute("SELECT is_active, balance, total_generation, progression_factor, last_updated FROM user_progress WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()

            if not result or result[0] == 0:
                print(f"Генерация для user_id {user_id} остановлена: is_active = 0")
                break

            if user_id in user_heartbeats:
                last_heartbeat = user_heartbeats[user_id]
                if (datetime.now() - last_heartbeat).total_seconds() > 10:  # Уменьшенный тайм-аут
                    cursor.execute("UPDATE user_progress SET is_active = 0 WHERE user_id = %s", (user_id,))
                    connection.commit()
                    print(f"Генерация для user_id {user_id} остановлена: нет heartbeat более 10 секунд")
                    break

            balance, total_generation, progression_factor, last_updated = result[1:]
            total_generation = total_generation or 1
            last_updated = last_updated or datetime.now()

            new_balance, new_progression = calculate_balance(balance, progression_factor or 1.0, last_updated, total_generation)

            cursor.execute("""
                UPDATE user_progress 
                SET balance = %s, progression_factor = %s, last_updated = %s 
                WHERE user_id = %s
            """, (new_balance, new_progression, datetime.now(), user_id))
            connection.commit()
            print(f"Генерация для user_id {user_id}: balance = {new_balance}, progression_factor = {new_progression}")

            time.sleep(1)
        except mysql.connector.Error as err:
            print(f"Ошибка в генерации для user_id {user_id}: {err}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400
    
    user_heartbeats[user_id] = datetime.now()
    print(f"Heartbeat получен для user_id {user_id}")
    return jsonify({"status": "success"}), 200

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_generation():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT balance, total_generation, is_active FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            balance, total_generation, is_active = result
            if not is_active:
                cursor.execute("UPDATE user_progress SET is_active = 1, last_updated = %s WHERE user_id = %s", (datetime.now(), user_id))
                threading.Thread(target=generation_loop, args=(user_id,), daemon=True).start()
                print(f"Генерация для user_id {user_id} запущена")
            connection.commit()
            return jsonify({"status": "success", "balance": balance}), 200
        else:
            return jsonify({"status": "error", "message": "User not found, please start via Telegram bot"}), 404

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/stop', methods=['POST'])
def stop_generation():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("UPDATE user_progress SET is_active = 0 WHERE user_id = %s", (user_id,))
        connection.commit()
        print(f"Генерация для user_id {user_id} остановлена по запросу клиента")
        if user_id in user_heartbeats:
            del user_heartbeats[user_id]
        return jsonify({"status": "success", "message": "Generation stopped"}), 200

    except mysql.connector.Error as err:
        print(f"Ошибка при остановке генерации для user_id {user_id}: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/get_balance', methods=['GET'])
def get_balance():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT balance, total_generation, progression_factor, last_updated, is_active FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            balance, total_generation, progression_factor, last_updated, is_active = result
            total_generation = total_generation or 1
            last_updated = last_updated or datetime.now()

            if is_active:
                new_balance, new_progression = calculate_balance(balance, progression_factor or 1.0, last_updated, total_generation)
                cursor.execute("""
                    UPDATE user_progress 
                    SET balance = %s, progression_factor = %s, last_updated = %s 
                    WHERE user_id = %s
                """, (new_balance, new_progression, datetime.now(), user_id))
                connection.commit()
                balance = new_balance

            return jsonify({"status": "success", "balance": balance}), 200
        else:
            return jsonify({"status": "error", "message": "User not found"}), 404

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/buy_item', methods=['POST'])
def buy_item():
    data = request.json
    user_id = data.get('user_id')
    item_name = data.get('item_name')
    item_cost = data.get('item_cost')
    item_generation = data.get('item_generation')

    if not all([user_id, item_name, item_cost, item_generation]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        if cursor.fetchone()[0] > 0:
            return jsonify({"status": "error", "message": "Item already owned"}), 400

        cursor.execute("SELECT balance, total_generation, last_updated FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "error", "message": "User not found"}), 404

        balance, total_generation, last_updated = result
        total_generation = total_generation or 1
        last_updated = last_updated or datetime.now()

        new_balance, _ = calculate_balance(balance, 1.0, last_updated, total_generation)

        if new_balance < item_cost:
            return jsonify({"status": "error", "message": "Insufficient funds"}), 400

        new_balance -= item_cost
        new_total_generation = total_generation + item_generation

        cursor.execute("""
            UPDATE user_progress 
            SET balance = %s, total_generation = %s, last_updated = %s 
            WHERE user_id = %s
        """, (new_balance, new_total_generation, datetime.now(), user_id))

        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, generation_per_hour) 
            VALUES (%s, %s, %s)
        """, (user_id, item_name, item_generation))

        connection.commit()
        return jsonify({"status": "success", "balance": new_balance, "total_generation": new_total_generation}), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/get_market', methods=['GET'])
def get_market():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT name, generation_per_second AS generation, price FROM market_items")
        items = cursor.fetchall()

        return jsonify({"status": "success", "items": items}), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/get_inventory', methods=['GET'])
def get_inventory():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT item_name, generation_per_hour FROM inventory WHERE user_id = %s", (user_id,))
        items = cursor.fetchall()

        return jsonify({"status": "success", "items": items}), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/get_rating', methods=['GET'])
def get_rating():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Получаем всех активных пользователей, сортируем по убыванию баланса
        cursor.execute("""
            SELECT username, balance 
            FROM user_progress 
            ORDER BY balance DESC
        """)
        users = cursor.fetchall()

        # Добавляем позицию в рейтинге
        for index, user in enumerate(users, start=1):
            user['position'] = index

        return jsonify({"status": "success", "users": users}), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/buy_with_stars', methods=['POST'])
def buy_with_stars():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')  # Количество монет
    stars_cost = data.get('stars_cost')  # Стоимость в Stars

    if not all([user_id, amount, stars_cost]):
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Получаем текущие данные пользователя
        cursor.execute("SELECT balance, total_generation, last_updated FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        balance, total_generation, last_updated = result
        total_generation = total_generation or 1
        last_updated = last_updated or datetime.now()

        # Рассчитываем обновленный баланс (Stars обрабатываются Telegram, мы добавляем монеты)
        new_balance, _ = calculate_balance(balance, 1.0, last_updated, total_generation)
        new_balance += amount  # Добавляем купленные монеты

        # Обновляем баланс в базе данных
        cursor.execute("""
            UPDATE user_progress 
            SET balance = %s, last_updated = %s 
            WHERE user_id = %s
        """, (new_balance, datetime.now(), user_id))

        connection.commit()
        print(f"Пользователь {user_id} купил {amount} монет за {stars_cost} Stars. Новый баланс: {new_balance}")

        return jsonify({"status": "success", "new_balance": new_balance}), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)