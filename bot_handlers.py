import telebot
from telebot import types
import os
import tempfile
import logging
from typing import Dict

from whatsapp_parser import WhatsAppParser
from ai_analyzer import FloorAnalyzer
from pricing_calculator import PricingCalculator
from report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot
        self.whatsapp_parser = WhatsAppParser()
        self.floor_analyzer = FloorAnalyzer()
        self.pricing_calculator = PricingCalculator()
        self.report_generator = ReportGenerator()
        
        # Временное хранилище для данных пользователей
        self.user_data = {}
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настраивает все обработчики бота"""
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            self.handle_start(message)
        
        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            self.handle_help(message)
        
        @self.bot.message_handler(content_types=['document'])
        def handle_document(message):
            self.handle_zip_file(message)
        
        @self.bot.message_handler(content_types=['photo'])
        def handle_photo(message):
            self.handle_single_photo(message)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callbacks(call):
            self.handle_callback_query(call)
    
    def handle_start(self, message):
        """Обрабатывает команду /start"""
        welcome_text = """🏠 **Добро пожаловать в бот Ивана!**

Я помогаю анализировать полы и рассчитывать стоимость ремонта.

📋 **Что я умею:**
• Анализировать фотографии полов
• Определять тип покрытия и повреждения
• Рассчитывать стоимость работ
• Создавать отчеты для клиентов

📁 **Как пользоваться:**
1. Отправьте ZIP архив с экспортом WhatsApp чата
2. Или отправьте отдельные фотографии полов
3. Получите детальный анализ и стоимость

📞 **Контакты Ивана:**
Телефон: +972 52-477-2115
Специализация: Ремонт полов и паркета

Отправьте ZIP файл или фотографии для начала анализа! 📸"""

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📋 Помощь", callback_data="help"),
            types.InlineKeyboardButton("📞 Контакты", callback_data="contacts")
        )
        
        self.bot.send_message(
            message.chat.id, 
            welcome_text, 
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    def handle_help(self, message):
        """Обрабатывает команду /help"""
        help_text = """🔧 **ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ**

📁 **Анализ WhatsApp чата:**
1. Откройте чат с клиентом в WhatsApp
2. Нажмите на имя контакта → "Экспорт чата"
3. Выберите "Включить медиафайлы"
4. Отправьте полученный ZIP файл в этот бот

📸 **Анализ отдельных фото:**
1. Отправьте фотографии полов по одной
2. Добавьте описание проблемы (опционально)
3. Получите анализ каждого изображения

📊 **Что вы получите:**
• Тип напольного покрытия
• Оценка состояния и повреждений
• Рекомендации по ремонту
• Расчет стоимости работ
• Готовый ответ для клиента

⚠️ **Ограничения:**
• Максимальный размер ZIP: 50MB
• Поддерживаемые форматы: JPG, PNG, WebP
• Максимальное качество анализа при хорошем освещении

📋 **Команды:**
/start - Начать работу
/help - Эта справка

