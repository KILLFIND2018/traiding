from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import threading
import time
import random
from config import MYSQL_CONFIG  # Импорт конфигурации

import logging

# Отключаем логи запросов
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app, resources={r"/static/*": {"origins": "*"}})

user_heartbeats = {}

def calculate_balance(current_balance, progression_factor, last_updated, total_generation):
    now = datetime.now()
    seconds_elapsed = (now - last_updated).total_seconds()
    
    # Базовая генерация за первые 60 секунд без прогрессии
    if seconds_elapsed <= 60:
        new_balance = current_balance + total_generation * seconds_elapsed
        new_progression = 0  # Прогрессия начинается с 0
    else:
        # Базовая генерация за первые 60 секунд
        progression_time = max(0, seconds_elapsed - 60)
        new_balance = current_balance + total_generation * 60
        
        # Расчет увеличения прогрессии: 0.01 за каждые, например, 300 секунд (5 минут)
        progression_step = 0.01  # Начальный шаг прогрессии
        progression_increase = int(progression_time / 300)  # Каждые 5 минут +0.01
        new_progression = progression_step * progression_increase  # Например, 0.01, 0.02, 0.03...
        
        # Ограничение прогрессии, чтобы не уйти в бесконечность (опционально)
        new_progression = min(new_progression, 0.50)  # Максимум 0.50, например
        
        # Применяем прогрессию к генерации после 60 секунд
        new_balance += total_generation * progression_time * new_progression

    # Учитываем, что баланс — BIGINT, округляем до целого числа
    return int(new_balance), new_progression

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
                cursor.execute("UPDATE user_progress SET is_active = 1, last_updated = %s, progression_factor = 0 WHERE user_id = %s", (datetime.now(), user_id))
                threading.Thread(target=generation_loop, args=(user_id,), daemon=True).start()
                print(f"Генерация для user_id {user_id} запущена")
            connection.commit()
            return jsonify({"status": "success", "balance": balance}), 200
        else:
            return jsonify({"status": "error", "message": "Пользователь не найден, пожалуйста, начните через Telegram-бота"}), 404

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
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Проверяем, есть ли предмет уже в инвентаре
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        if cursor.fetchone()[0] > 0:
            return jsonify({
                "status": "error", 
                "message": f"⚠️ {item_name} уже есть в вашем инвентаре!"
            }), 400

        # Получаем текущий прогресс пользователя
        cursor.execute("SELECT balance, total_generation, last_updated FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        balance, total_generation, last_updated = result
        total_generation = total_generation or 1
        last_updated = last_updated or datetime.now()

        # Рассчитываем новый баланс с учетом времени
        new_balance, _ = calculate_balance(balance, 1.0, last_updated, total_generation)

        # Проверяем, хватает ли средств после обновления баланса
        if new_balance < item_cost:
            return jsonify({
                "status": "error", 
                "message": "Недостаточно средств для покупки!"
            }), 400  # Сообщение на русском

        # Обновляем баланс и генерацию
        new_balance -= item_cost
        new_total_generation = total_generation + item_generation

        cursor.execute("""
            UPDATE user_progress 
            SET balance = %s, total_generation = %s, last_updated = %s 
            WHERE user_id = %s
        """, (new_balance, new_total_generation, datetime.now(), user_id))

        # Добавляем предмет в инвентарь
        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, generation_per_hour) 
            VALUES (%s, %s, %s)
        """, (user_id, item_name, item_generation))

        connection.commit()
        return jsonify({
            "status": "success", 
            "balance": new_balance, 
            "total_generation": new_total_generation
        }), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Ошибка базы данных: {err}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/get_market', methods=['GET'])
def get_market():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT name, generation_per_hour AS generation, price FROM market_items")
        items = cursor.fetchall()

        # Добавляем путь к изображению для каждого предмета
        for item in items:
            image_name = item['name'].replace(' ', '_').lower() + '.png'
            item['image_path'] = f'/static/img-market/{image_name}'

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

@app.route('/get_auction_lots', methods=['GET'])
def get_auction_lots():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT l.lot_id, l.item_name, l.description, l.start_price, l.current_bid, u.username AS seller_username, l.seller_id
            FROM auction_lots l
            JOIN user_progress u ON l.seller_id = u.user_id
            WHERE l.is_active = 1
        """)
        lots = cursor.fetchall()
        return jsonify({"status": "success", "lots": lots}), 200
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/create_lot', methods=['POST'])
def create_lot():
    data = request.json
    user_id = data.get('user_id')
    item_name = data.get('item_name')
    description = data.get('description')
    start_price = data.get('start_price')

    if not all([user_id, item_name, description, start_price]):
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        #Проверка наличия предмета в инвентаре и получение его генерации
        cursor.execute("SELECT generation_per_hour FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        inventory_item = cursor.fetchone()
        if not inventory_item:
            return jsonify({"status": "error", "message": "Товар не найден в инвентаре"}), 400

        generation_per_hour = inventory_item[0]

        # Уменьшаем total_generation продавца
        cursor.execute("""
            UPDATE user_progress 
            SET total_generation = total_generation - %s 
            WHERE user_id = %s
        """, (generation_per_hour, user_id))

        # Создание лота
        cursor.execute("""
            INSERT INTO auction_lots (seller_id, item_name, description, start_price)
            VALUES (%s, %s, %s, %s)
        """, (user_id, item_name, description, start_price))

        # Удаление предмета из инвентаря продавца
        cursor.execute("DELETE FROM inventory WHERE user_id = %s AND item_name = %s LIMIT 1", (user_id, item_name))
        
        connection.commit()
        return jsonify({"status": "success"}), 200
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/place_bid', methods=['POST'])
def place_bid():
    data = request.json
    user_id = data.get('user_id')
    lot_id = data.get('lot_id')
    bid_amount = data.get('bid_amount')

    if not all([user_id, lot_id, bid_amount]):
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Проверка лота
        cursor.execute("SELECT start_price, current_bid, seller_id FROM auction_lots WHERE lot_id = %s AND is_active = 1", (lot_id,))
        lot = cursor.fetchone()
        if not lot:
            return jsonify({"status": "error", "message": "Лот не найден или неактивен"}), 404

        start_price, current_bid, seller_id = lot
        if user_id == seller_id:
            return jsonify({"status": "error", "message": "Вы не можете делать ставки на свой собственный лот."}), 400

        min_bid = current_bid or start_price
        if bid_amount <= min_bid:
            return jsonify({"status": "error", "message": "Ставка должна быть выше текущей ставки"}), 400

        # Проверка баланса
        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (user_id,))
        balance = cursor.fetchone()[0]
        if balance < bid_amount:
            return jsonify({"status": "error", "message": "Недостаточно средств"}), 400

        # Обновление ставки
        cursor.execute("""
            UPDATE auction_lots 
            SET current_bid = %s, current_bidder_id = %s 
            WHERE lot_id = %s
        """, (bid_amount, user_id, lot_id))
        connection.commit()
        return jsonify({"status": "success"}), 200
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/complete_lot', methods=['POST'])
def complete_lot():
    data = request.json
    user_id = data.get('user_id')
    lot_id = data.get('lot_id')

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Сначала получаем данные лота
        cursor.execute("""
            SELECT seller_id, item_name, current_bid, current_bidder_id 
            FROM auction_lots 
            WHERE lot_id = %s AND is_active = 1
        """, (lot_id,))
        lot = cursor.fetchone()
        if not lot:
            return jsonify({"status": "error", "message": "Лот не найден или неактивен"}), 404

        seller_id, item_name, current_bid, current_bidder_id = lot
        if seller_id != user_id:
            return jsonify({"status": "error", "message": "Только продавец может завершить лот."}), 403

        if not current_bidder_id:
            return jsonify({"status": "error", "message": "Пока нет ставок"}), 400

        # Получаем generation_per_hour из market_items
        cursor.execute("SELECT generation_per_hour FROM market_items WHERE name = %s", (item_name,))
        market_item = cursor.fetchone()
        if not market_item:
            return jsonify({"status": "error", "message": "Предмет не найден в магазине"}), 404
        generation_per_hour = market_item[0]

        # Проверка баланса покупателя
        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (current_bidder_id,))
        buyer_balance = cursor.fetchone()[0]
        if buyer_balance < current_bid:
            return jsonify({"status": "error", "message": "У покупателя недостаточно средств"}), 400

        # Списание средств у покупателя
        cursor.execute("UPDATE user_progress SET balance = balance - %s WHERE user_id = %s", (current_bid, current_bidder_id))
        # Начисление средств продавцу
        cursor.execute("UPDATE user_progress SET balance = balance + %s WHERE user_id = %s", (current_bid, seller_id))
        # Передача предмета покупателю
        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, generation_per_hour)
            VALUES (%s, %s, %s)
        """, (current_bidder_id, item_name, generation_per_hour))
        # Увеличиваем total_generation покупателя
        cursor.execute("""
            UPDATE user_progress 
            SET total_generation = total_generation + %s 
            WHERE user_id = %s
        """, (generation_per_hour, current_bidder_id))
        # Завершение лота
        cursor.execute("UPDATE auction_lots SET is_active = 0 WHERE lot_id = %s", (lot_id,))

        connection.commit()
        return jsonify({"status": "success"}), 200
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/get_chat', methods=['GET'])
def get_chat():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.username, c.message, c.timestamp 
            FROM auction_chat c 
            JOIN user_progress u ON c.user_id = u.user_id 
            ORDER BY c.timestamp ASC 
            LIMIT 50
        """)
        messages = cursor.fetchall()
        return jsonify({"status": "success", "messages": messages}), 200
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/send_chat', methods=['POST'])
def send_chat():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')

    if not all([user_id, message]):
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO auction_chat (user_id, message) VALUES (%s, %s)", (user_id, message))
        connection.commit()
        return jsonify({"status": "success"}), 200
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()


