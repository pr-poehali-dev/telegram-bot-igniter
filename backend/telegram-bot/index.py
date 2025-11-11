"""
Business: Telegram bot webhook handler для системы огоньков
Args: event - dict с httpMethod, body, headers
      context - object с request_id
Returns: HTTP response dict
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

def send_telegram_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None):
    import urllib.request
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        return None
    
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.request.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Telegram API Error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"Error sending message: {type(e).__name__}: {e}")
        return None

def get_or_create_user(conn, telegram_user: Dict) -> int:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (telegram_id) 
            DO UPDATE SET 
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                updated_at = CURRENT_TIMESTAMP
            RETURNING telegram_id
            """,
            (
                telegram_user.get('id'),
                telegram_user.get('username'),
                telegram_user.get('first_name'),
                telegram_user.get('last_name')
            )
        )
        conn.commit()
        return cur.fetchone()['telegram_id']

def handle_start(conn, user_id: int, chat_id: int):
    keyboard = {
        'keyboard': [
            [{'text': '🔥 Мои огоньки'}, {'text': '➕ Пригласить друга'}],
            [{'text': '👤 Профиль'}, {'text': '⚙️ Настройки'}]
        ],
        'resize_keyboard': True
    }
    
    welcome_text = (
        "🔥 <b>Добро пожаловать в Огоньки!</b>\n\n"
        "Поддерживай общение с друзьями каждый день и собирай серии огоньков!\n\n"
        "💡 <b>Как это работает:</b>\n"
        "• Отправь сообщение другу = +1 день к серии\n"
        "• Пропустил день = огонёк тухнет 😔\n"
        "• Есть 3 защиты в месяц для восстановления\n\n"
        "Начни с приглашения друга! 👇"
    )
    
    send_telegram_message(chat_id, welcome_text, keyboard)

def handle_my_streaks(conn, user_id: int, chat_id: int):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT 
                s.id, s.streak_count, s.last_message_date, s.status,
                CASE 
                    WHEN s.user1_id = %s THEN u2.username
                    ELSE u1.username
                END as friend_username,
                CASE 
                    WHEN s.user1_id = %s THEN s.user2_id
                    ELSE s.user1_id
                END as friend_id,
                (SELECT COUNT(*) FROM messages m 
                 WHERE m.streak_id = s.id 
                 AND m.to_user_id = %s 
                 AND m.is_read = FALSE) as unread_count
            FROM streaks s
            JOIN users u1 ON s.user1_id = u1.telegram_id
            JOIN users u2 ON s.user2_id = u2.telegram_id
            WHERE (s.user1_id = %s OR s.user2_id = %s)
            AND s.status = 'active'
            ORDER BY s.streak_count DESC
            """,
            (user_id, user_id, user_id, user_id, user_id)
        )
        streaks = cur.fetchall()
    
    if not streaks:
        text = (
            "🔍 <b>У тебя пока нет активных огоньков</b>\n\n"
            "Пригласи друга и начните серию! ➕"
        )
    else:
        text = "🔥 <b>Твои огоньки:</b>\n\n"
        
        for streak in streaks:
            fire_emoji = '🔥' if streak['streak_count'] > 0 else '💨'
            unread = '🔴' if streak['unread_count'] > 0 else ''
            crown = '👑' if streak['streak_count'] >= 30 else ''
            
            text += (
                f"{fire_emoji} <b>@{streak['friend_username']}</b> {crown} {unread}\n"
                f"   └ Серия: <b>{streak['streak_count']}</b> дней\n"
                f"   └ Последнее сообщение: {streak['last_message_date'] or 'никогда'}\n\n"
            )
    
    send_telegram_message(chat_id, text)

def handle_invite_friend(conn, user_id: int, chat_id: int):
    text = (
        "➕ <b>Пригласить друга</b>\n\n"
        "Отправь username друга в формате:\n"
        "<code>@username</code>\n\n"
        "Если друг не зарегистрирован в боте, "
        "мы отправим ему приглашение!"
    )
    
    send_telegram_message(chat_id, text)

def handle_username_invite(conn, user_id: int, chat_id: int, username: str):
    username = username.lstrip('@').lower()
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT telegram_id FROM users WHERE LOWER(username) = %s",
            (username,)
        )
        friend = cur.fetchone()
    
    if not friend:
        text = (
            f"❌ <b>Пользователь @{username} не найден</b>\n\n"
            "Убедись, что друг уже запустил бота!"
        )
        send_telegram_message(chat_id, text)
        return
    
    friend_id = friend['telegram_id']
    
    if friend_id == user_id:
        send_telegram_message(chat_id, "😅 Нельзя пригласить самого себя!")
        return
    
    user1_id = min(user_id, friend_id)
    user2_id = max(user_id, friend_id)
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, status FROM streaks 
            WHERE user1_id = %s AND user2_id = %s
            """,
            (user1_id, user2_id)
        )
        existing = cur.fetchone()
    
    if existing:
        if existing['status'] == 'active':
            text = f"🔥 Огонёк с @{username} уже активен!"
        else:
            text = f"⏳ Запрос к @{username} уже отправлен!"
        send_telegram_message(chat_id, text)
        return
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO streaks (user1_id, user2_id, status)
            VALUES (%s, %s, 'pending')
            RETURNING id
            """,
            (user1_id, user2_id)
        )
        conn.commit()
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT username FROM users WHERE telegram_id = %s",
            (user_id,)
        )
        requester = cur.fetchone()
    
    requester_username = requester['username'] or 'Пользователь'
    
    friend_text = (
        f"🔔 <b>Новый запрос!</b>\n\n"
        f"@{requester_username} хочет начать огонёк с тобой!\n\n"
        "Отправь /accept чтобы принять"
    )
    send_telegram_message(friend_id, friend_text)
    
    text = f"✅ Запрос отправлен @{username}!"
    send_telegram_message(chat_id, text)

def handle_accept(conn, user_id: int, chat_id: int):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            UPDATE streaks
            SET status = 'active', updated_at = CURRENT_TIMESTAMP
            WHERE (user1_id = %s OR user2_id = %s)
            AND status = 'pending'
            RETURNING user1_id, user2_id
            """,
            (user_id, user_id)
        )
        updated = cur.fetchone()
        conn.commit()
    
    if not updated:
        text = "❌ Нет ожидающих запросов"
        send_telegram_message(chat_id, text)
        return
    
    friend_id = updated['user1_id'] if updated['user1_id'] != user_id else updated['user2_id']
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT username FROM users WHERE telegram_id = %s",
            (friend_id,)
        )
        friend = cur.fetchone()
    
    friend_username = friend['username'] or 'друг'
    
    text = f"🔥 Огонёк с @{friend_username} начат! Начинайте общаться!"
    send_telegram_message(chat_id, text)
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT username FROM users WHERE telegram_id = %s",
            (user_id,)
        )
        user = cur.fetchone()
    
    user_username = user['username'] or 'друг'
    friend_text = f"🔥 @{user_username} принял запрос! Огонёк начат!"
    send_telegram_message(friend_id, friend_text)