❓ **Вопросы?** Обращайтесь к Ивану: +972 52-477-2115"""

        self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    
    def handle_zip_file(self, message):
        """Обрабатывает ZIP файл с экспортом WhatsApp"""
        try:
            # Проверяем что это ZIP файл
            if not message.document.file_name.endswith('.zip'):
                self.bot.send_message(
                    message.chat.id,
                    "❌ Поддерживаются только ZIP архивы с экспортами WhatsApp"
                )
                return
            
            # Проверяем размер файла
            if message.document.file_size > 50 * 1024 * 1024:  # 50MB
                self.bot.send_message(
                    message.chat.id,
                    "❌ Файл слишком большой. Максимальный размер: 50MB"
                )
                return
            
            # Показываем что бот работает
            self.bot.send_chat_action(message.chat.id, 'typing')
            status_msg = self.bot.send_message(
                message.chat.id,
                "📦 Скачиваю и распаковываю архив..."
            )
            
            # Скачиваем файл
            file_info = self.bot.get_file(message.document.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Обновляем статус
            self.bot.edit_message_text(
                "🔍 Анализирую содержимое архива...",
                message.chat.id,
                status_msg.message_id
            )
            
            # Парсим WhatsApp экспорт
            parse_result = self.whatsapp_parser.process_whatsapp_export(downloaded_file)
            
            if not parse_result['success']:
                self.bot.edit_message_text(
                    f"❌ Ошибка при обработке архива: {parse_result.get('error', 'Неизвестная ошибка')}",
                    message.chat.id,
                    status_msg.message_id
                )
                return
            
            # Проверяем наличие изображений
            image_files = [f for f in parse_result['media_files'] if f['type'] == 'image']
            
            if not image_files:
                self.bot.edit_message_text(
                    "❌ В архиве не найдено изображений для анализа",
                    message.chat.id,
                    status_msg.message_id
                )
                return
            
            # Обновляем статус
            self.bot.edit_message_text(
                f"🔍 Найдено {len(image_files)} изображений. Анализирую...",
                message.chat.id,
                status_msg.message_id
            )
            
            # Анализируем изображения
            analysis_result = self.floor_analyzer.analyze_multiple_images(
                image_files, 
                parse_result['conversation_context']
            )
            
            if not analysis_result['success']:
                self.bot.edit_message_text(
                    f"❌ Ошибка при анализе изображений: {analysis_result.get('error', 'Неизвестная ошибка')}",
                    message.chat.id,
                    status_msg.message_id
                )
                return
            
            # Рассчитываем стоимость
            cost_info = self.pricing_calculator.calculate_project_cost(analysis_result)
            timeline = self.pricing_calculator.get_work_timeline(analysis_result, cost_info)
            
            # Удаляем статусное сообщение
            self.bot.delete_message(message.chat.id, status_msg.message_id)
            
            # Сохраняем данные для пользователя
            self.user_data[message.chat.id] = {
                'analysis': analysis_result,
                'cost_info': cost_info,
                'timeline': timeline,
                'client_info': parse_result['client_info'],
                'parse_result': parse_result
            }
            
            # Отправляем результаты
            self.send_analysis_results(message.chat.id)
            
        except Exception as e:
            logger.error(f"Error processing ZIP file: {e}")
            self.bot.send_message(
                message.chat.id,
                f"❌ Произошла ошибка при обработке файла: {str(e)}"
            )
    
    def handle_single_photo(self, message):
        """Обрабатывает отдельную фотографию"""
        try:
            self.bot.send_chat_action(message.chat.id, 'typing')
            status_msg = self.bot.send_message(
                message.chat.id,
                "🔍 Анализирую изображение..."
            )
            
            # Скачиваем фото
            file_info = self.bot.get_file(message.photo[-1].file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(downloaded_file)
                temp_file_path = temp_file.name
            
            try:
                # Анализируем изображение
                context = message.caption if message.caption else ""
                analysis = self.floor_analyzer.analyze_floor_image(temp_file_path, context)
                
                if not analysis['success']:
                    self.bot.edit_message_text(
                        f"❌ Ошибка при анализе: {analysis.get('error', 'Неизвестная ошибка')}",
                        message.chat.id,
                        status_msg.message_id
                    )
                    return
                
                # Создаем упрощенный результат для одного изображения
                single_analysis = {
                    'success': True,
                    'floor_type': analysis.get('floor_type', 'unknown'),
                    'condition': analysis.get('condition', 'unknown'),
                    'total_area_estimate': analysis.get('area_estimate', 20),
                    'damages': analysis.get('damages', []),
                    'recommendations': analysis.get('recommendations', []),
                    'work_complexity': analysis.get('work_complexity', 'medium'),
                    'images_analyzed': 1,
                    'context': context
                }
                
                # Рассчитываем стоимость
                cost_info = self.pricing_calculator.calculate_project_cost(single_analysis)
                timeline = self.pricing_calculator.get_work_timeline(single_analysis, cost_info)
                
                # Удаляем статусное сообщение
                self.bot.delete_message(message.chat.id, status_msg.message_id)
                
                # Создаем краткий отчет
                quick_summary = self.report_generator.create_quick_summary(single_analysis, cost_info)
                
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton("📋 Подробный отчет", callback_data="detailed_single"),
                    types.InlineKeyboardButton("📱 Ответ клиенту", callback_data="client_template_single")
                )
                
                # Сохраняем данные
                self.user_data[message.chat.id] = {
                    'analysis': single_analysis,
                    'cost_info': cost_info,
                    'timeline': timeline,
                    'client_info': {'name': 'Клиент'},
                    'is_single_photo': True
                }
                
                self.bot.send_message(
                    message.chat.id,
                    f"✅ **Анализ завершен!**\n\n{quick_summary}",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
            finally:
                # Удаляем временный файл
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error processing single photo: {e}")
            self.bot.send_message(
                message.chat.id,
                f"❌ Произошла ошибка при анализе фотографии: {str(e)}"
            )
    
    def send_analysis_results(self, chat_id: int):
        """Отправляет результаты анализа"""
        user_data = self.user_data.get(chat_id)
        if not user_data:
            return
        
        # Создаем краткую сводку
        quick_summary = self.report_generator.create_quick_summary(
            user_data['analysis'], 
            user_data['cost_info']
        )
        
        # Создаем клавиатуру с действиями
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("📋 Полный отчет", callback_data="full_report"),
            types.InlineKeyboardButton("📱 Ответ клиенту", callback_data="client_template"),
            types.InlineKeyboardButton("💰 Изменить цену", callback_data="adjust_price"),
            types.InlineKeyboardButton("📊 Детали анализа", callback_data="analysis_details"),
            types.InlineKeyboardButton("🔄 Новый анализ", callback_data="new_analysis")
        )
        
        self.bot.send_message(
            chat_id,
            f"✅ **Анализ WhatsApp чата завершен!**\n\n{quick_summary}",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    def handle_callback_query(self, call):
        """Обрабатывает нажатия на кнопки"""
        try:
            user_data = self.user_data.get(call.message.chat.id)
            
            if call.data == "help":
                self.handle_help(call.message)
            
            elif call.data == "contacts":
                contact_text = """📞 **КОНТАКТЫ ИВАНА**

👤 Имя: Иван
📱 Телефон: +972 52-477-2115
🏠 Специализация: Ремонт полов и паркета

🕒 Время работы: Воскресенье - Четверг, 8:00 - 18:00
📍 Обслуживаемые районы: Весь Израиль

💬 Для заказа работ звоните или пишите в WhatsApp!"""
                
                self.bot.send_message(call.message.chat.id, contact_text, parse_mode='Markdown')
            
            elif call.data in ["full_report", "detailed_single"] and user_data:
                # Создаем полный отчет
                full_report = self.report_generator.create_analysis_report(
                    user_data['analysis'],
                    user_data['cost_info'],
                    user_data['timeline'],
                    user_data['client_info']
                )
                
                self.bot.send_message(call.message.chat.id, full_report, parse_mode='Markdown')
            
            elif call.data in ["client_template", "client_template_single"] and user_data:
                # Создаем шаблон ответа клиенту
                client_template = self.report_generator.create_client_response_template(
                    user_data['analysis'],
                    user_data['cost_info'],
                    user_data['timeline'],
                    user_data['client_info']
                )
                
                self.bot.send_message(
                    call.message.chat.id, 
                    f"📱 **ШАБЛОН ОТВЕТА КЛИЕНТУ:**\n\n{client_template}",
                    parse_mode='Markdown'
                )
            
            elif call.data == "new_analysis":
                # Очищаем данные пользователя
                if call.message.chat.id in self.user_data:
                    del self.user_data[call.message.chat.id]
                
                self.bot.send_message(
                    call.message.chat.id,
                    "🔄 Готов к новому анализу! Отправьте ZIP архив или фотографии."
                )
            
            # Подтверждаем обработку callback
            self.bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            self.bot.answer_callback_query(call.id, "❌ Произошла ошибка")