import requests

@app.route('/get_bitcoin_price', methods=['GET'])
def get_bitcoin_price():
    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
        data = response.json()
        price = data['bitcoin']['usd']
        return jsonify({"status": "success", "price": price}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/place_bitcoin_bet', methods=['POST'])
def place_bitcoin_bet():
    data = request.json
    user_id = data.get('user_id')
    bet_amount = data.get('bet_amount')
    bet_direction = data.get('bet_direction')

    if not all([user_id, bet_amount, bet_direction]):
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        connection.autocommit = False  # Отключаем авто-коммит

        cursor = connection.cursor()

        # Проверка последней ставки
        cursor.execute("SELECT bet_time FROM bitcoin_bets WHERE user_id = %s ORDER BY bet_time DESC LIMIT 1", (user_id,))
        last_bet = cursor.fetchone()
        cursor.fetchall()  # Очистка буфера

        if last_bet:
            last_bet_time = last_bet[0]
            cooldown = 100  # 100 секунд
            if (datetime.now() - last_bet_time).total_seconds() < cooldown:
                return jsonify({"status": "error", "message": "Ставка доступна раз в 100 секунд"}), 400

        # Получение баланса с блокировкой строки
        cursor.execute(
            "SELECT balance, total_generation, last_updated FROM user_progress WHERE user_id = %s FOR UPDATE", 
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.fetchall()

        if not result:
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        balance, total_generation, last_updated = result
        current_balance, _ = calculate_balance(
            balance, 
            1.0, 
            last_updated or datetime.now(), 
            total_generation or 1
        )

        if current_balance < bet_amount:
            return jsonify({"status": "error", "message": "Недостаточно средств"}), 400

        # Получение цены BTC
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd',
                timeout=5
            )
            btc_price = response.json()['bitcoin']['usd']
        except Exception as e:
            connection.rollback()
            return jsonify({"status": "error", "message": f"Ошибка получения цены BTC: {str(e)}"}), 500

        # Списание средств
        cursor.execute(
            "UPDATE user_progress SET balance = %s, last_updated = %s WHERE user_id = %s",
            (current_balance - bet_amount, datetime.now(), user_id)
        )

        # Запись ставки
        cursor.execute(
            """INSERT INTO bitcoin_bets 
            (user_id, bet_amount, bet_direction, bet_time, bet_price)
            VALUES (%s, %s, %s, %s, %s)""",
            (user_id, bet_amount, bet_direction, datetime.now(), btc_price)
        )

        connection.commit()  # Фиксация транзакции

        return jsonify({
            "status": "success",
            "new_balance": current_balance - bet_amount,
            "bet_price": btc_price
        }), 200

    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        return jsonify({"status": "error", "message": f"Ошибка БД: {str(err)}"}), 500
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"status": "error", "message": f"Ошибка: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/check_bitcoin_bet', methods=['GET'])
def check_bitcoin_bet():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Читаем все результаты запроса
        cursor.execute("SELECT bet_amount, bet_direction, bet_time, bet_price, resolved FROM bitcoin_bets WHERE user_id = %s", (user_id,))
        bets = cursor.fetchall()

        # Если ставок нет или все разрешены
        if not bets or all(bet[4] for bet in bets):
            return jsonify({"status": "success", "message": "Нет активных ставок"}), 200

        # Берем первую активную ставку
        for bet in bets:
            if not bet[4]:  # Ищем unresolved ставку
                bet_amount, bet_direction, bet_time, bet_price = bet[0:4]
                break
        else:
            return jsonify({"status": "success", "message": "Нет активных ставок"}), 200

        # Проверка времени
        if (datetime.now() - bet_time).total_seconds() < 10:  # 24 часа
            remaining = 10 - (datetime.now() - bet_time).total_seconds()
            return jsonify({"status": "pending", "remaining": int(remaining)}), 200

        # Получение текущей цены
        btc_price_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd').json()
        current_price = btc_price_response['bitcoin']['usd']

        # Проверка результата
        won = (bet_direction == 'up' and current_price > bet_price) or (bet_direction == 'down' and current_price < bet_price)
        prize = bet_amount * 2 if won else 0

        # Обновление данных
        cursor.execute("UPDATE user_progress SET balance = balance + %s WHERE user_id = %s", (prize, user_id))
        cursor.execute("UPDATE bitcoin_bets SET resolved = TRUE WHERE user_id = %s", (user_id,))
        connection.commit()

        return jsonify({"status": "success", "won": won, "prize": prize}), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

@app.route('/generate_referral', methods=['POST'])
def generate_referral():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400
    
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # Генерируем уникальный реферальный код
        import uuid
        referral_code = str(uuid.uuid4())[:8]
        
        cursor.execute("""
            INSERT INTO referrals (user_id, referral_code, created_at)
            VALUES (%s, %s, %s)
        """, (user_id, referral_code, datetime.now()))
        
        connection.commit()
        return jsonify({"status": "success", "referral_code": referral_code}), 200
        
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/use_referral', methods=['POST'])
def use_referral():
    data = request.json
    user_id = data.get('user_id')
    referral_code = data.get('referral_code')
    
    if not all([user_id, referral_code]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("SELECT user_id FROM referrals WHERE referral_code = %s AND used_by IS NULL", (referral_code,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"status": "error", "message": "Invalid or used referral code"}), 400
            
        referrer_id = result[0]
        
        if referrer_id == user_id:
            return jsonify({"status": "error", "message": "You cannot use your own referral"}), 400
            
        cursor.execute("SELECT COUNT(*) FROM referrals WHERE used_by = %s", (user_id,))
        if cursor.fetchone()[0] > 0:
            return jsonify({"status": "error", "message": "You have already used a referral"}), 400
            
        cursor.execute("""
            UPDATE referrals 
            SET used_by = %s, used_at = %s 
            WHERE referral_code = %s
        """, (user_id, datetime.now(), referral_code))
        
        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, generation_per_hour)
            VALUES (%s, %s, %s)
        """, (referrer_id, "Macbook", 50))
        
        connection.commit()
        return jsonify({"status": "success", "message": "Referral used successfully"}), 200
        
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/get_new_rewards', methods=['GET'])
def get_new_rewards():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Получаем награды, для которых алерт еще не показан
        cursor.execute("""
            SELECT id, item_name, awarded_at 
            FROM rewards 
            WHERE user_id = %s AND alert_shown = FALSE
        """, (user_id,))
        rewards = cursor.fetchall()

        # Если есть новые награды, возвращаем их
        if rewards:
            # Отмечаем алерт как показанный
            cursor.execute("""
                UPDATE rewards 
                SET alert_shown = TRUE 
                WHERE user_id = %s AND alert_shown = FALSE
            """, (user_id,))
            connection.commit()
        
        return jsonify({"status": "success", "rewards": rewards})

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()
@app.route('/get_login_reward_status', methods=['GET'])
def get_login_reward_status():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Проверяем время последнего получения награды
        cursor.execute("""
            SELECT last_reward_time, total_generation, balance, last_updated 
            FROM user_progress 
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "error", "message": "User not found"}), 404

        last_reward_time, total_generation, balance, last_updated = result
        total_generation = total_generation or 1
        last_updated = last_updated or datetime.now()

        current_time = datetime.now()
        reward_interval = 240  # 4 минуты в секундах

        # Если время последнего вознаграждения не установлено
        if not last_reward_time:
            return jsonify({
                "status": "available",
                "remaining": 0,
                "total_generation": total_generation
            }), 200

        time_since_last_reward = (current_time - last_reward_time).total_seconds()
        
        if time_since_last_reward >= reward_interval:
            return jsonify({
                "status": "available",
                "remaining": 0,
                "total_generation": total_generation
            }), 200
        else:
            remaining = reward_interval - time_since_last_reward
            return jsonify({
                "status": "pending",
                "remaining": int(remaining),
                "total_generation": total_generation
            }), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/claim_login_reward', methods=['POST'])
def claim_login_reward():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT last_reward_time, total_generation, balance, last_updated 
            FROM user_progress 
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "error", "message": "User not found"}), 404

        last_reward_time, total_generation, balance, last_updated = result
        total_generation = total_generation or 1
        last_updated = last_updated or datetime.now()

        current_time = datetime.now()
        reward_interval = 240  # 4 минуты в секундах

        # Проверяем, доступна ли награда
        if last_reward_time and (current_time - last_reward_time).total_seconds() < reward_interval:
            return jsonify({"status": "error", "message": "Reward not available yet"}), 400

        # Рассчитываем прибыль за 4 минуты (240 секунд)
        profit_per_second = total_generation
        period_profit = profit_per_second * 240
        reward = int(period_profit * 0.05)  # 5% от прибыли за 4 минуты
        
        # Обновляем баланс и время последнего получения награды
        new_balance = balance + reward
        cursor.execute("""
            UPDATE user_progress 
            SET balance = %s, last_reward_time = %s 
            WHERE user_id = %s
        """, (new_balance, current_time, user_id))
        
        connection.commit()
        
        print(f"User {user_id} claimed login reward: {reward} coins. New balance: {new_balance}")
        
        return jsonify({
            "status": "success",
            "reward": reward,
            "new_balance": new_balance
        }), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/spin_wheel', methods=['POST'])
