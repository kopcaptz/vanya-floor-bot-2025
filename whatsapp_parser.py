import zipfile
import os
import re
import tempfile
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class WhatsAppParser:
    def __init__(self):
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.webp'}
        self.supported_audio_formats = {'.m4a', '.ogg', '.mp3'}
    
    def process_whatsapp_export(self, zip_content: bytes) -> Dict:
        """
        Обрабатывает ZIP архив с экспортом WhatsApp
        
        Returns:
            Dict с результатами парсинга
        """
        result = {
            'success': False,
            'chat_messages': [],
            'media_files': [],
            'client_info': {},
            'conversation_context': '',
            'error': None
        }
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Сохраняем ZIP файл
                zip_path = os.path.join(temp_dir, 'whatsapp_export.zip')
                with open(zip_path, 'wb') as f:
                    f.write(zip_content)
                
                # Распаковываем архив
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Парсим содержимое
                result = self._parse_extracted_content(temp_dir)
                result['success'] = True
                
        except Exception as e:
            logger.error(f"Error processing WhatsApp export: {e}")
            result['error'] = str(e)
        
        return result
    
    def _parse_extracted_content(self, extract_dir: str) -> Dict:
        """Парсит содержимое распакованного архива"""
        result = {
            'chat_messages': [],
            'media_files': [],
            'client_info': {},
            'conversation_context': ''
        }
        
        # Ищем файл чата
        chat_file = self._find_chat_file(extract_dir)
        if chat_file:
            result['chat_messages'] = self._parse_chat_file(chat_file)
            result['client_info'] = self._extract_client_info(result['chat_messages'])
            result['conversation_context'] = self._create_conversation_context(result['chat_messages'])
        
        # Ищем медиафайлы
        result['media_files'] = self._find_media_files(extract_dir)
        
        return result
    
    def _find_chat_file(self, extract_dir: str) -> Optional[str]:
        """Находит файл с текстом чата"""
        for file in os.listdir(extract_dir):
            if file.endswith('_chat.txt') or file == '_chat.txt':
                return os.path.join(extract_dir, file)
        return None
    
    def _parse_chat_file(self, chat_file_path: str) -> List[Dict]:
        """Парсит файл чата WhatsApp"""
        messages = []
        
        try:
            with open(chat_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Регулярное выражение для парсинга сообщений WhatsApp
            # Поддерживает разные форматы дат
            patterns = [
                r'\[(\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}:\d{2})\] ([^:]+): (.+)',  # [DD.MM.YYYY, HH:MM:SS] Name: Message
                r'(\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}) - ([^:]+): (.+)',          # DD.MM.YYYY, HH:MM - Name: Message
                r'(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2} [AP]M) - ([^:]+): (.+)'  # M/D/YY, H:MM AM/PM - Name: Message
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                if matches:
                    for match in matches:
                        timestamp_str, sender, message = match
                        
                        messages.append({
                            'timestamp': timestamp_str,
                            'sender': sender.strip(),
                            'message': message.strip(),
                            'is_media': self._is_media_message(message),
                            'is_system': self._is_system_message(message)
                        })
                    break
            
        except Exception as e:
            logger.error(f"Error parsing chat file: {e}")
        
        return messages
    
    def _is_media_message(self, message: str) -> bool:
        """Проверяет, является ли сообщение медиафайлом"""
        media_indicators = [
            '<Media omitted>',
            'audio omitted',
            'video omitted',
            'image omitted',
            'document omitted',
            'Медиафайл пропущен',
            'Аудио пропущено'
        ]
        return any(indicator in message for indicator in media_indicators)
    
    def _is_system_message(self, message: str) -> bool:
        """Проверяет, является ли сообщение системным"""
        system_indicators = [
            'Messages and calls are end-to-end encrypted',
            'создал группу',
            'покинул группу',
            'изменил тему группы',
            'added',
            'left',
            'changed the group'
        ]
        return any(indicator in message for indicator in system_indicators)
    
    def _extract_client_info(self, messages: List[Dict]) -> Dict:
        """Извлекает информацию о клиенте из сообщений"""
        client_info = {
            'name': None,
            'phone': None,
            'address': None,
            'problem_descriptions': [],
            'message_count': 0
        }
        
        # Определяем имя клиента (не Иван и не системные сообщения)
        senders = {}
        for msg in messages:
            if not msg['is_system'] and msg['sender'] != 'Иван':
                senders[msg['sender']] = senders.get(msg['sender'], 0) + 1
        
        if senders:
            # Берем отправителя с наибольшим количеством сообщений
            client_info['name'] = max(senders, key=senders.get)
            client_info['message_count'] = senders[client_info['name']]
        
        # Ищем описания проблем и другую информацию
        floor_keywords = ['пол', 'паркет', 'ламинат', 'плитка', 'линолеум', 'покрытие']
        
        for msg in messages:
            message_lower = msg['message'].lower()
            
            # Ищем описания проблем с полом
            if any(keyword in message_lower for keyword in floor_keywords):
                client_info['problem_descriptions'].append(msg['message'])
            
            # Ищем адрес
            if any(word in message_lower for word in ['адрес', 'улица', 'дом', 'квартира']):
                client_info['address'] = msg['message']
            
            # Ищем телефон
            phone_pattern = r'[\+]?[0-9\-\s\(\)]{10,}'
            phone_match = re.search(phone_pattern, msg['message'])
            if phone_match:
                client_info['phone'] = phone_match.group()
        
        return client_info
    
    def _create_conversation_context(self, messages: List[Dict]) -> str:
        """Создает контекст разговора для ИИ"""
        context_parts = []
        
        # Берем последние 15 сообщений, исключая системные и медиа
        relevant_messages = [
            msg for msg in messages[-15:] 
            if not msg['is_system'] and not msg['is_media']
        ]
        
        for msg in relevant_messages:
            context_parts.append(f"{msg['sender']}: {msg['message']}")
        
        return '\n'.join(context_parts)
    
    def _find_media_files(self, extract_dir: str) -> List[Dict]:
        """Находит все медиафайлы в распакованном архиве"""
        media_files = []
        
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in self.supported_image_formats:
                    media_files.append({
                        'path': file_path,
                        'name': file,
                        'type': 'image',
                        'extension': file_ext
                    })
                elif file_ext in self.supported_audio_formats:
                    media_files.append({
                        'path': file_path,
                        'name': file,
                        'type': 'audio',
                        'extension': file_ext
                    })
        
        return media_files

