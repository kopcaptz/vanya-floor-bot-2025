#!/usr/bin/env python3
"""
Telegram бот для автоматизации оценки полов - версия для Heroku
Поддерживает webhook для постоянной работы
"""

import os
import logging
from flask import Flask, request, jsonify
import telebot
from bot_handlers import BotHandlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '8346136918:AAHwREKIctQJSuWWBySju7naWT_FiDdJBwo')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
PORT = int(os.getenv('PORT', 5000))

# Создание Flask приложения
app = Flask(__name__)

# Создание бота
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация обработчиков
try:
    bot_handlers = BotHandlers(bot)
    logger.info("Bot handlers initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot handlers: {e}")
    bot_handlers = None

@app.route('/')
def index():
    """Главная страница для проверки работы"""
    return jsonify({
        'status': 'running',
        'bot': 'Vanya Floor Analyzer Bot',
        'version': '1.0',
        'handlers': 'initialized' if bot_handlers else 'failed'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик webhook от Telegram"""
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return jsonify({'status': 'ok'})
        else:
            logger.warning('Invalid content type for webhook')
            return jsonify({'error': 'Invalid content type'}), 400
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/set_webhook')
def set_webhook():
    """Установка webhook (для отладки)"""
    try:
        webhook_url = request.args.get('url', WEBHOOK_URL)
        if not webhook_url:
            return jsonify({'error': 'No webhook URL provided'}), 400
        
        result = bot.set_webhook(url=webhook_url)
        if result:
            return jsonify({'status': 'webhook set', 'url': webhook_url})
        else:
            return jsonify({'error': 'Failed to set webhook'}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook_info')
def webhook_info():
    """Информация о webhook"""
    try:
        info = bot.get_webhook_info()
        return jsonify({
            'url': info.url,
            'has_custom_certificate': info.has_custom_certificate,
            'pending_update_count': info.pending_update_count,
            'last_error_date': info.last_error_date,
            'last_error_message': info.last_error_message,
            'max_connections': info.max_connections,
            'allowed_updates': info.allowed_updates
        })
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Проверка здоровья приложения"""
    try:
        # Проверяем доступность Telegram API
        me = bot.get_me()
        
        return jsonify({
            'status': 'healthy',
            'bot_info': {
                'id': me.id,
                'username': me.username,
                'first_name': me.first_name
            },
            'handlers': 'ok' if bot_handlers else 'error'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

def setup_webhook():
    """Настройка webhook при запуске"""
    if WEBHOOK_URL:
        try:
            # Удаляем старый webhook
            bot.remove_webhook()
            
            # Устанавливаем новый webhook
            result = bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
            if result:
                logger.info(f"Webhook set successfully: {WEBHOOK_URL}/webhook")
            else:
                logger.error("Failed to set webhook")
        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
    else:
        logger.warning("No WEBHOOK_URL provided, webhook not set")

if __name__ == '__main__':
    logger.info("Starting Vanya Floor Bot for Heroku...")
    
    # Настройка webhook
    setup_webhook()
    
    # Запуск Flask приложения
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False
    )