def spin_wheel():
    data = request.json
    user_id = data.get('user_id')
    prize_index = data.get('prize_index')
    
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Начало транзакции и блокировка
        connection.start_transaction()
        cursor.execute("SELECT balance, total_generation FROM user_progress WHERE user_id = %s FOR UPDATE", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            connection.rollback()
            return jsonify({"status": "error", "message": "User not found"}), 404
            
        balance, total_generation = result
        spin_cost = 100
        
        if balance < spin_cost:
            connection.rollback()
            return jsonify({"status": "error", "message": "Недостаточно средств"}), 400

        new_balance = balance - spin_cost
        cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (new_balance, user_id))

        prizes = [
            "x3 токенов", 
            "1000 токенов", 
            "Drinking Water Dispenser", 
            "10000 токенов", 
            "100000 токенов", 
            "2000 токенов", 
            "Humanoid robot", 
            "x2 токенов"
        ]
        
        prize = prizes[prize_index]
        refund = False
        total_generation_update = 0  # Для накопления изменений total_generation

        if prize in ["Drinking Water Dispenser", "Humanoid robot"]:
            cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, prize))
            item_exists = cursor.fetchone()[0] > 0
            
            if item_exists:
                new_balance += spin_cost
                cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (new_balance, user_id))
                refund = True
            else:
                generation_per_hour = 10 if prize == "Drinking Water Dispenser" else 20
                cursor.execute("""
                    INSERT INTO inventory (user_id, item_name, generation_per_hour)
                    VALUES (%s, %s, %s)
                """, (user_id, prize, generation_per_hour))
                total_generation_update = generation_per_hour  # Фиксируем добавление генерации
        else:
            if prize in ["1000 токенов", "2000 токенов", "10000 токенов", "100000 токенов"]:
                prize_amount = int(prize.split()[0])
                new_balance += prize_amount
            elif prize.startswith("x"):
                multiplier = int(prize[1])
                new_balance = new_balance * multiplier
            
            cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (new_balance, user_id))

        # Обновляем total_generation, если был выигран предмет
        if total_generation_update > 0:
            cursor.execute("""
                UPDATE user_progress 
                SET total_generation = total_generation + %s 
                WHERE user_id = %s
            """, (total_generation_update, user_id))

        connection.commit()
        
        return jsonify({
            "status": "success",
            "prize": prize,
            "prize_index": prize_index,
            "new_balance": int(new_balance),
            "refund": refund
        }), 200

    except mysql.connector.Error as err:
        connection.rollback()
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/get_referral_link', methods=['GET'])
def get_referral_link():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is missing"}), 400
    
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # Проверяем, есть ли неиспользованный реферальный код
        cursor.execute("""
            SELECT referral_code 
            FROM referrals 
            WHERE user_id = %s AND used_by IS NULL 
            LIMIT 1
        """, (user_id,))
        result = cursor.fetchone()
        
        if result:
            referral_code = result[0]
        else:
            # Генерируем новый код
            import uuid
            referral_code = str(uuid.uuid4())[:8]
            cursor.execute("""
                INSERT INTO referrals (user_id, referral_code, created_at)
                VALUES (%s, %s, %s)
            """, (user_id, referral_code, datetime.now()))
            connection.commit()
        
        referral_link = f"https://t.me/CTSimulatorBot?start={referral_code}"
        return jsonify({"status": "success", "referral_link": referral_link}), 200
        
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/play_game', methods=['POST'])
def play_game():
    data = request.json
    user_id = data.get('user_id')
    bet = data.get('bet')
    selected_cell = data.get('selected_cell')

    # Валидация данных
    if not user_id:
        return jsonify({"status": "error", "message": "Не указан пользователь"}), 400
        
    if not isinstance(bet, int) or bet <= 0:
        return jsonify({"status": "error", "message": "Некорректная ставка"}), 400

    if not isinstance(selected_cell, int) or selected_cell < 0 or selected_cell > 7:
        return jsonify({"status": "error", "message": "Некорректный выбор блока"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Начало транзакции
        connection.start_transaction()

        # Блокировка строки для атомарного обновления
        cursor.execute("""
            SELECT balance 
            FROM user_progress 
            WHERE user_id = %s 
            FOR UPDATE
        """, (user_id,))
        result = cursor.fetchone()

        if not result:
            connection.rollback()
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        balance = result[0]

        if balance < bet:
            connection.rollback()
            return jsonify({"status": "error", "message": "Недостаточно средств"}), 400

        # Логика игры
        winning_cell = random.randint(0, 7)
        is_win = selected_cell == winning_cell
        new_balance = balance + (bet if is_win else -bet)

        # Обновление баланса
        cursor.execute("""
            UPDATE user_progress 
            SET balance = %s 
            WHERE user_id = %s
        """, (new_balance, user_id))

        # Фиксация транзакции
        connection.commit()

        return jsonify({
            "status": "success",
            "new_balance": new_balance,
            "result": "win" if is_win else "lose",
            "winning_cell": winning_cell
        }), 200

    except mysql.connector.Error as err:
        connection.rollback()
        app.logger.error(f"Database error: {err}")
        return jsonify({"status": "error", "message": "Ошибка базы данных"}), 500
    except Exception as e:
        connection.rollback()
        app.logger.error(f"Game error: {e}")
        return jsonify({"status": "error", "message": "Внутренняя ошибка сервера"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)