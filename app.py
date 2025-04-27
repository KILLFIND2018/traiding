from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import threading
import time
import random
from config import MYSQL_CONFIG

import logging

# Отключаем логи запросов
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app, resources={r"/static/*": {"origins": "*"}})

user_heartbeats = {}

def calculate_balance(current_balance, last_updated, total_generation):
    now = datetime.now()
    seconds_elapsed = (now - last_updated).total_seconds()
    hours_elapsed = seconds_elapsed / 3600  # Конвертируем секунды в часы
    
    # Рассчитываем новый баланс на основе почасовой генерации
    new_balance = current_balance + (total_generation * hours_elapsed)
    
    # Округляем до целого, так как баланс BIGINT
    return int(new_balance)

def generation_loop(user_id):
    while True:
        try:
            connection = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = connection.cursor()

            cursor.execute("SELECT is_active, balance, total_generation, last_updated FROM user_progress WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()

            if not result or result[0] == 0:
                print(f"Генерация для user_id {user_id} остановлена: is_active = 0")
                break

            if user_id in user_heartbeats:
                last_heartbeat = user_heartbeats[user_id]
                if (datetime.now() - last_heartbeat).total_seconds() > 10:
                    cursor.execute("UPDATE user_progress SET is_active = 0 WHERE user_id = %s", (user_id,))
                    connection.commit()
                    print(f"Генерация для user_id {user_id} остановлена: нет heartbeat более 10 секунд")
                    break

            balance, total_generation, last_updated = result[1:]
            total_generation = total_generation or 0  # Почасовая ставка
            last_updated = last_updated or datetime.now()

            new_balance = calculate_balance(balance, last_updated, total_generation)

            cursor.execute("""
                UPDATE user_progress 
                SET balance = %s, last_updated = %s 
                WHERE user_id = %s
            """, (new_balance, datetime.now(), user_id))
            connection.commit()
            print(f"Генерация для user_id {user_id}: баланс = {new_balance}, генерация = {total_generation} (в час)")

            time.sleep(5)  # Обновление каждые 5 секунд
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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400
    
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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

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
            return jsonify({"status": "error", "message": "Пользователь не найден, начните через Telegram-бота"}), 404

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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("UPDATE user_progress SET is_active = 0 WHERE user_id = %s", (user_id,))
        connection.commit()
        print(f"Генерация для user_id {user_id} остановлена по запросу")
        if user_id in user_heartbeats:
            del user_heartbeats[user_id]
        return jsonify({"status": "success", "message": "Генерация остановлена"}), 200

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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT balance, total_generation, last_updated, is_active FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            balance, total_generation, last_updated, is_active = result
            total_generation = total_generation or 0

            if is_active:
                new_balance = calculate_balance(balance, last_updated or datetime.now(), total_generation)
                cursor.execute("""
                    UPDATE user_progress 
                    SET balance = %s, last_updated = %s 
                    WHERE user_id = %s
                """, (new_balance, datetime.now(), user_id))
                connection.commit()
                balance = new_balance

            return jsonify({"status": "success", "balance": balance}), 200
        else:
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

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
    item_generation = data.get('item_generation')  # Это generation_per_hour

    if not all([user_id, item_name, item_cost, item_generation]):
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        # Проверяем наличие предмета в инвентаре
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        if cursor.fetchone()[0] > 0:
            return jsonify({
                "status": "error", 
                "message": f"⚠️ {item_name} already in your inventory!"
            }), 400

        # Получаем прогресс пользователя
        cursor.execute("SELECT balance, total_generation, last_updated FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        balance, total_generation, last_updated = result
        total_generation = total_generation or 0
        last_updated = last_updated or datetime.now()

        # Рассчитываем баланс
        new_balance = calculate_balance(balance, last_updated, total_generation)

        # Проверяем наличие средств
        if new_balance < item_cost:
            return jsonify({
                "status": "error", 
                "message": "Insufficient funds!"
            }), 400

        # Обновляем баланс и генерацию
        new_balance -= item_cost
        new_total_generation = total_generation + item_generation  # Добавляем почасовую генерацию

        cursor.execute("""
            UPDATE user_progress 
            SET balance = %s, total_generation = %s, last_updated = %s 
            WHERE user_id = %s
        """, (new_balance, new_total_generation, datetime.now(), user_id))

        # Добавляем предмет в инвентарь
        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, generation_per_hour) 
            VALUES (%s, %s, %s)
        """, (user_id, item_name, int(item_generation)))

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

        # Добавляем путь к изображению
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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

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

        cursor.execute("""
            SELECT username, balance 
            FROM user_progress 
            ORDER BY balance DESC
        """)
        users = cursor.fetchall()

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
    amount = data.get('amount')
    stars_cost = data.get('stars_cost')

    if not all([user_id, amount, stars_cost]):
        return jsonify({"status": "error", "message": "Отсутствуют обязательные поля"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT balance, total_generation, last_updated FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        balance, total_generation, last_updated = result
        total_generation = total_generation or 0
        last_updated = last_updated or datetime.now()

        new_balance = calculate_balance(balance, last_updated, total_generation)
        new_balance += amount

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

        cursor.execute("SELECT generation_per_hour FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        inventory_item = cursor.fetchone()
        if not inventory_item:
            return jsonify({"status": "error", "message": "Предмет не найден в инвентаре"}), 400

        generation_per_hour = inventory_item[0]

        cursor.execute("""
            UPDATE user_progress 
            SET total_generation = total_generation - %s 
            WHERE user_id = %s
        """, (generation_per_hour, user_id))

        cursor.execute("""
            INSERT INTO auction_lots (seller_id, item_name, description, start_price)
            VALUES (%s, %s, %s, %s)
        """, (user_id, item_name, description, start_price))

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

        cursor.execute("SELECT start_price, current_bid, seller_id FROM auction_lots WHERE lot_id = %s AND is_active = 1", (lot_id,))
        lot = cursor.fetchone()
        if not lot:
            return jsonify({"status": "error", "message": "Лот не найден или неактивен"}), 404

        start_price, current_bid, seller_id = lot
        if user_id == seller_id:
            return jsonify({"status": "error", "message": "Нельзя ставить на свой лот"}), 400

        min_bid = current_bid or start_price
        if bid_amount <= min_bid:
            return jsonify({"status": "error", "message": "Ставка должна быть выше текущей"}), 400

        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (user_id,))
        balance = cursor.fetchone()[0]
        if balance < bid_amount:
            return jsonify({"status": "error", "message": "Insufficient funds"}), 400

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
            return jsonify({"status": "error", "message": "Только продавец может завершить лот"}), 403

        if not current_bidder_id:
            return jsonify({"status": "error", "message": "Нет ставок"}), 400

        cursor.execute("SELECT generation_per_hour FROM inventory WHERE user_id = %s AND item_name = %s", (seller_id, item_name))
        inventory_item = cursor.fetchone()
        generation_per_hour = inventory_item[0] if inventory_item else 0

        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (current_bidder_id,))
        buyer_balance = cursor.fetchone()[0]
        if buyer_balance < current_bid:
            return jsonify({"status": "error", "message": "У покупателя недостаточно средств"}), 400

        cursor.execute("UPDATE user_progress SET balance = balance - %s WHERE user_id = %s", (current_bid, current_bidder_id))
        cursor.execute("UPDATE user_progress SET balance = balance + %s WHERE user_id = %s", (current_bid, seller_id))
        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, generation_per_hour)
            VALUES (%s, %s, %s)
        """, (current_bidder_id, item_name, generation_per_hour))
        cursor.execute("""
            UPDATE user_progress 
            SET total_generation = total_generation + %s 
            WHERE user_id = %s
        """, (generation_per_hour, current_bidder_id))
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
        connection.autocommit = False

        cursor = connection.cursor()

        cursor.execute("SELECT bet_time FROM bitcoin_bets WHERE user_id = %s ORDER BY bet_time DESC LIMIT 1", (user_id,))
        last_bet = cursor.fetchone()
        cursor.fetchall()

        if last_bet:
            last_bet_time = last_bet[0]
            cooldown = 14400
            if (datetime.now() - last_bet_time).total_seconds() < cooldown:
                return jsonify({"status": "error", "message": "Ставка доступна раз в 4 часа"}), 400

        cursor.execute(
            "SELECT balance, total_generation, last_updated FROM user_progress WHERE user_id = %s FOR UPDATE", 
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.fetchall()

        if not result:
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        balance, total_generation, last_updated = result
        current_balance = calculate_balance(
            balance, 
            last_updated or datetime.now(), 
            total_generation or 0
        )

        if current_balance < bet_amount:
            return jsonify({"status": "error", "message": "Insufficient funds"}), 400

        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd',
                timeout=5
            )
            btc_price = response.json()['bitcoin']['usd']
        except Exception as e:
            connection.rollback()
            return jsonify({"status": "error", "message": f"Ошибка получения цены BTC: {str(e)}"}), 500

        cursor.execute(
            "UPDATE user_progress SET balance = %s, last_updated = %s WHERE user_id = %s",
            (current_balance - bet_amount, datetime.now(), user_id)
        )

        cursor.execute(
            """INSERT INTO bitcoin_bets 
            (user_id, bet_amount, bet_direction, bet_time, bet_price)
            VALUES (%s, %s, %s, %s, %s)""",
            (user_id, bet_amount, bet_direction, datetime.now(), btc_price)
        )

        connection.commit()

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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT bet_amount, bet_direction, bet_time, bet_price, resolved FROM bitcoin_bets WHERE user_id = %s", (user_id,))
        bets = cursor.fetchall()

        if not bets or all(bet[4] for bet in bets):
            return jsonify({"status": "success", "message": "Нет активных ставок"}), 200

        for bet in bets:
            if not bet[4]:
                bet_amount, bet_direction, bet_time, bet_price = bet[0:4]
                break
        else:
            return jsonify({"status": "success", "message": "Нет активных ставок"}), 200

        if (datetime.now() - bet_time).total_seconds() < 14400:
            remaining = 14400 - (datetime.now() - bet_time).total_seconds()
            return jsonify({"status": "pending", "remaining": int(remaining)}), 200

        btc_price_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd').json()
        current_price = btc_price_response['bitcoin']['usd']

        won = (bet_direction == 'up' and current_price > bet_price) or (bet_direction == 'down' and current_price < bet_price)
        prize = bet_amount * 2 if won else 0

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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400
    
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
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
        return jsonify({"status": "error", "message": "Required fields are missing"}), 400
    
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("SELECT user_id FROM referrals WHERE referral_code = %s AND used_by IS NULL", (referral_code,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"status": "error", "message": "Неверный или использованный код"}), 400
            
        referrer_id = result[0]
        
        if referrer_id == user_id:
            return jsonify({"status": "error", "message": "Нельзя использовать свой код"}), 400
            
        cursor.execute("SELECT COUNT(*) FROM referrals WHERE used_by = %s", (user_id,))
        if cursor.fetchone()[0] > 0:
            return jsonify({"status": "error", "message": "You have already used the referral code"}), 400
            
        cursor.execute("""
            UPDATE referrals 
            SET used_by = %s, used_at = %s 
            WHERE referral_code = %s
        """, (user_id, datetime.now(), referral_code))
        
        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, generation_per_hour)
            VALUES (%s, %s, %s)
        """, (referrer_id, "Macbook", 150))
        
        cursor.execute("""
            UPDATE user_progress 
            SET total_generation = total_generation + %s 
            WHERE user_id = %s
        """, (150, referrer_id))
        
        connection.commit()
        return jsonify({"status": "success", "message": "Реферальный код успешно использован"}), 200
        
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/get_new_rewards', methods=['GET'])
def get_new_rewards():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, item_name, awarded_at 
            FROM rewards 
            WHERE user_id = %s AND alert_shown = FALSE
        """, (user_id,))
        rewards = cursor.fetchall()

        if rewards:
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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

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
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        last_reward_time, total_generation, balance, last_updated = result
        total_generation = total_generation or 0
        last_updated = last_updated or datetime.now()

        current_time = datetime.now()
        reward_interval = 14400

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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

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
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        last_reward_time, total_generation, balance, last_updated = result
        total_generation = total_generation or 0
        last_updated = last_updated or datetime.now()

        current_time = datetime.now()
        reward_interval = 14400

        if last_reward_time and (current_time - last_reward_time).total_seconds() < reward_interval:
            return jsonify({"status": "error", "message": "Награда пока недоступна"}), 400

        profit_per_hour = total_generation
        period_profit = profit_per_hour * 4
        reward = int(period_profit * 0.05)
        
        new_balance = balance + reward
        cursor.execute("""
            UPDATE user_progress 
            SET balance = %s, last_reward_time = %s 
            WHERE user_id = %s
        """, (new_balance, current_time, user_id))
        
        connection.commit()
        
        print(f"Пользователь {user_id} получил награду за вход: {reward} монет. Новый баланс: {new_balance}")
        
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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        connection.start_transaction()
        cursor.execute("SELECT balance, total_generation, last_updated FROM user_progress WHERE user_id = %s FOR UPDATE", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            connection.rollback()
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404
            
        balance, total_generation, last_updated = result
        total_generation = total_generation or 0
        spin_cost = 100
        
        new_balance = calculate_balance(balance, last_updated or datetime.now(), total_generation)
        
        if new_balance < spin_cost:
            connection.rollback()
            return jsonify({"status": "error", "message": "Insufficient funds"}), 400

        new_balance -= spin_cost
        cursor.execute("UPDATE user_progress SET balance = %s, last_updated = %s WHERE user_id = %s", (new_balance, datetime.now(), user_id))

        prizes = [
            "x3 tokens", 
            "1000 tokens", 
            "Drinking Water Dispenser", 
            "10000 tokens", 
            "100000 tokens", 
            "2000 tokens", 
            "Humanoid robot", 
            "x2 tokens"
        ]
        
        prize = prizes[prize_index]
        refund = False
        total_generation_update = 0

        if prize in ["Drinking Water Dispenser", "Humanoid robot"]:
            cursor.execute("SELECT generation_per_hour FROM market_items WHERE name = %s", (prize,))
            generation_result = cursor.fetchone()
            if not generation_result:
                connection.rollback()
                return jsonify({"status": "error", "message": "Предмет не найден в магазине"}), 404
                
            generation_per_hour = generation_result[0]

            cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = %s AND item_name = %s", (user_id, prize))
            item_exists = cursor.fetchone()[0] > 0
            
            if item_exists:
                new_balance += spin_cost
                cursor.execute("UPDATE user_progress SET balance = %s, last_updated = %s WHERE user_id = %s", (new_balance, datetime.now(), user_id))
                refund = True
            else:
                cursor.execute("""
                    INSERT INTO inventory (user_id, item_name, generation_per_hour)
                    VALUES (%s, %s, %s)
                """, (user_id, prize, generation_per_hour))
                total_generation_update = generation_per_hour

        else:
            if prize in ["1000 токенов", "2000 токенов", "10000 токенов", "100000 токенов"]:
                prize_amount = int(prize.split()[0].replace('x', ''))
                new_balance += prize_amount
            elif prize.startswith("x"):
                multiplier = int(prize[1])
                new_balance = new_balance * multiplier
            
            cursor.execute("UPDATE user_progress SET balance = %s, last_updated = %s WHERE user_id = %s", (new_balance, datetime.now(), user_id))

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
        return jsonify({"status": "error", "message": "User ID отсутствует"}), 400
    
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
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
            import uuid
            referral_code = str(uuid.uuid4())[:8]
            cursor.execute("""
                INSERT INTO referrals (user_id, referral_code, created_at)
                VALUES (%s, %s, %s)
            """, (user_id, referral_code, datetime.now()))
            connection.commit()
        
        referral_link = f"https://t.me/tycoonsimulatorbot?start={referral_code}"
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

    if not user_id:
        return jsonify({"status": "error", "message": "Не указан пользователь"}), 400
        
    if not isinstance(bet, int) or bet <= 0:
        return jsonify({"status": "error", "message": "Некорректная ставка"}), 400

    if not isinstance(selected_cell, int) or selected_cell < 0 or selected_cell > 7:
        return jsonify({"status": "error", "message": "Некорректный выбор блока"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        connection.start_transaction()

        cursor.execute("""
            SELECT balance, total_generation, last_updated 
            FROM user_progress 
            WHERE user_id = %s 
            FOR UPDATE
        """, (user_id,))
        result = cursor.fetchone()

        if not result:
            connection.rollback()
            return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

        balance, total_generation, last_updated = result
        total_generation = total_generation or 0

        balance = calculate_balance(balance, last_updated or datetime.now(), total_generation)

        if balance < bet:
            connection.rollback()
            return jsonify({"status": "error", "message": "Insufficient funds"}), 400

        winning_cell = random.randint(0, 7)
        is_win = selected_cell == winning_cell
        new_balance = balance + (bet if is_win else -bet)

        cursor.execute("""
            UPDATE user_progress 
            SET balance = %s, last_updated = %s 
            WHERE user_id = %s
        """, (new_balance, datetime.now(), user_id))

        connection.commit()

        return jsonify({
            "status": "success",
            "new_balance": new_balance,
            "result": "win" if is_win else "lose",
            "winning_cell": winning_cell
        }), 200

    except mysql.connector.Error as err:
        connection.rollback()
        app.logger.error(f"Ошибка базы данных: {err}")
        return jsonify({"status": "error", "message": "Ошибка базы данных"}), 500
    except Exception as e:
        connection.rollback()
        app.logger.error(f"Ошибка игры: {e}")
        return jsonify({"status": "error", "message": "Внутренняя ошибка сервера"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
@app.route('/reward_user', methods=['POST'])
def reward_user():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')

    if not all([user_id, amount]):
        return jsonify({"status": "error", "message": "Required fields are missing"}), 400

    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT balance FROM user_progress WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "error", "message": "User not found"}), 404

        balance = result[0]
        new_balance = balance + amount

        cursor.execute("UPDATE user_progress SET balance = %s WHERE user_id = %s", (new_balance, user_id))
        connection.commit()

        return jsonify({"status": "success", "new_balance": new_balance}), 200

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        cursor.close()
        connection.close()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)