def handle_profile(conn, user_id: int, chat_id: int):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT username, first_name FROM users WHERE telegram_id = %s
            """,
            (user_id,)
        )
        user = cur.fetchone()
        
        cur.execute(
            """
            SELECT COUNT(*) as total_streaks,
                   COALESCE(SUM(streak_count), 0) as total_days,
                   COALESCE(MAX(streak_count), 0) as longest_streak
            FROM streaks
            WHERE (user1_id = %s OR user2_id = %s)
            AND status = 'active'
            """,
            (user_id, user_id)
        )
        stats = cur.fetchone()
    
    username = user['username'] or user['first_name'] or 'Пользователь'
    
    text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"📛 @{username}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Активных огоньков: {stats['total_streaks']}\n"
        f"• Всего дней: {stats['total_days']}\n"
        f"• Лучшая серия: {stats['longest_streak']} 🏆\n"
    )
    
    send_telegram_message(chat_id, text)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        
        if 'message' not in body:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True})
            }
        
        message = body['message']
        user = message.get('from', {})
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        conn = get_db_connection()
        
        try:
            user_id = get_or_create_user(conn, user)
            
            if text == '/start':
                handle_start(conn, user_id, chat_id)
            elif text == '/accept':
                handle_accept(conn, user_id, chat_id)
            elif text in ['🔥 Мои огоньки', '/streaks']:
                handle_my_streaks(conn, user_id, chat_id)
            elif text in ['➕ Пригласить друга', '/invite']:
                handle_invite_friend(conn, user_id, chat_id)
            elif text in ['👤 Профиль', '/profile']:
                handle_profile(conn, user_id, chat_id)
            elif text.startswith('@'):
                handle_username_invite(conn, user_id, chat_id, text)
            else:
                send_telegram_message(
                    chat_id,
                    "Используй меню или команды:\n"
                    "/start - Главное меню\n"
                    "/streaks - Мои огоньки\n"
                    "/invite - Пригласить друга\n"
                    "/profile - Профиль"
                )
        
        finally:
            conn.close()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True})
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }