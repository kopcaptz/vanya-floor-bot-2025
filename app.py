import os
import logging
from flask import Flask, request, jsonify
import telebot
from bot_handlers import BotHandlers
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Настраиваем обработчики
bot_handlers = BotHandlers(bot)

@app.route('/')
def index():
    """Главная страница"""
    return jsonify({
        'status': 'running',
        'bot_name': 'Vanya Floor Analyzer Bot',
        'version': '1.0',
        'description': 'Telegram bot for analyzing floor images and calculating repair costs'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook для получения обновлений от Telegram"""
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health_check():
    """Проверка здоровья приложения"""
    try:
        # Проверяем подключение к Telegram API
        bot_info = bot.get_me()
        return jsonify({
            'status': 'healthy',
            'bot_username': bot_info.username,
            'bot_id': bot_info.id
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Устанавливает webhook для бота"""
    try:
        webhook_url = request.json.get('url')
        if not webhook_url:
            return jsonify({'error': 'URL is required'}), 400
        
        result = bot.set_webhook(url=webhook_url)
        if result:
            return jsonify({'status': 'webhook set successfully', 'url': webhook_url})
        else:
            return jsonify({'error': 'Failed to set webhook'}), 500
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/remove_webhook', methods=['POST'])
def remove_webhook():
    """Удаляет webhook"""
    try:
        result = bot.remove_webhook()
        if result:
            return jsonify({'status': 'webhook removed successfully'})
        else:
            return jsonify({'error': 'Failed to remove webhook'}), 500
    except Exception as e:
        logger.error(f"Error removing webhook: {e}")
        return jsonify({'error': str(e)}), 500

def run_polling():
    """Запускает бота в режиме polling (для локального тестирования)"""
    logger.info("Starting bot in polling mode...")
    try:
        # Удаляем webhook если он был установлен
        bot.remove_webhook()
        
        # Запускаем polling
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        logger.error(f"Error in polling mode: {e}")

if __name__ == '__main__':
    # Проверяем переменные окружения
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Если запускаем локально, используем polling
    if os.environ.get('WEBHOOK_MODE') != 'true':
        logger.info("Running in local polling mode")
        run_polling()
    else:
        # Запускаем Flask сервер для webhook
        logger.info(f"Starting Flask server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=debug)

